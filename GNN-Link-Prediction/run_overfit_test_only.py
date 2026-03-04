"""
Run ONLY the mini-overfit test.

This is useful for debugging model architecture issues.
If this test fails, fix it before running full training.

Usage:
    python run_overfit_test_only.py
    
Or with custom parameters:
    python run_overfit_test_only.py --num_persons 100 --max_epochs 1000
"""

import sys
import logging
from pathlib import Path
import torch
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from config import HETERODATA_PATH, LOG_LEVEL
from scripts.train_linkpred_gnn import overfit_test

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/overfit_test.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Run mini-overfit test')
    parser.add_argument('--num_persons', type=int, default=50,
                       help='Number of persons for overfit test (default: 50)')
    parser.add_argument('--max_epochs', type=int, default=500,
                       help='Max epochs for overfit test (default: 500)')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("STANDALONE OVERFIT TEST")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Number of persons: {args.num_persons}")
    logger.info(f"  Max epochs: {args.max_epochs}")
    logger.info(f"  Data path: {HETERODATA_PATH}")
    logger.info("")
    
    # Load data
    logger.info("Loading HeteroData...")
    data = torch.load(HETERODATA_PATH, weights_only=False)
    
    # Add reverse edges for bidirectional message passing
    logger.info("Adding reverse edges...")
    if ('person', 'has_skill', 'skill') in data.edge_types:
        data['skill', 'rev_has_skill', 'person'].edge_index = \
            data['person', 'has_skill', 'skill'].edge_index.flip(0)
    
    if ('person', 'worked_on', 'project') in data.edge_types:
        data['project', 'rev_worked_on', 'person'].edge_index = \
            data['person', 'worked_on', 'project'].edge_index.flip(0)
    
    if ('project', 'uses_technology', 'skill') in data.edge_types:
        data['skill', 'rev_uses_technology', 'project'].edge_index = \
            data['project', 'uses_technology', 'skill'].edge_index.flip(0)
    
    if ('skill', 'belongs_to_category', 'skill_category') in data.edge_types:
        data['skill_category', 'rev_belongs_to_category', 'skill'].edge_index = \
            data['skill', 'belongs_to_category', 'skill_category'].edge_index.flip(0)
    
    logger.info("Data loaded successfully\n")
    
    # Run overfit test
    success = overfit_test(data, num_persons=args.num_persons, max_epochs=args.max_epochs)
    
    # Final message
    if success:
        logger.info("\n" + "="*80)
        logger.info("SUCCESS: Overfit test PASSED")
        logger.info("="*80)
        logger.info("Your model architecture is working correctly!")
        logger.info("You can now proceed with full training.")
        sys.exit(0)
    else:
        logger.error("\n" + "="*80)
        logger.error("FAILURE: Overfit test FAILED")
        logger.error("="*80)
        logger.error("Please review the diagnostics above and fix the issues.")
        logger.error("Common fixes:")
        logger.error("  1. Increase max_epochs: --max_epochs 1000")
        logger.error("  2. Check your skill embeddings (are they all zeros?)")
        logger.error("  3. Verify message passing is working")
        logger.error("  4. Try a different GNN architecture")
        sys.exit(1)


if __name__ == "__main__":
    main()
