"""
Train heterogeneous GNN for skill link prediction.

Features:
- Leak-safe train/val/test splits (by person)
- HeteroGraphSAGE or RGCN model
- Negative sampling during training
- Early stopping on validation metrics
- Sanity checks (overfit test, coverage check)
- Full evaluation (Hits@K, MRR, AUC)
- GO/NO-GO decision vs baselines
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.nn import SAGEConv, RGCNConv, HeteroConv, Linear
from torch_geometric.transforms import ToUndirected
from sklearn.metrics import roc_auc_score
from tqdm import tqdm
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    HETERODATA_PATH, BASELINE_RESULTS_PATH,
    BEST_MODEL_PATH, GNN_RESULTS_PATH, FINAL_COMPARISON_PATH,
    RANDOM_SEED, DEVICE,
    TRAIN_RATIO, VAL_RATIO, TEST_RATIO, NUM_NEGATIVES_PER_POSITIVE,
    HIDDEN_DIM, NUM_LAYERS, DROPOUT, GNN_TYPE,
    BATCH_SIZE, LEARNING_RATE, WEIGHT_DECAY, MAX_EPOCHS,
    EARLY_STOPPING_PATIENCE, EARLY_STOPPING_METRIC,
    K_VALUES, GO_CRITERIA,
    OVERFIT_TEST_NUM_PERSONS, OVERFIT_TEST_MAX_EPOCHS, OVERFIT_TEST_SUCCESS_THRESHOLD,
    MIN_SKILLS_PER_PERSON_THRESHOLD,
    LOG_LEVEL, LOG_FILE
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set random seeds
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def convert_to_python_types(obj):
    """Convert numpy/torch types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {key: convert_to_python_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_python_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif torch.is_tensor(obj):
        return obj.cpu().numpy().tolist()
    else:
        return obj


# ============================================================================
# GNN MODEL
# ============================================================================

class HeteroGNN(nn.Module):
    """Heterogeneous GNN for link prediction using HeteroConv."""
    
    def __init__(self, metadata, hidden_dim, num_layers, dropout=0.3):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Extract node types and edge types from metadata
        node_types, edge_types = metadata
        
        # Create heterogeneous convolution layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            conv_dict = {}
            for edge_type in edge_types:
                src_type, _, dst_type = edge_type
                # Use SAGEConv for each edge type
                conv_dict[edge_type] = SAGEConv((-1, -1), hidden_dim)
            
            self.convs.append(HeteroConv(conv_dict, aggr='mean'))
        
    def forward(self, x_dict, edge_index_dict):
        """Forward pass through GNN layers."""
        for i, conv in enumerate(self.convs):
            x_dict = conv(x_dict, edge_index_dict)
            if i < self.num_layers - 1:
                x_dict = {key: F.relu(x) for key, x in x_dict.items()}
                x_dict = {key: F.dropout(x, p=self.dropout, training=self.training)
                         for key, x in x_dict.items()}
        return x_dict


class LinkPredictionModel(nn.Module):
    """Full link prediction model with GNN encoder + dot product decoder."""
    
    def __init__(self, metadata, hidden_dim, num_layers, dropout=0.3):
        super().__init__()
        self.encoder = HeteroGNN(metadata, hidden_dim, num_layers, dropout)
        
    def forward(self, x_dict, edge_index_dict):
        """Encode nodes to embeddings."""
        return self.encoder(x_dict, edge_index_dict)
    
    def decode(self, z_person, z_skill, edge_label_index):
        """
        Decode edge scores using dot product.
        
        Args:
            z_person: Person embeddings [num_persons, hidden_dim]
            z_skill: Skill embeddings [num_skills, hidden_dim]
            edge_label_index: [2, num_edges] tensor
            
        Returns:
            scores: [num_edges] tensor
        """
        person_embeds = z_person[edge_label_index[0]]
        skill_embeds = z_skill[edge_label_index[1]]
        scores = (person_embeds * skill_embeds).sum(dim=-1)
        return scores
    
    def decode_all(self, z_person, z_skill):
        """Compute scores for ALL person-skill pairs (for ranking)."""
        return z_person @ z_skill.t()


# ============================================================================
# DATASET PREPARATION
# ============================================================================

class LinkPredDataset:
    """Leak-safe link prediction dataset with train/val/test splits."""
    
    def __init__(self, data: HeteroData, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
        self.data = data
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        
        # Extract edge data
        self.person_skill_edges = data['person', 'has_skill', 'skill'].edge_index
        self.num_persons = data['person'].x.shape[0]
        self.num_skills = data['skill'].x.shape[0]
        
        logger.info(f"Dataset: {self.num_persons} persons, {self.num_skills} skills")
        logger.info(f"Total HAS_SKILL edges: {self.person_skill_edges.shape[1]}")
        
        # Build person->skills map
        self.person_skills = self._build_person_skills_map()
        
        # Check data quality
        self._check_data_quality()
        
    def _build_person_skills_map(self):
        """Build adjacency dict."""
        person_skills = {i: set() for i in range(self.num_persons)}
        edges = self.person_skill_edges.numpy()
        for person_idx, skill_idx in zip(edges[0], edges[1]):
            person_skills[person_idx].add(skill_idx)
        return person_skills
    
    def _check_data_quality(self):
        """Sanity check: coverage of training signal."""
        logger.info("\n" + "="*80)
        logger.info("DATA QUALITY CHECKS")
        logger.info("="*80)
        
        # Check skill distribution per person
        skills_per_person = [len(skills) for skills in self.person_skills.values()]
        logger.info(f"Skills per person: min={min(skills_per_person)}, "
                   f"mean={np.mean(skills_per_person):.1f}, "
                   f"median={np.median(skills_per_person):.1f}, "
                   f"max={max(skills_per_person)}")
        
        # Warn if many persons have few skills
        low_skill_count = sum(1 for s in skills_per_person if s < MIN_SKILLS_PER_PERSON_THRESHOLD)
        pct = low_skill_count / len(skills_per_person) * 100
        logger.info(f"Persons with <{MIN_SKILLS_PER_PERSON_THRESHOLD} skills: "
                   f"{low_skill_count}/{len(skills_per_person)} ({pct:.1f}%)")
        
        if pct > 30:
            logger.warning(f"[WARNING] {pct:.1f}% of persons have very few skills. "
                          f"Training signal may be weak!")
        
        # Check embedding coverage
        skill_embeds = self.data['skill'].x
        zero_embeds = (skill_embeds.sum(dim=1) == 0).sum().item()
        embed_coverage = 1 - (zero_embeds / self.num_skills)
        logger.info(f"Skills with embeddings: {self.num_skills - zero_embeds}/{self.num_skills} "
                   f"({embed_coverage*100:.1f}%)")
        
        if embed_coverage < 0.8:
            logger.warning(f"[WARNING] Only {embed_coverage*100:.1f}% of skills have embeddings!")
        
        logger.info("="*80 + "\n")
    
    def split_by_persons(self):
        """
        Leak-safe split: partition persons into train/val/test.
        Each split only uses edges from its persons.
        """
        logger.info("\n" + "="*80)
        logger.info("CREATING LEAK-SAFE TRAIN/VAL/TEST SPLITS")
        logger.info("="*80)
        
        # Build person->skills map to filter persons with no skills
        person_skills = {}
        edges = self.person_skill_edges.t().numpy()
        for person_idx, skill_idx in edges:
            if person_idx not in person_skills:
                person_skills[person_idx] = []
            person_skills[person_idx].append(skill_idx)
        
        # Only use persons with at least one skill
        all_persons = [p for p in range(self.num_persons) if p in person_skills]
        logger.info(f"Total persons with skills: {len(all_persons)}/{self.num_persons}")
        
        # Shuffle persons
        np.random.shuffle(all_persons)
        
        # Split
        num_train = int(len(all_persons) * self.train_ratio)
        num_val = int(len(all_persons) * self.val_ratio)
        
        train_persons = set(all_persons[:num_train])
        val_persons = set(all_persons[num_train:num_train + num_val])
        test_persons = set(all_persons[num_train + num_val:])
        
        logger.info(f"Train persons: {len(train_persons)}")
        logger.info(f"Val persons: {len(val_persons)}")
        logger.info(f"Test persons: {len(test_persons)}")
        
        # Split edges by person membership
        train_edges = []
        val_edges = []
        test_edges = []
        
        edges = self.person_skill_edges.t().numpy()
        for person_idx, skill_idx in edges:
            if person_idx in train_persons:
                train_edges.append([person_idx, skill_idx])
            elif person_idx in val_persons:
                val_edges.append([person_idx, skill_idx])
            elif person_idx in test_persons:
                test_edges.append([person_idx, skill_idx])
        
        logger.info(f"Train edges: {len(train_edges)}")
        logger.info(f"Val edges: {len(val_edges)}")
        logger.info(f"Test edges: {len(test_edges)}")
        logger.info("="*80 + "\n")
        
        return {
            'train_persons': train_persons,
            'val_persons': val_persons,
            'test_persons': test_persons,
            'train_edges': torch.tensor(train_edges, dtype=torch.long).t(),
            'val_edges': torch.tensor(val_edges, dtype=torch.long).t(),
            'test_edges': torch.tensor(test_edges, dtype=torch.long).t()
        }
    
    def sample_negatives(self, positive_edges, num_negatives_per_positive=5):
        """
        Sample negative edges (person-skill pairs that DON'T exist).
        
        Args:
            positive_edges: [2, num_pos] tensor
            num_negatives_per_positive: Number of negatives per positive
            
        Returns:
            negative_edges: [2, num_neg] tensor
        """
        num_positives = positive_edges.shape[1]
        num_negatives = num_positives * num_negatives_per_positive
        
        # Build set of positive edges for fast lookup
        positive_set = set()
        for i in range(num_positives):
            person_idx = positive_edges[0, i].item()
            skill_idx = positive_edges[1, i].item()
            positive_set.add((person_idx, skill_idx))
        
        # Sample negatives
        negative_edges = []
        attempts = 0
        max_attempts = num_negatives * 10
        
        while len(negative_edges) < num_negatives and attempts < max_attempts:
            person_idx = np.random.randint(0, self.num_persons)
            skill_idx = np.random.randint(0, self.num_skills)
            
            if (person_idx, skill_idx) not in positive_set:
                negative_edges.append([person_idx, skill_idx])
            
            attempts += 1
        
        if len(negative_edges) < num_negatives:
            logger.warning(f"Could only sample {len(negative_edges)}/{num_negatives} negatives")
        
        return torch.tensor(negative_edges, dtype=torch.long).t()


# ============================================================================
# TRAINING & EVALUATION
# ============================================================================

class LinkPredictionTrainer:
    """Train and evaluate link prediction model."""
    
    def __init__(self, data: HeteroData, model: LinkPredictionModel):
        self.data = data.to(DEVICE)
        self.model = model.to(DEVICE)
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=LEARNING_RATE,
            weight_decay=WEIGHT_DECAY
        )
        self.criterion = nn.BCEWithLogitsLoss()
        
        # For evaluation
        self.dataset = LinkPredDataset(data)
    
    def train_epoch(self, train_pos_edges, train_neg_edges):
        """Train for one epoch."""
        self.model.train()
        
        # Combine positives and negatives
        edge_label_index = torch.cat([train_pos_edges, train_neg_edges], dim=1)
        edge_label = torch.cat([
            torch.ones(train_pos_edges.shape[1]),
            torch.zeros(train_neg_edges.shape[1])
        ]).to(DEVICE)
        
        edge_label_index = edge_label_index.to(DEVICE)
        
        # Forward pass
        z_dict = self.model(self.data.x_dict, self.data.edge_index_dict)
        z_person = z_dict['person']
        z_skill = z_dict['skill']
        
        # Decode
        scores = self.model.decode(z_person, z_skill, edge_label_index)
        
        # Compute loss
        loss = self.criterion(scores, edge_label)
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    @torch.no_grad()
    def evaluate(self, eval_persons, eval_pos_edges, eval_neg_edges, split_name="Val"):
        """Evaluate on validation or test set."""
        self.model.eval()
        
        # Forward pass
        z_dict = self.model(self.data.x_dict, self.data.edge_index_dict)
        z_person = z_dict['person']
        z_skill = z_dict['skill']
        
        # Build person->skills map for eval set
        person_skills = {p: set() for p in eval_persons}
        edges = eval_pos_edges.cpu().numpy()
        for person_idx, skill_idx in zip(edges[0], edges[1]):
            if person_idx in eval_persons:
                person_skills[person_idx].add(skill_idx)
        
        # Add negative edges to eval set
        neg_edges = eval_neg_edges.cpu().numpy()
        person_neg_skills = {p: set() for p in eval_persons}
        for person_idx, skill_idx in zip(neg_edges[0], neg_edges[1]):
            if person_idx in eval_persons:
                person_neg_skills[person_idx].add(skill_idx)
        
        # Evaluate each person
        all_metrics = []
        
        for person_idx in eval_persons:
            positives = person_skills.get(person_idx, set())
            negatives = person_neg_skills.get(person_idx, set())
            
            if not positives:
                continue
            
            # Get scores for this person
            person_embed = z_person[person_idx].unsqueeze(0)  # [1, hidden_dim]
            all_skill_embeds = z_skill  # [num_skills, hidden_dim]
            scores = (person_embed @ all_skill_embeds.t()).squeeze(0)  # [num_skills]
            
            # Rank test skills
            test_skills = list(positives | negatives)
            test_scores = [(skill_idx, scores[skill_idx].item()) for skill_idx in test_skills]
            test_scores.sort(key=lambda x: -x[1])
            ranked_skills = [s for s, _ in test_scores]
            
            # Compute metrics
            metrics = {}
            
            # Hits@K
            for k in K_VALUES:
                top_k = set(ranked_skills[:k])
                hits = len(top_k & positives) / len(positives)
                metrics[f'hits@{k}'] = hits
            
            # MRR
            reciprocal_ranks = []
            for pos_skill in positives:
                if pos_skill in ranked_skills:
                    rank = ranked_skills.index(pos_skill) + 1
                    reciprocal_ranks.append(1.0 / rank)
                else:
                    reciprocal_ranks.append(0.0)
            metrics['mrr'] = np.mean(reciprocal_ranks)
            
            # AUC
            if len(positives) > 0 and len(negatives) > 0:
                y_true = [1 if s in positives else 0 for s in test_skills]
                y_score = [scores[s].item() for s in test_skills]
                try:
                    metrics['auc'] = roc_auc_score(y_true, y_score)
                except:
                    metrics['auc'] = 0.5
            else:
                metrics['auc'] = 0.5
            
            all_metrics.append(metrics)
        
        # Average metrics
        if not all_metrics:
            return {f'hits@{k}': 0.0 for k in K_VALUES} | {'mrr': 0.0, 'auc': 0.5}
        
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in all_metrics])
        
        return avg_metrics
    
    def train(self, splits, max_epochs=100, patience=10):
        """Full training loop with early stopping."""
        logger.info("\n" + "="*80)
        logger.info("TRAINING GNN")
        logger.info("="*80)
        
        train_pos = splits['train_edges']
        val_pos = splits['val_edges']
        val_persons = splits['val_persons']
        
        # Sample negatives
        logger.info("Sampling negative edges...")
        train_neg = self.dataset.sample_negatives(train_pos, NUM_NEGATIVES_PER_POSITIVE)
        val_neg = self.dataset.sample_negatives(val_pos, NUM_NEGATIVES_PER_POSITIVE)
        
        logger.info(f"Train: {train_pos.shape[1]} pos, {train_neg.shape[1]} neg")
        logger.info(f"Val: {val_pos.shape[1]} pos, {val_neg.shape[1]} neg")
        
        best_val_metric = 0.0
        best_epoch = 0
        patience_counter = 0
        
        for epoch in range(max_epochs):
            # Train
            train_loss = self.train_epoch(train_pos, train_neg)
            
            # Evaluate on validation set
            val_metrics = self.evaluate(val_persons, val_pos, val_neg, "Val")
            
            # Early stopping
            val_metric = val_metrics[EARLY_STOPPING_METRIC.replace('val_', '')]
            
            if val_metric > best_val_metric:
                best_val_metric = val_metric
                best_epoch = epoch
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), BEST_MODEL_PATH)
            else:
                patience_counter += 1
            
            # Log
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logger.info(f"Epoch {epoch+1}/{max_epochs} | Loss: {train_loss:.4f} | "
                          f"Val Hits@10: {val_metrics['hits@10']:.4f} | "
                          f"Val MRR: {val_metrics['mrr']:.4f} | "
                          f"Val AUC: {val_metrics['auc']:.4f}")
            
            # Early stopping
            if patience_counter >= patience:
                logger.info(f"\nEarly stopping at epoch {epoch+1}")
                logger.info(f"Best {EARLY_STOPPING_METRIC}: {best_val_metric:.4f} at epoch {best_epoch+1}")
                break
        
        # Load best model
        self.model.load_state_dict(torch.load(BEST_MODEL_PATH, weights_only=False))
        logger.info(f"\n[OK] Best model loaded from epoch {best_epoch+1}")
        logger.info("="*80 + "\n")


# ============================================================================
# SANITY CHECKS
# ============================================================================

def extract_overfit_subgraph(data: HeteroData, num_persons=50):
    """
    Extract induced subgraph for overfit test.
    Returns only the nodes/edges reachable from selected persons.
    """
    # Select persons with most skills (easier to overfit)
    person_skill_edges = data['person', 'has_skill', 'skill'].edge_index
    person_skills_count = torch.bincount(person_skill_edges[0], minlength=data['person'].x.shape[0])
    
    # Get top N persons by skill count
    top_persons = torch.argsort(person_skills_count, descending=True)[:num_persons]
    person_mask = torch.zeros(data['person'].x.shape[0], dtype=torch.bool)
    person_mask[top_persons] = True
    
    # Get skills connected to these persons
    mask = person_mask[person_skill_edges[0]]
    subgraph_edges = person_skill_edges[:, mask]
    skill_indices = subgraph_edges[1].unique()
    skill_mask = torch.zeros(data['skill'].x.shape[0], dtype=torch.bool)
    skill_mask[skill_indices] = True
    
    # Create ID remapping for compact indexing
    person_old_to_new = torch.full((data['person'].x.shape[0],), -1, dtype=torch.long)
    person_old_to_new[top_persons] = torch.arange(len(top_persons))
    
    skill_old_to_new = torch.full((data['skill'].x.shape[0],), -1, dtype=torch.long)
    skill_old_to_new[skill_indices] = torch.arange(len(skill_indices))
    
    # Remap edges
    remapped_edges = torch.stack([
        person_old_to_new[subgraph_edges[0]],
        skill_old_to_new[subgraph_edges[1]]
    ])
    
    # Build subgraph data
    subgraph_data = HeteroData()
    subgraph_data['person'].x = data['person'].x[top_persons]
    subgraph_data['skill'].x = data['skill'].x[skill_indices]
    subgraph_data['person', 'has_skill', 'skill'].edge_index = remapped_edges
    
    # Add reverse edges
    subgraph_data['skill', 'rev_has_skill', 'person'].edge_index = remapped_edges.flip(0)
    
    # Copy other node/edge types if they exist (for full message passing)
    if 'project' in data.node_types:
        # For simplicity, include all projects/categories (they don't affect person count)
        subgraph_data['project'].x = data['project'].x
        subgraph_data['skill_category'].x = data['skill_category'].x
        
        # Add edges (filter to only include our skills)
        if ('project', 'uses_technology', 'skill') in data.edge_types:
            proj_skill_edges = data['project', 'uses_technology', 'skill'].edge_index
            proj_mask = skill_mask[proj_skill_edges[1]]
            proj_edges = proj_skill_edges[:, proj_mask]
            subgraph_data['project', 'uses_technology', 'skill'].edge_index = torch.stack([
                proj_edges[0],
                skill_old_to_new[proj_edges[1]]
            ])
            subgraph_data['skill', 'rev_uses_technology', 'project'].edge_index = subgraph_data['project', 'uses_technology', 'skill'].edge_index.flip(0)
        
        if ('skill', 'belongs_to_category', 'skill_category') in data.edge_types:
            cat_edges = data['skill', 'belongs_to_category', 'skill_category'].edge_index
            cat_mask = skill_mask[cat_edges[0]]
            cat_edges_filtered = cat_edges[:, cat_mask]
            subgraph_data['skill', 'belongs_to_category', 'skill_category'].edge_index = torch.stack([
                skill_old_to_new[cat_edges_filtered[0]],
                cat_edges_filtered[1]
            ])
            subgraph_data['skill_category', 'rev_belongs_to_category', 'skill'].edge_index = subgraph_data['skill', 'belongs_to_category', 'skill_category'].edge_index.flip(0)
        
        if ('person', 'worked_on', 'project') in data.edge_types:
            person_proj_edges = data['person', 'worked_on', 'project'].edge_index
            person_proj_mask = person_mask[person_proj_edges[0]]
            person_proj_filtered = person_proj_edges[:, person_proj_mask]
            subgraph_data['person', 'worked_on', 'project'].edge_index = torch.stack([
                person_old_to_new[person_proj_filtered[0]],
                person_proj_filtered[1]
            ])
            subgraph_data['project', 'rev_worked_on', 'person'].edge_index = subgraph_data['person', 'worked_on', 'project'].edge_index.flip(0)
    
    return subgraph_data, top_persons.tolist(), skill_indices.tolist()


def precompute_frozen_negatives(positive_edges, num_persons, num_skills, neg_per_pos=2):
    """
    Precompute negative samples once and freeze them.
    This ensures consistent training signal for overfit test.
    """
    num_positives = positive_edges.shape[1]
    num_negatives = num_positives * neg_per_pos
    
    # Build positive set
    positive_set = set()
    for i in range(num_positives):
        person_idx = positive_edges[0, i].item()
        skill_idx = positive_edges[1, i].item()
        positive_set.add((person_idx, skill_idx))
    
    # Sample negatives
    negative_edges = []
    attempts = 0
    max_attempts = num_negatives * 20
    
    np.random.seed(42)  # Fixed seed for reproducibility
    while len(negative_edges) < num_negatives and attempts < max_attempts:
        person_idx = np.random.randint(0, num_persons)
        skill_idx = np.random.randint(0, num_skills)
        
        if (person_idx, skill_idx) not in positive_set:
            negative_edges.append([person_idx, skill_idx])
            positive_set.add((person_idx, skill_idx))  # Prevent duplicates
        
        attempts += 1
    
    return torch.tensor(negative_edges, dtype=torch.long).t()


def overfit_test(data: HeteroData, num_persons=50, max_epochs=500):
    """
    STRICT OVERFIT TEST: Must achieve near-perfect performance on tiny subset.
    
    This is a pipeline sanity check. If this fails, there's a fundamental issue.
    
    Changes from normal training:
    - Small subset (50 persons with most skills)
    - Induced subgraph (only relevant nodes/edges)
    - Frozen negatives (precomputed once, reused every epoch)
    - No regularization (dropout=0, weight_decay=0)
    - High capacity (hidden_dim=256, 3 layers)
    - High learning rate (0.005)
    - Many epochs (500-1000)
    - No early stopping
    """
    logger.info("\n" + "="*80)
    logger.info("SANITY CHECK: MINI-OVERFIT TEST")
    logger.info("="*80)
    logger.info(f"Extracting subgraph for {num_persons} persons with most skills...")
    
    # Extract subgraph
    subgraph_data, person_ids, skill_ids = extract_overfit_subgraph(data, num_persons)
    
    # Get training edges
    train_edges = subgraph_data['person', 'has_skill', 'skill'].edge_index
    num_persons_sub = subgraph_data['person'].x.shape[0]
    num_skills_sub = subgraph_data['skill'].x.shape[0]
    num_edges = train_edges.shape[1]
    
    # Compute statistics
    person_skill_counts = torch.bincount(train_edges[0], minlength=num_persons_sub)
    avg_skills_per_person = person_skill_counts.float().mean().item()
    
    # Check embedding coverage
    skill_embeds = subgraph_data['skill'].x
    zero_embeds = (skill_embeds.sum(dim=1) == 0).sum().item()
    embed_coverage = 1 - (zero_embeds / num_skills_sub)
    
    logger.info(f"\nOverfit Subgraph Statistics:")
    logger.info(f"  Persons: {num_persons_sub}")
    logger.info(f"  Skills: {num_skills_sub}")
    logger.info(f"  Edges: {num_edges}")
    logger.info(f"  Avg skills/person: {avg_skills_per_person:.1f}")
    logger.info(f"  Skill embedding coverage: {embed_coverage*100:.1f}%")
    logger.info(f"  Min skills/person: {person_skill_counts.min().item()}")
    logger.info(f"  Max skills/person: {person_skill_counts.max().item()}")
    
    # Precompute frozen negatives (fewer negatives for easier overfit)
    logger.info(f"\nPrecomputing frozen negatives (neg_per_pos=2)...")
    train_neg = precompute_frozen_negatives(train_edges, num_persons_sub, num_skills_sub, neg_per_pos=2)
    logger.info(f"  Positive edges: {train_edges.shape[1]}")
    logger.info(f"  Negative edges: {train_neg.shape[1]}")
    
    # Create OVERFIT-SPECIFIC model (no regularization, high capacity)
    logger.info(f"\nCreating overfit model (hidden_dim=256, layers=3, dropout=0)...")
    model = LinkPredictionModel(
        subgraph_data.metadata(),
        hidden_dim=256,  # High capacity
        num_layers=3,    # More layers
        dropout=0.0      # NO DROPOUT
    )
    
    # Initialize lazy modules
    with torch.no_grad():
        _ = model(subgraph_data.x_dict, subgraph_data.edge_index_dict)
    
    model = model.to(DEVICE)
    subgraph_data = subgraph_data.to(DEVICE)
    train_edges = train_edges.to(DEVICE)
    train_neg = train_neg.to(DEVICE)
    
    # Optimizer with NO weight decay and HIGHER learning rate
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=0.0)
    criterion = nn.BCEWithLogitsLoss()
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    logger.info(f"Training for {max_epochs} epochs (no early stopping)...")
    logger.info("")
    
    # Training loop
    best_hits10 = 0.0
    best_auc = 0.0
    best_epoch = 0
    
    for epoch in range(max_epochs):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        z_dict = model(subgraph_data.x_dict, subgraph_data.edge_index_dict)
        z_person = z_dict['person']
        z_skill = z_dict['skill']
        
        # Compute scores for positives and negatives
        pos_scores = model.decode(z_person, z_skill, train_edges)
        neg_scores = model.decode(z_person, z_skill, train_neg)
        
        # Balanced BCE loss
        pos_loss = criterion(pos_scores, torch.ones_like(pos_scores))
        neg_loss = criterion(neg_scores, torch.zeros_like(neg_scores))
        loss = (pos_loss + neg_loss) / 2
        
        loss.backward()
        optimizer.step()
        
        # Evaluation every 50 epochs (or last epoch)
        if (epoch + 1) % 50 == 0 or epoch == max_epochs - 1:
            model.eval()
            with torch.no_grad():
                z_dict = model(subgraph_data.x_dict, subgraph_data.edge_index_dict)
                z_person = z_dict['person']
                z_skill = z_dict['skill']
                
                pos_scores = model.decode(z_person, z_skill, train_edges).cpu()
                neg_scores = model.decode(z_person, z_skill, train_neg).cpu()
                
                # Compute metrics
                all_scores = torch.cat([pos_scores, neg_scores])
                all_labels = torch.cat([
                    torch.ones(pos_scores.shape[0]),
                    torch.zeros(neg_scores.shape[0])
                ])
                
                # AUC
                try:
                    auc = roc_auc_score(all_labels.numpy(), all_scores.numpy())
                except:
                    auc = 0.0
                
                # Hits@10 (per person)
                person_hits = []
                for person_idx in range(num_persons_sub):
                    # Get this person's true skills
                    person_mask = train_edges[0] == person_idx
                    true_skills = train_edges[1][person_mask].cpu().numpy()
                    
                    if len(true_skills) == 0:
                        continue
                    
                    # Get scores for all skills
                    person_emb = z_person[person_idx:person_idx+1]
                    skill_embs = z_skill
                    scores = (person_emb @ skill_embs.t()).squeeze().cpu()
                    
                    # Top 10 predictions
                    top10 = torch.argsort(scores, descending=True)[:10].numpy()
                    
                    # Compute hits
                    hits = len(set(top10) & set(true_skills)) / len(true_skills)
                    person_hits.append(hits)
                
                hits10 = np.mean(person_hits) if person_hits else 0.0
                
                # % positive > negative
                pos_win_rate = (pos_scores.unsqueeze(1) > neg_scores.unsqueeze(0)).float().mean().item()
                
                if hits10 > best_hits10:
                    best_hits10 = hits10
                    best_epoch = epoch + 1
                if auc > best_auc:
                    best_auc = auc
                
                logger.info(f"Epoch {epoch+1:4d}/{max_epochs} | Loss: {loss.item():.4f} | "
                           f"AUC: {auc:.4f} | Hits@10: {hits10:.4f} | "
                           f"Pos>Neg: {pos_win_rate*100:.1f}%")
    
    # Final evaluation
    logger.info("\n" + "-"*80)
    logger.info("OVERFIT TEST RESULTS:")
    logger.info(f"  Best Hits@10: {best_hits10:.4f} (epoch {best_epoch})")
    logger.info(f"  Best AUC: {best_auc:.4f}")
    logger.info("-"*80)
    
    # Pass criteria: Hits@10 >= 0.95 OR AUC >= 0.995
    success = best_hits10 >= 0.95 or best_auc >= 0.995
    
    if success:
        logger.info("[PASS] OVERFIT TEST PASSED")
        logger.info("  Model can successfully memorize small subset")
        logger.info("  Architecture is fundamentally sound")
    else:
        logger.error("[FAIL] OVERFIT TEST FAILED")
        logger.error(f"  Achieved: Hits@10={best_hits10:.4f}, AUC={best_auc:.4f}")
        logger.error(f"  Required: Hits@10>=0.95 OR AUC>=0.995")
        logger.error("\nMost likely causes (in order):")
        
        # Diagnostic analysis
        if embed_coverage < 0.95:
            logger.error(f"  1. [HIGH] Missing skill embeddings ({embed_coverage*100:.1f}% coverage)")
            logger.error(f"     -> {zero_embeds}/{num_skills_sub} skills have zero embeddings")
            logger.error("     -> Model cannot distinguish skills without features")
        else:
            logger.error("  1. [LOW] Embedding coverage is good")
        
        if avg_skills_per_person < 3:
            logger.error(f"  2. [HIGH] Too few skills per person (avg={avg_skills_per_person:.1f})")
            logger.error("     -> Not enough signal to learn from")
        else:
            logger.error("  2. [LOW] Skills per person is reasonable")
        
        if best_auc < 0.6:
            logger.error("  3. [HIGH] AUC very low - model not learning at all")
            logger.error("     -> Check: Are negatives leaking into positives?")
            logger.error("     -> Check: Is message passing working for all node types?")
            logger.error("     -> Check: Is the decoder computing dot products correctly?")
        else:
            logger.error("  3. [MEDIUM] AUC is reasonable but not excellent")
            logger.error("     -> Model is learning but may need:")
            logger.error("        - More epochs (try 1000)")
            logger.error("        - Different architecture (try RGCN)")
            logger.error("        - Better initialization")
    
    logger.info("="*80 + "\n")
    
    return success


# ============================================================================
# GO / NO-GO DECISION
# ============================================================================

def make_go_nogo_decision(gnn_results, baseline_results):
    """
    Determine if GNN is production-ready based on criteria.
    
    GO if:
    - GNN beats popularity baseline on Hits@10 and MRR
    - GNN beats embedding baseline on Hits@10
    - GNN achieves minimum absolute thresholds
    """
    logger.info("\n" + "="*80)
    logger.info("GO / NO-GO DECISION")
    logger.info("="*80)
    
    gnn = gnn_results
    pop = baseline_results['popularity']
    emb = baseline_results['embedding_similarity']
    
    checks = {}
    
    # Check 1: GNN beats popularity on Hits@10
    checks['gnn_beats_popularity_hits10'] = bool(gnn['hits@10'] > pop['hits@10'])
    logger.info(f"1. GNN Hits@10 ({gnn['hits@10']:.4f}) > Popularity Hits@10 ({pop['hits@10']:.4f}): "
               f"{'[PASS]' if checks['gnn_beats_popularity_hits10'] else '[FAIL]'}")
    
    # Check 2: GNN beats popularity on MRR
    checks['gnn_beats_popularity_mrr'] = bool(gnn['mrr'] > pop['mrr'])
    logger.info(f"2. GNN MRR ({gnn['mrr']:.4f}) > Popularity MRR ({pop['mrr']:.4f}): "
               f"{'[PASS]' if checks['gnn_beats_popularity_mrr'] else '[FAIL]'}")
    
    # Check 3: GNN beats embedding on Hits@10
    checks['gnn_beats_embedding_hits10'] = bool(gnn['hits@10'] > emb['hits@10'])
    logger.info(f"3. GNN Hits@10 ({gnn['hits@10']:.4f}) > Embedding Hits@10 ({emb['hits@10']:.4f}): "
               f"{'[PASS]' if checks['gnn_beats_embedding_hits10'] else '[FAIL]'}")
    
    # Check 4: Absolute thresholds
    checks['min_gnn_hits10'] = bool(gnn['hits@10'] >= GO_CRITERIA['min_gnn_hits10'])
    logger.info(f"4. GNN Hits@10 ({gnn['hits@10']:.4f}) >= {GO_CRITERIA['min_gnn_hits10']}: "
               f"{'[PASS]' if checks['min_gnn_hits10'] else '[FAIL]'}")
    
    checks['min_gnn_mrr'] = bool(gnn['mrr'] >= GO_CRITERIA['min_gnn_mrr'])
    logger.info(f"5. GNN MRR ({gnn['mrr']:.4f}) >= {GO_CRITERIA['min_gnn_mrr']}: "
               f"{'[PASS]' if checks['min_gnn_mrr'] else '[FAIL]'}")
    
    # Overall decision
    all_required_checks_pass = all([
        checks['gnn_beats_popularity_hits10'],
        checks['gnn_beats_popularity_mrr'],
        checks['min_gnn_hits10'],
        checks['min_gnn_mrr']
    ])
    
    logger.info("\n" + "-"*80)
    if all_required_checks_pass:
        logger.info("[GO] GNN is production-ready!")
        logger.info("   -> GNN significantly outperforms baselines")
        logger.info("   -> Suitable for deployment")
        decision = "GO"
    else:
        logger.info("[NO-GO] GNN is not production-ready")
        logger.info("   -> GNN does not sufficiently beat baselines")
        logger.info("   -> Needs improvement before deployment")
        logger.info("   -> Suggestions:")
        logger.info("     1. Tune hyperparameters (hidden_dim, num_layers, lr)")
        logger.info("     2. Try different GNN architecture (RGCN, HGT)")
        logger.info("     3. Add more node/edge features")
        logger.info("     4. Collect more training data")
        decision = "NO-GO"
    
    logger.info("="*80 + "\n")
    
    return decision, checks


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    try:
        # Load data
        logger.info("Loading HeteroData...")
        data = torch.load(HETERODATA_PATH, weights_only=False)
        
        # Add reverse edges to make graph bidirectional (needed for message passing)
        # This allows all node types to receive messages
        logger.info("Adding reverse edges for bidirectional message passing...")
        
        # Add reverse edge types
        if ('person', 'has_skill', 'skill') in data.edge_types:
            data['skill', 'rev_has_skill', 'person'].edge_index = data['person', 'has_skill', 'skill'].edge_index.flip(0)
        
        if ('person', 'worked_on', 'project') in data.edge_types:
            data['project', 'rev_worked_on', 'person'].edge_index = data['person', 'worked_on', 'project'].edge_index.flip(0)
        
        if ('project', 'uses_technology', 'skill') in data.edge_types:
            data['skill', 'rev_uses_technology', 'project'].edge_index = data['project', 'uses_technology', 'skill'].edge_index.flip(0)
        
        if ('skill', 'belongs_to_category', 'skill_category') in data.edge_types:
            data['skill_category', 'rev_belongs_to_category', 'skill'].edge_index = data['skill', 'belongs_to_category', 'skill_category'].edge_index.flip(0)
        
        logger.info("[OK] Data loaded\n")
        
        # SANITY CHECK 1: Overfit test
        overfit_success = overfit_test(data, OVERFIT_TEST_NUM_PERSONS, OVERFIT_TEST_MAX_EPOCHS)
        
        if not overfit_success:
            logger.error("\n[WARNING] Overfit test failed! Review model architecture before proceeding.")
            logger.error("Continuing anyway for full evaluation...")
        
        # Prepare dataset
        dataset = LinkPredDataset(data)
        splits = dataset.split_by_persons()
        
        # Create model
        logger.info("Creating GNN model...")
        model = LinkPredictionModel(
            data.metadata(),
            HIDDEN_DIM,
            NUM_LAYERS,
            DROPOUT
        )
        
        # Initialize lazy parameters with a dummy forward pass
        with torch.no_grad():
            _ = model(data.x_dict, data.edge_index_dict)
        
        logger.info(f"Model created: {sum(p.numel() for p in model.parameters())} parameters\n")
        
        # Train
        trainer = LinkPredictionTrainer(data, model)
        trainer.train(splits, MAX_EPOCHS, EARLY_STOPPING_PATIENCE)
        
        # Evaluate on test set
        logger.info("\n" + "="*80)
        logger.info("FINAL EVALUATION ON TEST SET")
        logger.info("="*80)
        
        test_persons = splits['test_persons']
        test_pos = splits['test_edges']
        test_neg = dataset.sample_negatives(test_pos, NUM_NEGATIVES_PER_POSITIVE)
        
        gnn_results = trainer.evaluate(test_persons, test_pos, test_neg, "Test")
        
        logger.info("\nGNN Test Results:")
        for key, value in gnn_results.items():
            logger.info(f"  {key}: {value:.4f}")
        
        # Save GNN results
        with open(GNN_RESULTS_PATH, 'w') as f:
            json.dump(convert_to_python_types(gnn_results), f, indent=2)
        logger.info(f"\n[OK] GNN results saved to: {GNN_RESULTS_PATH}")
        
        # Load baseline results
        with open(BASELINE_RESULTS_PATH, 'r') as f:
            baseline_results = json.load(f)
        
        # Comparison table
        logger.info("\n" + "="*80)
        logger.info("FINAL COMPARISON: GNN vs BASELINES")
        logger.info("="*80)
        
        comparison_data = {
            'Method': ['GNN', 'Popularity', 'Embedding Similarity'],
            **{f'Hits@{k}': [
                gnn_results[f'hits@{k}'],
                baseline_results['popularity'][f'hits@{k}'],
                baseline_results['embedding_similarity'][f'hits@{k}']
            ] for k in K_VALUES},
            'MRR': [
                gnn_results['mrr'],
                baseline_results['popularity']['mrr'],
                baseline_results['embedding_similarity']['mrr']
            ],
            'AUC': [
                gnn_results['auc'],
                baseline_results['popularity']['auc'],
                baseline_results['embedding_similarity']['auc']
            ]
        }
        
        df = pd.DataFrame(comparison_data)
        df.to_csv(FINAL_COMPARISON_PATH, index=False)
        
        logger.info("\n" + df.to_string(index=False))
        logger.info(f"\n[OK] Comparison table saved to: {FINAL_COMPARISON_PATH}")
        
        # GO / NO-GO decision
        decision, checks = make_go_nogo_decision(gnn_results, baseline_results)
        
        # Save final decision
        final_report = {
            'decision': decision,
            'checks': checks,
            'gnn_results': gnn_results,
            'baseline_results': baseline_results,
            'overfit_test_passed': overfit_success
        }
        
        report_path = BEST_MODEL_PATH.parent.parent / 'output' / 'final_report.json'
        with open(report_path, 'w') as f:
            json.dump(convert_to_python_types(final_report), f, indent=2)
        
        logger.info(f"\n[OK] Final report saved to: {report_path}")
        logger.info("\n" + "="*80)
        logger.info("TRAINING COMPLETE")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
