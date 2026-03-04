"""
Baseline evaluation for skill link prediction.

Implements two strong baselines:
1. Popularity Baseline: Rank skills by global HAS_SKILL frequency
2. Embedding Similarity Baseline: Rank skills by cosine similarity to person's skill embedding

Metrics: Hits@K, MRR, AUC
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score
from collections import Counter
from tqdm import tqdm

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    HETERODATA_PATH, ID_MAPS_PATH,
    BASELINE_RESULTS_PATH, K_VALUES,
    RANDOM_SEED, LOG_LEVEL, LOG_FILE
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

# Set random seed
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


class BaselineEvaluator:
    """Evaluate baseline methods for skill link prediction."""
    
    def __init__(self, data_path: str):
        """Load HeteroData."""
        logger.info(f"Loading HeteroData from {data_path}...")
        self.data = torch.load(data_path, weights_only=False)
        logger.info("HeteroData loaded successfully")
        
        # Extract key data
        self.person_skill_edges = self.data['person', 'has_skill', 'skill'].edge_index
        self.skill_embeddings = self.data['skill'].x
        
        self.num_persons = self.data['person'].x.shape[0]
        self.num_skills = self.skill_embeddings.shape[0]
        
        logger.info(f"Loaded {self.num_persons} persons, {self.num_skills} skills")
        logger.info(f"Total HAS_SKILL edges: {self.person_skill_edges.shape[1]}")
        
        # Build person->skills adjacency for fast lookup
        self.person_skills = self._build_person_skills_map()
        
    def _build_person_skills_map(self) -> Dict[int, set]:
        """Build dict mapping person_idx -> set of skill_idx."""
        person_skills = {i: set() for i in range(self.num_persons)}
        
        edges = self.person_skill_edges.numpy()
        for person_idx, skill_idx in zip(edges[0], edges[1]):
            person_skills[person_idx].add(skill_idx)
        
        return person_skills
    
    # ========================================================================
    # BASELINE 1: POPULARITY
    # ========================================================================
    
    def popularity_baseline(self) -> Dict[int, float]:
        """
        Rank skills by global popularity (frequency of HAS_SKILL edges).
        
        Returns:
            skill_scores: {skill_idx: popularity_score}
        """
        logger.info("\n" + "="*80)
        logger.info("BASELINE 1: Popularity")
        logger.info("="*80)
        
        # Count skill occurrences
        skill_counts = Counter(self.person_skill_edges[1].numpy())
        
        # Convert to scores (normalized)
        total_edges = self.person_skill_edges.shape[1]
        skill_scores = {skill_idx: count / total_edges 
                       for skill_idx, count in skill_counts.items()}
        
        # Skills not in graph get score 0
        for skill_idx in range(self.num_skills):
            if skill_idx not in skill_scores:
                skill_scores[skill_idx] = 0.0
        
        logger.info(f"Popularity scores computed for {len(skill_scores)} skills")
        logger.info(f"Top 5 popular skills: {sorted(skill_scores.items(), key=lambda x: -x[1])[:5]}")
        
        return skill_scores
    
    # ========================================================================
    # BASELINE 2: EMBEDDING SIMILARITY
    # ========================================================================
    
    def embedding_similarity_baseline(self, person_idx: int) -> Dict[int, float]:
        """
        Rank skills by cosine similarity to person's average skill embedding.
        
        Args:
            person_idx: Index of person
            
        Returns:
            skill_scores: {skill_idx: similarity_score}
        """
        # Get person's current skills
        person_skill_indices = list(self.person_skills[person_idx])
        
        if not person_skill_indices:
            # Person has no skills -> return zero scores
            return {i: 0.0 for i in range(self.num_skills)}
        
        # Compute person embedding as mean of their skill embeddings
        person_skill_embeds = self.skill_embeddings[person_skill_indices]
        person_embedding = person_skill_embeds.mean(dim=0)
        
        # Compute cosine similarity to all skills
        similarities = F.cosine_similarity(
            person_embedding.unsqueeze(0),
            self.skill_embeddings,
            dim=1
        )
        
        skill_scores = {i: similarities[i].item() for i in range(self.num_skills)}
        
        return skill_scores
    
    # ========================================================================
    # EVALUATION METRICS
    # ========================================================================
    
    def evaluate_ranking(self, 
                        person_idx: int,
                        skill_scores: Dict[int, float],
                        positive_skills: set,
                        negative_skills: set) -> Dict[str, float]:
        """
        Evaluate ranking for a single person.
        
        Args:
            person_idx: Person index
            skill_scores: {skill_idx: score}
            positive_skills: Set of ground truth positive skill indices
            negative_skills: Set of negative skill indices
            
        Returns:
            metrics: {hits@k, mrr, auc}
        """
        # Get scores for test skills (positives + negatives)
        test_skills = list(positive_skills | negative_skills)
        test_scores = [(skill_idx, skill_scores[skill_idx]) for skill_idx in test_skills]
        
        # Sort by score descending
        test_scores.sort(key=lambda x: -x[1])
        ranked_skills = [skill_idx for skill_idx, _ in test_scores]
        
        # Compute metrics
        metrics = {}
        
        # Hits@K
        for k in K_VALUES:
            top_k = set(ranked_skills[:k])
            hits = len(top_k & positive_skills) / len(positive_skills)
            metrics[f'hits@{k}'] = hits
        
        # MRR (Mean Reciprocal Rank)
        reciprocal_ranks = []
        for pos_skill in positive_skills:
            if pos_skill in ranked_skills:
                rank = ranked_skills.index(pos_skill) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)
        metrics['mrr'] = np.mean(reciprocal_ranks)
        
        # AUC
        if len(positive_skills) > 0 and len(negative_skills) > 0:
            y_true = [1 if s in positive_skills else 0 for s in test_skills]
            y_score = [skill_scores[s] for s in test_skills]
            try:
                metrics['auc'] = roc_auc_score(y_true, y_score)
            except ValueError:
                metrics['auc'] = 0.5  # Random baseline if all same label
        else:
            metrics['auc'] = 0.5
        
        return metrics
    
    def evaluate_baseline(self, 
                         baseline_name: str,
                         get_scores_fn,
                         test_persons: List[int],
                         test_positives: Dict[int, set],
                         test_negatives: Dict[int, set]) -> Dict[str, float]:
        """
        Evaluate a baseline method on test set.
        
        Args:
            baseline_name: Name of baseline
            get_scores_fn: Function(person_idx) -> skill_scores
            test_persons: List of test person indices
            test_positives: {person_idx: set of positive skill indices}
            test_negatives: {person_idx: set of negative skill indices}
            
        Returns:
            avg_metrics: Average metrics across all test persons
        """
        logger.info(f"\nEvaluating {baseline_name} on {len(test_persons)} test persons...")
        
        all_metrics = []
        
        for person_idx in tqdm(test_persons, desc=baseline_name):
            # Get skill scores for this person
            if callable(get_scores_fn):
                skill_scores = get_scores_fn(person_idx)
            else:
                skill_scores = get_scores_fn  # Pre-computed scores
            
            # Evaluate
            metrics = self.evaluate_ranking(
                person_idx,
                skill_scores,
                test_positives[person_idx],
                test_negatives[person_idx]
            )
            all_metrics.append(metrics)
        
        # Average metrics
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in all_metrics])
        
        logger.info(f"\n{baseline_name} Results:")
        for key, value in avg_metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        return avg_metrics
    
    # ========================================================================
    # TEST SET PREPARATION
    # ========================================================================
    
    def prepare_test_set(self, test_ratio: float = 0.1,
                        num_negatives: int = 5) -> Tuple[List[int], Dict, Dict]:
        """
        Prepare leak-safe test set by splitting persons.
        
        Args:
            test_ratio: Fraction of persons for testing
            num_negatives: Number of negative samples per positive
            
        Returns:
            test_persons: List of test person indices
            test_positives: {person_idx: set of positive skills}
            test_negatives: {person_idx: set of negative skills}
        """
        logger.info("\nPreparing test set...")
        
        # Split persons (only those with at least one skill)
        all_persons = [p for p in range(self.num_persons) if len(self.person_skills[p]) > 0]
        logger.info(f"Total persons with skills: {len(all_persons)}/{self.num_persons}")
        
        np.random.shuffle(all_persons)
        
        num_test = int(len(all_persons) * test_ratio)
        test_persons = all_persons[:num_test]
        
        logger.info(f"Test set: {len(test_persons)} persons")
        
        # For each test person, sample positives and negatives
        test_positives = {}
        test_negatives = {}
        
        for person_idx in test_persons:
            # Positives = person's actual skills
            positives = self.person_skills[person_idx]
            
            # Sample negatives from skills NOT connected to person
            all_skills = set(range(self.num_skills))
            candidate_negatives = all_skills - positives
            
            num_neg = min(num_negatives * len(positives), len(candidate_negatives))
            negatives = set(np.random.choice(list(candidate_negatives), 
                                            size=num_neg, 
                                            replace=False))
            
            test_positives[person_idx] = positives
            test_negatives[person_idx] = negatives
        
        logger.info(f"Average positives per person: {np.mean([len(v) for v in test_positives.values()]):.1f}")
        logger.info(f"Average negatives per person: {np.mean([len(v) for v in test_negatives.values()]):.1f}")
        
        return test_persons, test_positives, test_negatives
    
    # ========================================================================
    # MAIN EVALUATION
    # ========================================================================
    
    def run_evaluation(self):
        """Run full baseline evaluation."""
        logger.info("\n" + "="*80)
        logger.info("BASELINE EVALUATION")
        logger.info("="*80)
        
        # Prepare test set
        test_persons, test_positives, test_negatives = self.prepare_test_set(
            test_ratio=0.1,
            num_negatives=5
        )
        
        results = {}
        
        # Baseline 1: Popularity
        popularity_scores = self.popularity_baseline()
        results['popularity'] = self.evaluate_baseline(
            "Popularity Baseline",
            popularity_scores,
            test_persons,
            test_positives,
            test_negatives
        )
        
        # Baseline 2: Embedding Similarity
        results['embedding_similarity'] = self.evaluate_baseline(
            "Embedding Similarity Baseline",
            self.embedding_similarity_baseline,
            test_persons,
            test_positives,
            test_negatives
        )
        
        # Save results
        with open(BASELINE_RESULTS_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("\n" + "="*80)
        logger.info("BASELINE EVALUATION COMPLETE")
        logger.info("="*80)
        logger.info(f"\nResults saved to: {BASELINE_RESULTS_PATH}")
        
        # Print comparison table
        self.print_comparison_table(results)
        
        return results
    
    def print_comparison_table(self, results: Dict):
        """Print comparison table of baseline results."""
        logger.info("\n" + "="*80)
        logger.info("BASELINE COMPARISON")
        logger.info("="*80)
        
        # Header
        metrics = list(results['popularity'].keys())
        header = f"{'Baseline':<30} " + " ".join([f"{m:>10}" for m in metrics])
        logger.info(header)
        logger.info("-" * len(header))
        
        # Rows
        for baseline_name, baseline_results in results.items():
            row = f"{baseline_name:<30} "
            row += " ".join([f"{baseline_results[m]:>10.4f}" for m in metrics])
            logger.info(row)
        
        logger.info("="*80)


def main():
    """Main execution."""
    try:
        evaluator = BaselineEvaluator(HETERODATA_PATH)
        results = evaluator.run_evaluation()
        
        logger.info("\n[OK] Baseline evaluation completed successfully!")
        logger.info("\nNext step: Train GNN with python scripts/train_linkpred_gnn.py")
        
    except Exception as e:
        logger.error(f"Baseline evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
