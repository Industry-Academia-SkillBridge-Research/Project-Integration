# 🚀 GNN Link Prediction - Quick Reference

## ⚡ Run Full Pipeline (Fastest)

```powershell
cd "F:\CV Parser Agent\GNN-Link-Prediction"
.\run_pipeline.ps1
```

---

## 📋 Step-by-Step Commands

### 1️⃣ Export Neo4j Data
```powershell
python scripts/export_neo4j_to_pyg_lp.py
```
**Output:** `output/heterodata_lp.pt`, `output/id_maps.json`

### 2️⃣ Evaluate Baselines
```powershell
python scripts/eval_baselines.py
```
**Output:** `output/baseline_results.json`

### 3️⃣ Train GNN
```powershell
python scripts/train_linkpred_gnn.py
```
**Output:** `output/gnn_results.json`, `models/best_gnn_linkpred.pt`, `output/final_report.json`

---

## 🔧 Configuration

**File:** [config.py](config.py)

### Must Change:
```python
NEO4J_PASSWORD = "your_password_here"  # Line 12
```

### Common Tuning:
```python
HIDDEN_DIM = 128          # 64, 128, 256
NUM_LAYERS = 2            # 2, 3, 4
LEARNING_RATE = 0.001     # 0.0001, 0.001, 0.01
DROPOUT = 0.3             # 0.1, 0.3, 0.5
```

---

## 📊 Key Outputs

| File | Description |
|------|-------------|
| `output/final_report.json` | **GO/NO-GO decision** |
| `output/final_comparison.csv` | GNN vs Baselines table |
| `output/gnn_linkpred.log` | Complete logs |
| `models/best_gnn_linkpred.pt` | Trained model checkpoint |
| `output/dataset_stats.json` | Data quality metrics |

---

## ✅ Success Criteria

**🟢 GO if:**
- GNN Hits@10 > Popularity Hits@10 ✓
- GNN MRR > Popularity MRR ✓
- GNN Hits@10 ≥ 0.10 ✓
- Overfit test PASSED ✓

**🔴 NO-GO if any fail**

---

## 🧪 Sanity Checks

### Check 1: Overfit Test
- Takes 100 persons, trains to near-perfect accuracy
- ✓ PASS: Model can learn
- ✗ FAIL: Bug or weak architecture

### Check 2: Coverage
- Persons with ≥5 skills: Should be >70%
- Skills with embeddings: Should be >80%

---

## 🐛 Common Issues

### Issue: Import errors
```powershell
pip install torch torch-geometric neo4j numpy pandas scikit-learn tqdm
```

### Issue: Neo4j connection fails
- Check Neo4j is running: `http://localhost:7474`
- Verify password in `config.py`

### Issue: Out of memory
```python
# In config.py
BATCH_SIZE = 512  # Reduce from 1024
HIDDEN_DIM = 64   # Reduce from 128
```

### Issue: Poor performance
1. Check `output/dataset_stats.json` for coverage
2. Increase `HIDDEN_DIM` to 256
3. Try `NUM_LAYERS = 3`
4. Increase `MAX_EPOCHS` to 200

---

## 📈 Expected Performance

| Metric | Popularity | Embedding Sim | GNN (Good) |
|--------|-----------|---------------|-----------|
| Hits@10 | 0.08-0.12 | 0.10-0.18 | **0.15-0.30** |
| MRR | 0.06-0.08 | 0.08-0.12 | **0.10-0.18** |
| AUC | 0.60-0.65 | 0.68-0.75 | **0.72-0.80** |

---

## 🎯 Interpreting Results

### Hits@10 = 0.25
*"25% of a person's actual skills appear in their top-10 recommendations"*

### MRR = 0.12
*"On average, the first correct skill appears at rank ~8"*

### AUC = 0.75
*"Model correctly distinguishes positive/negative pairs 75% of the time"*

---

## 🔄 Iterative Improvement

1. **Run pipeline** → Get baseline results
2. **Check GO/NO-GO** → If NO-GO, proceed:
3. **Analyze logs** → Check coverage, overfit test
4. **Tune hyperparams** → Increase capacity or LR
5. **Re-run training** → Only step 3: `python scripts/train_linkpred_gnn.py`
6. **Repeat** until GO

---

## 📚 Files Overview

```
GNN-Link-Prediction/
├── run_pipeline.ps1           ← Run this!
├── config.py                  ← Configure here
├── requirements.txt           ← Dependencies
├── README.md                  ← Full docs
├── QUICKSTART.md             ← This file
│
├── scripts/
│   ├── export_neo4j_to_pyg_lp.py    [Step 1]
│   ├── eval_baselines.py            [Step 2]
│   └── train_linkpred_gnn.py        [Step 3]
│
├── output/                    ← Results here
└── models/                    ← Trained model here
```

---

## 💡 Pro Tips

1. **First run:** Use default config, establish baseline
2. **Check quality:** Review `dataset_stats.json` before tuning
3. **GPU:** Will auto-use if available (10x faster)
4. **Reproducibility:** Fixed seed=42, results are deterministic
5. **Logging:** All details in `output/gnn_linkpred.log`

---

## 🎓 Research Quality

This implementation is **paper-ready**:
- ✅ Leak-safe evaluation (proper splits)
- ✅ Strong baselines (not random)
- ✅ Multiple metrics (industry standard)
- ✅ Sanity checks (overfit test)
- ✅ Reproducible (fixed seeds)
- ✅ GO/NO-GO (production criteria)

---

## 🆘 Getting Help

1. Check logs: `output/gnn_linkpred.log`
2. Review stats: `output/dataset_stats.json`
3. Read full docs: `README.md`
4. Check Neo4j: Verify data exists with:
   ```cypher
   MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
   RETURN count(*) as num_edges
   ```

---

**Last Updated:** January 2026  
**Ready to run!** 🚀
