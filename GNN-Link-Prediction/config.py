"""
Configuration file for GNN Link Prediction system.
Centralized settings for Neo4j connection, model hyperparameters, and paths.
"""

import os
from pathlib import Path

# ============================================================================
# NEO4J CONNECTION - Desktop
# ============================================================================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "tharusha@2001"

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Output files
HETERODATA_PATH = OUTPUT_DIR / "heterodata_lp.pt"
TRAIN_DATA_PATH = OUTPUT_DIR / "train_data.pt"
VAL_DATA_PATH = OUTPUT_DIR / "val_data.pt"
TEST_DATA_PATH = OUTPUT_DIR / "test_data.pt"
ID_MAPS_PATH = OUTPUT_DIR / "id_maps.json"
STATS_PATH = OUTPUT_DIR / "dataset_stats.json"

# Model checkpoints
BEST_MODEL_PATH = MODELS_DIR / "best_gnn_linkpred.pt"

# Results
BASELINE_RESULTS_PATH = OUTPUT_DIR / "baseline_results.json"
GNN_RESULTS_PATH = OUTPUT_DIR / "gnn_results.json"
FINAL_COMPARISON_PATH = OUTPUT_DIR / "final_comparison.csv"

# ============================================================================
# DATASET PARAMETERS
# ============================================================================
RANDOM_SEED = 42

# Link prediction target
TARGET_RELATION = ("person", "has_skill", "skill")

# Train/Val/Test split ratios (by person)
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

# Negative sampling
NUM_NEGATIVES_PER_POSITIVE = 5

# Feature dimensions
SKILL_EMBEDDING_DIM = 384  # Expected dimension of skill embeddings
PERSON_FEATURE_DIM = 3  # [num_skills, num_projects, experience_months]

# ============================================================================
# GNN MODEL HYPERPARAMETERS
# ============================================================================
# Model architecture
HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.3
GNN_TYPE = "GraphSAGE"  # Options: "GraphSAGE", "RGCN"

# Training
BATCH_SIZE = 1024
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-5
MAX_EPOCHS = 100
EARLY_STOPPING_PATIENCE = 10

# Early stopping metric
EARLY_STOPPING_METRIC = "val_hits@10"  # Options: "val_mrr", "val_hits@10", "val_auc"

# ============================================================================
# EVALUATION METRICS
# ============================================================================
K_VALUES = [5, 10, 20]  # For Hits@K evaluation

# ============================================================================
# SANITY CHECK PARAMETERS
# ============================================================================
OVERFIT_TEST_NUM_PERSONS = 100
OVERFIT_TEST_MAX_EPOCHS = 50
OVERFIT_TEST_SUCCESS_THRESHOLD = 0.90  # Hits@10 >= 0.90

MIN_SKILLS_PER_PERSON_THRESHOLD = 5  # Warn if many persons have < 5 skills

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FILE = OUTPUT_DIR / "gnn_linkpred.log"

# ============================================================================
# GO / NO-GO DECISION CRITERIA
# ============================================================================
GO_CRITERIA = {
    "gnn_beats_popularity_hits10": True,  # GNN Hits@10 > Popularity Hits@10
    "gnn_beats_popularity_mrr": True,     # GNN MRR > Popularity MRR
    "gnn_beats_embedding_hits10": True,   # GNN Hits@10 > Embedding Hits@10
    "min_gnn_hits10": 0.10,               # GNN Hits@10 >= 0.10 (absolute threshold)
    "min_gnn_mrr": 0.05,                  # GNN MRR >= 0.05
}

# ============================================================================
# DEVICE
# ============================================================================
import torch
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"[CONFIG] Using device: {DEVICE}")
print(f"[CONFIG] Output directory: {OUTPUT_DIR}")
print(f"[CONFIG] Random seed: {RANDOM_SEED}")
