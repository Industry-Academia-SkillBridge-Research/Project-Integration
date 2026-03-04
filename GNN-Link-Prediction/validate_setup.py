"""
Pre-flight validation script.
Run this BEFORE the full pipeline to check if everything is configured correctly.
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("GNN LINK PREDICTION - PRE-FLIGHT VALIDATION")
print("=" * 80)
print()

all_checks_passed = True

# ============================================================================
# CHECK 1: Python Dependencies
# ============================================================================
print("[CHECK 1/5] Python Dependencies...")

required_packages = {
    'torch': 'PyTorch',
    'torch_geometric': 'PyTorch Geometric',
    'neo4j': 'Neo4j Driver',
    'numpy': 'NumPy',
    'pandas': 'Pandas',
    'sklearn': 'Scikit-learn',
    'tqdm': 'TQDM'
}

missing_packages = []

for package, name in required_packages.items():
    try:
        __import__(package)
        print(f"  ✓ {name} installed")
    except ImportError:
        print(f"  ✗ {name} MISSING")
        missing_packages.append(name)
        all_checks_passed = False

if missing_packages:
    print("\n  ⚠️  Install missing packages:")
    print(f"     pip install {' '.join(missing_packages).lower().replace(' ', '-')}")
else:
    print("  ✓ All dependencies installed")

print()

# ============================================================================
# CHECK 2: Configuration File
# ============================================================================
print("[CHECK 2/5] Configuration File...")

try:
    from config import (
        NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
        HETERODATA_PATH, RANDOM_SEED, DEVICE
    )
    print(f"  ✓ config.py loaded successfully")
    print(f"  ✓ Neo4j URI: {NEO4J_URI}")
    print(f"  ✓ Neo4j User: {NEO4J_USER}")
    
    if NEO4J_PASSWORD == "tharusha@2001":
        print(f"  ✓ Neo4j Password: configured")
    elif NEO4J_PASSWORD == "your_password_here" or not NEO4J_PASSWORD:
        print(f"  ✗ Neo4j Password: NOT SET (change in config.py)")
        all_checks_passed = False
    else:
        print(f"  ✓ Neo4j Password: configured")
    
    print(f"  ✓ Random Seed: {RANDOM_SEED}")
    print(f"  ✓ Device: {DEVICE}")
    
except Exception as e:
    print(f"  ✗ Failed to load config.py: {e}")
    all_checks_passed = False

print()

# ============================================================================
# CHECK 3: Neo4j Connection
# ============================================================================
print("[CHECK 3/5] Neo4j Connection...")

try:
    from neo4j import GraphDatabase
    from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        test_value = result.single()['test']
        
        if test_value == 1:
            print(f"  ✓ Connected to Neo4j at {NEO4J_URI}")
        else:
            print(f"  ✗ Neo4j query returned unexpected value")
            all_checks_passed = False
    
    driver.close()
    
except Exception as e:
    print(f"  ✗ Failed to connect to Neo4j: {e}")
    print(f"     - Check Neo4j is running (http://localhost:7474)")
    print(f"     - Verify password in config.py")
    all_checks_passed = False

print()

# ============================================================================
# CHECK 4: Neo4j Data
# ============================================================================
print("[CHECK 4/5] Neo4j Data Availability...")

if all_checks_passed or 'driver' in locals():
    try:
        from neo4j import GraphDatabase
        from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # Check Person nodes
            result = session.run("MATCH (p:Person) RETURN count(p) as count")
            person_count = result.single()['count']
            
            if person_count > 0:
                print(f"  ✓ Person nodes: {person_count}")
            else:
                print(f"  ✗ No Person nodes found!")
                all_checks_passed = False
            
            # Check Skill nodes
            result = session.run("MATCH (s:Skill) RETURN count(s) as count")
            skill_count = result.single()['count']
            
            if skill_count > 0:
                print(f"  ✓ Skill nodes: {skill_count}")
            else:
                print(f"  ✗ No Skill nodes found!")
                all_checks_passed = False
            
            # Check HAS_SKILL edges
            result = session.run(
                "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) RETURN count(*) as count"
            )
            edge_count = result.single()['count']
            
            if edge_count > 0:
                print(f"  ✓ HAS_SKILL edges: {edge_count}")
            else:
                print(f"  ✗ No HAS_SKILL edges found!")
                all_checks_passed = False
            
            # Check skill embeddings
            result = session.run(
                """
                MATCH (s:Skill)
                WHERE s.embedding IS NOT NULL AND size(s.embedding) > 0
                RETURN count(s) as count
                """
            )
            embed_count = result.single()['count']
            
            if embed_count > 0:
                coverage = (embed_count / skill_count * 100) if skill_count > 0 else 0
                print(f"  ✓ Skills with embeddings: {embed_count}/{skill_count} ({coverage:.1f}%)")
                
                if coverage < 80:
                    print(f"     ⚠️  Warning: Low embedding coverage (<80%)")
            else:
                print(f"  ✗ No skill embeddings found!")
                print(f"     Run embedding generation script first")
                all_checks_passed = False
        
        driver.close()
        
    except Exception as e:
        print(f"  ✗ Failed to query Neo4j data: {e}")
        all_checks_passed = False
else:
    print("  ⊘ Skipped (Neo4j not connected)")

print()

# ============================================================================
# CHECK 5: Output Directories
# ============================================================================
print("[CHECK 5/5] Output Directories...")

try:
    from config import OUTPUT_DIR, MODELS_DIR
    
    if OUTPUT_DIR.exists():
        print(f"  ✓ Output directory exists: {OUTPUT_DIR}")
    else:
        print(f"  ℹ Creating output directory: {OUTPUT_DIR}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if MODELS_DIR.exists():
        print(f"  ✓ Models directory exists: {MODELS_DIR}")
    else:
        print(f"  ℹ Creating models directory: {MODELS_DIR}")
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
except Exception as e:
    print(f"  ✗ Failed to check directories: {e}")
    all_checks_passed = False

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
if all_checks_passed:
    print("✓ PRE-FLIGHT VALIDATION PASSED")
    print("=" * 80)
    print()
    print("System is ready! Run the pipeline:")
    print("  python scripts/export_neo4j_to_pyg_lp.py")
    print("  python scripts/eval_baselines.py")
    print("  python scripts/train_linkpred_gnn.py")
    print()
    print("Or run all at once:")
    print("  .\\run_pipeline.ps1")
    print()
else:
    print("✗ PRE-FLIGHT VALIDATION FAILED")
    print("=" * 80)
    print()
    print("Fix the issues above before running the pipeline.")
    print()
    sys.exit(1)
