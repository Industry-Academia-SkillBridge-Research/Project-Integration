# 📦 GNN-Link-Prediction Project Structure

## Complete File Tree

```
F:\CV Parser Agent\GNN-Link-Prediction\
│
├── 📄 config.py                           [Configuration - EDIT THIS FIRST]
├── 📄 requirements.txt                    [Python dependencies]
├── 📄 validate_setup.py                   [Pre-flight checks - RUN FIRST]
│
├── 🚀 run_pipeline.ps1                    [Full pipeline runner - MAIN SCRIPT]
│
├── 📖 README.md                           [Complete documentation]
├── 📖 QUICKSTART.md                       [Quick reference guide]
├── 📖 EXECUTIVE_SUMMARY.md               [High-level overview]
├── 📖 TESTING_GUIDE.md                    [Testing & troubleshooting]
├── 📖 PROJECT_STRUCTURE.md               [This file]
│
├── 📁 scripts/                            [Executable Python scripts]
│   ├── __init__.py
│   ├── export_neo4j_to_pyg_lp.py         [Step 1: Neo4j → PyG export]
│   ├── eval_baselines.py                  [Step 2: Baseline evaluation]
│   └── train_linkpred_gnn.py             [Step 3: GNN training]
│
├── 📁 output/                             [Generated results]
│   ├── heterodata_lp.pt                  [PyG HeteroData object]
│   ├── id_maps.json                       [Node ID mappings]
│   ├── dataset_stats.json                 [Dataset statistics]
│   ├── baseline_results.json              [Baseline metrics]
│   ├── gnn_results.json                   [GNN metrics]
│   ├── final_comparison.csv               [Comparison table]
│   ├── final_report.json                  [GO/NO-GO decision]
│   └── gnn_linkpred.log                   [Complete logs]
│
└── 📁 models/                             [Saved models]
    └── best_gnn_linkpred.pt              [Best model checkpoint]
```

---

## File Purposes

### 🔧 Configuration & Setup

#### `config.py` ⭐ MUST EDIT
**Purpose:** Central configuration for entire system

**Key settings:**
```python
# Neo4j connection (CHANGE PASSWORD!)
NEO4J_PASSWORD = "your_password_here"

# Model architecture
HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.3

# Training
LEARNING_RATE = 0.001
MAX_EPOCHS = 100
BATCH_SIZE = 1024

# Evaluation
K_VALUES = [5, 10, 20]
```

**When to edit:**
- Always: Set Neo4j password
- For tuning: Adjust model/training hyperparameters
- For experimentation: Change split ratios, negative sampling

---

#### `requirements.txt`
**Purpose:** Python dependencies for pip install

**Contents:**
- torch (PyTorch)
- torch-geometric (PyG)
- neo4j (Neo4j driver)
- numpy, pandas, scikit-learn
- tqdm (progress bars)

**Usage:**
```bash
pip install -r requirements.txt
```

---

#### `validate_setup.py` ⭐ RUN FIRST
**Purpose:** Pre-flight validation before running pipeline

**Checks:**
1. Python dependencies installed
2. Config file loads correctly
3. Neo4j connection works
4. Required data exists (Person, Skill, edges)
5. Skill embeddings present
6. Output directories ready

**Usage:**
```bash
python validate_setup.py
```

**Output:** ✓ PASS or ✗ FAIL with specific issues

---

### 🚀 Execution Scripts

#### `run_pipeline.ps1` ⭐ MAIN SCRIPT
**Purpose:** Run complete pipeline in one command

**What it does:**
1. Activates virtual environment
2. Runs export_neo4j_to_pyg_lp.py
3. Runs eval_baselines.py
4. Runs train_linkpred_gnn.py
5. Displays final report with GO/NO-GO decision

**Usage:**
```powershell
.\run_pipeline.ps1
```

**Duration:** 10-60 minutes depending on data size

---

### 📜 Python Scripts (scripts/)

#### `export_neo4j_to_pyg_lp.py` (Step 1)
**Purpose:** Export Neo4j graph → PyTorch Geometric HeteroData

**What it does:**
1. Connects to Neo4j
2. Exports Person, Skill, Project, SkillCategory nodes
3. Builds node features:
   - Person: [num_skills, num_projects, experience] (normalized)
   - Skill: 384-dim embeddings
   - Project: Mean of skill embeddings
   - SkillCategory: Mean of member skill embeddings
4. Exports all edges (HAS_SKILL, WORKED_ON, etc.)
5. Saves HeteroData + ID maps + statistics

**Input:** Neo4j database  
**Output:** `output/heterodata_lp.pt`, `id_maps.json`, `dataset_stats.json`

**Runtime:** 1-10 minutes

---

#### `eval_baselines.py` (Step 2)
**Purpose:** Evaluate baseline methods for comparison

**Baselines:**
1. **Popularity:** Rank skills by global frequency
2. **Embedding Similarity:** Rank by cosine similarity to person's skill embedding

**What it does:**
1. Loads HeteroData
2. Prepares test set (10% persons)
3. Evaluates both baselines
4. Computes Hits@K, MRR, AUC
5. Saves results

**Input:** `output/heterodata_lp.pt`  
**Output:** `output/baseline_results.json`

**Runtime:** 2-15 minutes

---

#### `train_linkpred_gnn.py` (Step 3)
**Purpose:** Train GNN, evaluate, and make GO/NO-GO decision

**What it does:**
1. **Sanity Check: Overfit Test**
   - Takes 100 persons
   - Trains to near-perfect accuracy
   - Verifies model can learn
   
2. **Data Preparation**
   - Leak-safe split (80/10/10 by person)
   - Sample negatives (5 per positive)
   
3. **GNN Training**
   - 2-layer Heterogeneous GraphSAGE
   - Dot product decoder
   - BCE loss with negatives
   - Early stopping on val Hits@10
   
4. **Evaluation**
   - Test set: Hits@5/10/20, MRR, AUC
   - Compare vs baselines
   
5. **GO/NO-GO Decision**
   - Automated criteria check
   - Generate final report

**Input:** `output/heterodata_lp.pt`, `baseline_results.json`  
**Output:** 
- `models/best_gnn_linkpred.pt` (trained model)
- `output/gnn_results.json` (metrics)
- `output/final_comparison.csv` (table)
- `output/final_report.json` (decision)

**Runtime:** 10-60 minutes (depends on data size & GPU)

---

### 📖 Documentation

#### `README.md` - Complete Guide
**Audience:** Developers, researchers  
**Contents:**
- Full system overview
- Methodology details
- Usage instructions
- Hyperparameter tuning
- Expected results
- Troubleshooting

**Length:** ~500 lines

---

#### `QUICKSTART.md` - Quick Reference
**Audience:** Users who want fast answers  
**Contents:**
- 1-page command reference
- Key configurations
- Output files
- Common issues
- Performance metrics

**Length:** ~200 lines

---

#### `EXECUTIVE_SUMMARY.md` - High-Level Overview
**Audience:** Managers, stakeholders  
**Contents:**
- Problem & solution
- Architecture diagrams
- Business impact
- Success metrics
- Cost-benefit analysis

**Length:** ~400 lines

---

#### `TESTING_GUIDE.md` - Testing & Troubleshooting
**Audience:** QA, debugging  
**Contents:**
- Step-by-step testing
- Expected outputs
- Interpreting results
- Troubleshooting guide
- Performance benchmarks

**Length:** ~500 lines

---

#### `PROJECT_STRUCTURE.md` - This File
**Audience:** New team members  
**Contents:**
- Complete file tree
- File purposes
- Usage workflows
- Cross-references

---

### 📊 Output Files (output/)

#### `heterodata_lp.pt` (Binary)
**Format:** PyTorch saved object  
**Size:** 10-100 MB  
**Contains:** Complete heterogeneous graph
- Node features for all types
- Edge indices for all relationships
- Metadata

**Used by:** All downstream scripts

---

#### `id_maps.json`
**Format:** JSON  
**Contains:** Node ID → index mappings
```json
{
  "person": {"person_001": 0, "person_002": 1, ...},
  "skill": {"Python": 0, "TensorFlow": 1, ...},
  "project": {...},
  "skill_category": {...}
}
```

**Used for:** Converting between Neo4j IDs and tensor indices

---

#### `dataset_stats.json` ⭐ CHECK THIS
**Format:** JSON  
**Contains:** Data quality metrics
```json
{
  "num_persons": 1250,
  "num_skills": 1578,
  "num_has_skill_edges": 8542,
  "skill_embedding_coverage": 0.95,
  "skills_missing_embeddings": 78,
  "person_feature_stats": {...}
}
```

**Use:** Diagnose data quality issues

---

#### `baseline_results.json`
**Format:** JSON  
**Contains:** Baseline metrics
```json
{
  "popularity": {
    "hits@5": 0.082, "hits@10": 0.105, "mrr": 0.068, "auc": 0.612
  },
  "embedding_similarity": {
    "hits@5": 0.124, "hits@10": 0.165, "mrr": 0.092, "auc": 0.701
  }
}
```

---

#### `gnn_results.json`
**Format:** JSON  
**Contains:** GNN metrics
```json
{
  "hits@5": 0.158,
  "hits@10": 0.214,
  "hits@20": 0.312,
  "mrr": 0.118,
  "auc": 0.748
}
```

---

#### `final_comparison.csv` ⭐ EASY TO SHARE
**Format:** CSV (Excel-ready)  
**Contains:** Side-by-side comparison

| Method | Hits@5 | Hits@10 | Hits@20 | MRR | AUC |
|--------|--------|---------|---------|-----|-----|
| GNN | 0.1580 | 0.2140 | 0.3120 | 0.1180 | 0.7480 |
| Popularity | 0.0820 | 0.1050 | 0.1420 | 0.0680 | 0.6120 |
| Embedding Similarity | 0.1240 | 0.1650 | 0.2280 | 0.0920 | 0.7010 |

**Use:** Share with stakeholders, include in reports

---

#### `final_report.json` ⭐ DECISION HERE
**Format:** JSON  
**Contains:** GO/NO-GO decision + all checks
```json
{
  "decision": "GO",
  "checks": {
    "gnn_beats_popularity_hits10": true,
    "gnn_beats_popularity_mrr": true,
    "gnn_beats_embedding_hits10": true,
    "min_gnn_hits10": true,
    "min_gnn_mrr": true
  },
  "gnn_results": {...},
  "baseline_results": {...},
  "overfit_test_passed": true
}
```

**Use:** 
- Production readiness decision
- Automated CI/CD gates
- Performance tracking

---

#### `gnn_linkpred.log` ⭐ DEBUGGING
**Format:** Plain text  
**Contains:** Complete logs from all scripts
- Timestamps
- INFO/WARNING/ERROR messages
- Training progress
- Evaluation results

**Use:** Debugging, understanding what happened

---

### 💾 Model Files (models/)

#### `best_gnn_linkpred.pt`
**Format:** PyTorch state dict  
**Size:** 1-10 MB  
**Contains:** Trained model weights

**Usage:**
```python
from train_linkpred_gnn import LinkPredictionModel
import torch

# Load model
model = LinkPredictionModel(...)
model.load_state_dict(torch.load('models/best_gnn_linkpred.pt'))
model.eval()

# Use for inference
z_dict = model(data.x_dict, data.edge_index_dict)
scores = model.decode_all(z_dict['person'], z_dict['skill'])
```

---

## Common Workflows

### 🎯 Workflow 1: First-Time Setup

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Neo4j password
# Edit config.py line 12

# 3. Validate setup
python validate_setup.py

# 4. Run full pipeline
.\run_pipeline.ps1

# 5. Check results
Get-Content output/final_report.json
```

---

### 🔧 Workflow 2: Hyperparameter Tuning

```powershell
# 1. Edit config.py
# Change HIDDEN_DIM, LEARNING_RATE, etc.

# 2. Re-train only (skip data export and baselines)
python scripts/train_linkpred_gnn.py

# 3. Compare results
Get-Content output/gnn_results.json

# 4. Repeat until GO
```

---

### 🔄 Workflow 3: Update with New Data

```powershell
# 1. Re-export data (after Neo4j updates)
python scripts/export_neo4j_to_pyg_lp.py

# 2. Check statistics changed
Get-Content output/dataset_stats.json

# 3. Re-evaluate baselines
python scripts/eval_baselines.py

# 4. Re-train GNN
python scripts/train_linkpred_gnn.py

# 5. Compare with previous results
```

---

### 🧪 Workflow 4: Quick Sanity Check

```powershell
# Just run validation
python validate_setup.py

# Should complete in <30 seconds
# Catches: connection issues, missing data, config errors
```

---

### 📊 Workflow 5: Share Results

```powershell
# Export comparison table
Get-Content output/final_comparison.csv | Out-File results.txt

# Or open in Excel
Start-Process output/final_comparison.csv

# Share final report
Get-Content output/final_report.json | ConvertFrom-Json | ConvertTo-Json
```

---

## Key Design Decisions

### Why Separate Scripts?
- **Modularity:** Run only what you need
- **Debugging:** Isolate failures to specific steps
- **Efficiency:** Skip expensive steps when unnecessary
- **Testing:** Test individual components

### Why PowerShell Runner?
- **Windows-friendly:** Native shell on Windows
- **Error handling:** Catches failures between steps
- **User feedback:** Colored output, progress indicators
- **Automation:** Can be integrated into CI/CD

### Why Multiple Docs?
- **Different audiences:** Devs vs managers vs QA
- **Different use cases:** Quick ref vs deep dive
- **Discoverability:** Easy to find relevant info
- **Maintenance:** Update specific sections independently

### Why JSON Outputs?
- **Machine-readable:** Easy to parse in other scripts
- **Human-readable:** Can inspect manually
- **Standard:** Works with Python, JavaScript, PowerShell, etc.
- **Version control:** Text-based, git-friendly

---

## File Dependencies

```
config.py
    ↓
validate_setup.py (validates config)
    ↓
export_neo4j_to_pyg_lp.py (reads config, writes heterodata)
    ↓
eval_baselines.py (reads heterodata, writes baseline_results)
    ↓
train_linkpred_gnn.py (reads heterodata + baseline_results, writes gnn_results + model)
    ↓
final_report.json (GO/NO-GO decision)
```

---

## Disk Space Requirements

### Minimum
- Code: ~1 MB
- Output: ~20 MB
- Models: ~5 MB
- **Total: ~30 MB**

### Typical (1000 persons, 1500 skills)
- Code: ~1 MB
- Output: ~50 MB (heterodata ~30 MB, logs ~10 MB, results ~10 MB)
- Models: ~5 MB
- **Total: ~60 MB**

### Large (10000 persons, 5000 skills)
- Code: ~1 MB
- Output: ~500 MB (heterodata ~400 MB, logs ~50 MB, results ~50 MB)
- Models: ~10 MB
- **Total: ~600 MB**

---

## Version History

### v1.0 (Current)
- Initial release
- Heterogeneous GraphSAGE
- Leak-safe evaluation
- Strong baselines
- GO/NO-GO decision
- Complete documentation

### Planned Features (v1.1+)
- RGCN support (alternative GNN)
- HGT support (advanced hetero GNN)
- Hyperparameter search (grid/random)
- Online learning (incremental updates)
- Explainability (attention weights)
- Fairness metrics (bias detection)

---

## Related Systems

This GNN system is part of the larger CV Parser Agent ecosystem:

```
CV Parser Agent/
├── GNN-Link-Prediction/              ← This system
├── Advanced-Recommendation-System/    (FastAPI backend)
├── Skill-Cooccurrence-PMI/           (PMI graph)
├── Skill-Category-Loader/            (Taxonomy)
└── ... (other components)
```

**Integration:** GNN can be used as alternative to existing recommendation logic in FastAPI system.

---

## Contact & Support

**Documentation Issues:** Update relevant .md file  
**Bug Reports:** Check logs in `output/gnn_linkpred.log`  
**Feature Requests:** Discuss with ML team  
**Performance Issues:** See TESTING_GUIDE.md troubleshooting section  

---

**Last Updated:** January 2026  
**Version:** 1.0  
**Status:** Production-Ready ✅
