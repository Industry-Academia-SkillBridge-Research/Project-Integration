"""
Build XAI Dataset Script.

Generates explanation dataset for surrogate model training.
Reads candidate-role pairs and creates one row per role-required skill.

Usage:
    python -m xai.scripts.build_xai_dataset
"""
import sys
from pathlib import Path
import logging
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from xai.services.xai_dataset_builder import XAIDatasetBuilder
from services.gnn_inference_service import gnn_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution."""
    logger.info("=" * 80)
    logger.info("Building XAI Dataset")
    logger.info("=" * 80)
    
    # Configuration
    labels_path = "readiness_labels.csv"
    output_path = "xai/output/xai_missing_skill_dataset.csv"
    max_pairs = None  # Set to limit for testing (e.g., 10)
    
    logger.info(f"Labels source: {labels_path}")
    logger.info(f"Output: {output_path}")
    
    # Load GNN model first
    logger.info("Loading GNN model...")
    try:
        base_path = Path(__file__).parent.parent.parent / "GNN-Link-Prediction"
        model_path = str(base_path / "models" / "best_gnn_linkpred.pt")
        data_path = str(base_path / "output" / "heterodata_lp.pt")
        id_maps_path = str(base_path / "output" / "id_maps.json")
        
        gnn_service.load_model(model_path, data_path, id_maps_path)
        logger.info("[OK] GNN model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load GNN model: {e}")
        logger.error("Dataset building requires GNN model")
        return
    
    # Load candidate-role pairs
    logger.info("Loading candidate-role pairs...")
    try:
        df_labels = pd.read_csv(labels_path)
        logger.info(f"Found {len(df_labels)} labeled pairs")
    except FileNotFoundError:
        logger.error(f"Labels file not found: {labels_path}")
        logger.info("Please ensure readiness_labels.csv exists")
        return
    
    # Extract unique pairs
    pairs = df_labels[['candidate_id', 'role_key']].drop_duplicates()
    candidate_role_pairs = [
        (row['candidate_id'], row['role_key'])
        for _, row in pairs.iterrows()
    ]
    
    if max_pairs:
        logger.info(f"Limiting to first {max_pairs} pairs for testing")
        candidate_role_pairs = candidate_role_pairs[:max_pairs]
    
    logger.info(f"Processing {len(candidate_role_pairs)} unique candidate-role pairs")
    
    # Build dataset
    logger.info("Initializing dataset builder...")
    builder = XAIDatasetBuilder()
    
    logger.info("Building dataset (this may take a while)...")
    try:
        builder.build_dataset(
            candidate_role_pairs=candidate_role_pairs,
            output_path=output_path
        )
        
        # Verify output
        df_output = pd.read_csv(output_path)
        logger.info("")
        logger.info("=" * 80)
        logger.info("Dataset built successfully!")
        logger.info(f"Output: {output_path}")
        logger.info(f"Total rows: {len(df_output)}")
        logger.info(f"Features: {list(df_output.columns)}")
        logger.info("")
        logger.info("Sample statistics:")
        logger.info(f"  - final_score range: [{df_output['final_score'].min():.4f}, {df_output['final_score'].max():.4f}]")
        logger.info(f"  - Unique candidates: {df_output['candidate_id'].nunique()}")
        logger.info(f"  - Unique roles: {df_output['role_key'].nunique()}")
        logger.info(f"  - Unique skills: {df_output['skill'].nunique()}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Dataset building failed: {e}", exc_info=True)
        return
    
    logger.info("Next step: Train surrogate model with train_xai_surrogate.py")


if __name__ == "__main__":
    main()
