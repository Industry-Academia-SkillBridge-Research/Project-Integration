# 🧪 Testing & Validation Guide

## Pre-Flight Validation

**Before running the full pipeline, validate your setup:**

```powershell
cd "F:\CV Parser Agent\GNN-Link-Prediction"
python validate_setup.py
```

This checks:
- ✅ Python dependencies installed
- ✅ Neo4j connection working
- ✅ Required data exists (Person, Skill, HAS_SKILL)
- ✅ Skill embeddings present
- ✅ Output directories created

**Expected output:**
```
✓ PRE-FLIGHT VALIDATION PASSED
System is ready! Run the pipeline...
```

---

## Step-by-Step Testing

### Test 1: Export Neo4j Data

```powershell
python scripts/export_neo4j_to_pyg_lp.py
```

**Success indicators:**
```
✓ Found 1250 Person nodes
✓ Found 1578 Skill nodes
✓ Skills with missing embeddings: 78/1578 (4.9%)
✓ Exported 8542 edges for ('person', 'has_skill', 'skill')
✓ All outputs saved successfully!
```

**Check outputs:**
```powershell
# Should exist and be non-empty
ls output/heterodata_lp.pt      # ~10-50 MB
ls output/id_maps.json           # Node ID mappings
ls output/dataset_stats.json     # Statistics
```

**Review statistics:**
```powershell
Get-Content output/dataset_stats.json | ConvertFrom-Json | ConvertTo-Json
```

**Key metrics to check:**
- `skill_embedding_coverage` > 0.80 (80%+ skills have embeddings)
- `num_has_skill_edges` > 1000 (sufficient training data)

---

### Test 2: Baseline Evaluation

```powershell
python scripts/eval_baselines.py
```

**Success indicators:**
```
Popularity Baseline Results:
  hits@5: 0.0820
  hits@10: 0.1050
  mrr: 0.0680
  auc: 0.6120

Embedding Similarity Baseline Results:
  hits@5: 0.1240
  hits@10: 0.1650
  mrr: 0.0920
  auc: 0.7010
```

**Check outputs:**
```powershell
Get-Content output/baseline_results.json | ConvertFrom-Json | ConvertTo-Json
```

**Expected behavior:**
- Embedding Similarity > Popularity (embeddings are useful)
- Hits@10 in range 0.08-0.20 (reasonable baseline)
- Should complete in 2-5 minutes

---

### Test 3: GNN Training (Full)

```powershell
python scripts/train_linkpred_gnn.py
```

**Success indicators:**

**Phase 1: Overfit Test**
```
SANITY CHECK: OVERFIT TEST
Testing if model can overfit 100 train persons...
Epoch 50/50 | Loss: 0.0234 | Train Hits@10: 0.9567
✓ OVERFIT TEST PASSED: Achieved Hits@10 = 0.9567 >= 0.90
  → Model architecture is capable of learning
```

**Phase 2: Training**
```
TRAINING GNN
Train: 6833 pos, 34165 neg
Val: 854 pos, 4270 neg

Epoch 1/100 | Loss: 0.6234 | Val Hits@10: 0.1234 | Val MRR: 0.0856
Epoch 5/100 | Loss: 0.4123 | Val Hits@10: 0.1856 | Val MRR: 0.1023
...
Epoch 35/100 | Loss: 0.2145 | Val Hits@10: 0.2341 | Val MRR: 0.1456

Early stopping at epoch 45
Best val_hits@10: 0.2412 at epoch 35
```

**Phase 3: Evaluation**
```
FINAL EVALUATION ON TEST SET
GNN Test Results:
  hits@5: 0.1580
  hits@10: 0.2140
  hits@20: 0.3120
  mrr: 0.1180
  auc: 0.7480
```

**Phase 4: GO/NO-GO**
```
GO / NO-GO DECISION
1. GNN Hits@10 (0.2140) > Popularity Hits@10 (0.1050): ✓ PASS
2. GNN MRR (0.1180) > Popularity MRR (0.0680): ✓ PASS
3. GNN Hits@10 (0.2140) > Embedding Hits@10 (0.1650): ✓ PASS
4. GNN Hits@10 (0.2140) >= 0.10: ✓ PASS
5. GNN MRR (0.1180) >= 0.05: ✓ PASS

🟢 GO: GNN is production-ready!
   → GNN significantly outperforms baselines
   → Suitable for deployment
```

**Check outputs:**
```powershell
# Final comparison
Get-Content output/final_comparison.csv

# GO/NO-GO decision
Get-Content output/final_report.json | ConvertFrom-Json | ConvertTo-Json

# Trained model
ls models/best_gnn_linkpred.pt  # Should be ~1-10 MB
```

**Expected timing:**
- Overfit test: 2-5 minutes
- Full training: 10-30 minutes (depends on data size and hardware)
- With GPU: 2-5 minutes

---

## Full Pipeline Test

**Run everything at once:**

```powershell
.\run_pipeline.ps1
```

**Expected output:**
```
================================================================================
STEP 1/3: Export Neo4j → PyTorch Geometric HeteroData
================================================================================
[... export logs ...]
✓ Export completed successfully!

================================================================================
STEP 2/3: Evaluate Baselines (Popularity + Embedding Similarity)
================================================================================
[... baseline logs ...]
✓ Baseline evaluation completed!

================================================================================
STEP 3/3: Train GNN + Final Evaluation
================================================================================
[... training logs ...]
✓ GNN training completed!

================================================================================
PIPELINE COMPLETE!
================================================================================
📊 Results available in:
  - output/final_comparison.csv    (Comparison table)
  - output/final_report.json       (GO/NO-GO decision)
  - output/gnn_linkpred.log        (Detailed logs)
  - models/best_gnn_linkpred.pt    (Trained model)

📋 Final Report:
🟢 DECISION: GO - GNN is production-ready!

Check Passed:
  ✓ gnn_beats_popularity_hits10
  ✓ gnn_beats_popularity_mrr
  ✓ gnn_beats_embedding_hits10
  ✓ min_gnn_hits10
  ✓ min_gnn_mrr

Overfit Test: ✓ PASSED
```

---

## Interpreting Results

### Good Results (GO)
```json
{
  "decision": "GO",
  "gnn_results": {
    "hits@10": 0.214,    // 21.4% of true skills in top-10
    "mrr": 0.118,        // Avg rank ~8 for first true skill
    "auc": 0.748         // 74.8% classification accuracy
  },
  "baseline_results": {
    "popularity": {"hits@10": 0.105},
    "embedding_similarity": {"hits@10": 0.165}
  }
}
```

**Interpretation:**
- GNN is 2x better than popularity baseline
- GNN beats embedding similarity by 30%
- Production-ready!

### Marginal Results (GO but needs monitoring)
```json
{
  "decision": "GO",
  "gnn_results": {
    "hits@10": 0.125,    // Just above threshold
    "mrr": 0.078,
    "auc": 0.695
  }
}
```

**Interpretation:**
- Passes criteria but margins are small
- Deploy with caution
- Plan improvements (more data, better features)

### Poor Results (NO-GO)
```json
{
  "decision": "NO-GO",
  "gnn_results": {
    "hits@10": 0.092,    // Below threshold
    "mrr": 0.048,        // Below threshold
    "auc": 0.632
  },
  "checks": {
    "gnn_beats_popularity_hits10": false,  // FAILED
    "min_gnn_hits10": false                // FAILED
  }
}
```

**Interpretation:**
- GNN doesn't beat baselines sufficiently
- Not ready for production
- Need improvements (see troubleshooting below)

---

## Troubleshooting

### Issue: Overfit Test Fails

**Symptom:**
```
✗ OVERFIT TEST FAILED: Only achieved Hits@10 = 0.45 < 0.90
```

**Possible causes & fixes:**

1. **Learning rate too low**
   ```python
   # In config.py
   LEARNING_RATE = 0.01  # Increase from 0.001
   ```

2. **Model too small**
   ```python
   HIDDEN_DIM = 256  # Increase from 128
   NUM_LAYERS = 3    # Increase from 2
   ```

3. **Features uninformative**
   - Check `dataset_stats.json` for embedding coverage
   - Verify skill embeddings are meaningful (not all zeros)

4. **Bug in model**
   - Review model forward/decode methods
   - Check if gradients are flowing (add debug prints)

---

### Issue: GNN Doesn't Beat Baselines

**Symptom:**
```
GNN Hits@10: 0.108
Embedding Similarity Hits@10: 0.165
Decision: NO-GO
```

**Diagnosis:**

1. **Check data quality**
   ```powershell
   Get-Content output/dataset_stats.json
   ```
   - Look for low `skill_embedding_coverage` (<0.8)
   - Look for low `num_has_skill_edges` (<1000)

2. **Check coverage warnings**
   ```powershell
   Select-String -Path output/gnn_linkpred.log -Pattern "WARNING"
   ```
   - If "30%+ persons have <5 skills" → Weak training signal
   - If "Only 60% embeddings" → Feature quality issue

3. **Try hyperparameter tuning**
   ```python
   # In config.py - Try these combinations:
   
   # Option A: Larger model
   HIDDEN_DIM = 256
   NUM_LAYERS = 3
   
   # Option B: Higher learning rate
   LEARNING_RATE = 0.005
   
   # Option C: More negatives
   NUM_NEGATIVES_PER_POSITIVE = 10
   
   # Option D: Different architecture
   GNN_TYPE = "RGCN"  # Instead of GraphSAGE
   ```

4. **Check training convergence**
   ```powershell
   Select-String -Path output/gnn_linkpred.log -Pattern "Epoch.*Loss"
   ```
   - Loss should decrease steadily
   - If loss stuck → Increase learning rate
   - If loss spikes → Decrease learning rate

---

### Issue: Out of Memory

**Symptom:**
```
RuntimeError: CUDA out of memory
```

**Fixes:**

```python
# In config.py
BATCH_SIZE = 256      # Reduce from 1024
HIDDEN_DIM = 64       # Reduce from 128
NUM_LAYERS = 2        # Keep at 2

# Or switch to CPU
DEVICE = torch.device('cpu')
```

---

### Issue: Training Too Slow

**Symptom:** Training takes >1 hour

**Optimizations:**

1. **Use GPU if available**
   - Check: `nvidia-smi` (should show GPU)
   - Config should auto-detect CUDA

2. **Reduce data size** (for testing)
   ```python
   # In config.py
   TRAIN_RATIO = 0.5  # Use less data temporarily
   VAL_RATIO = 0.1
   TEST_RATIO = 0.1
   ```

3. **Reduce epochs**
   ```python
   MAX_EPOCHS = 50  # Reduce from 100
   ```

---

### Issue: Skill Embeddings Missing

**Symptom:**
```
Skills with missing embeddings: 1200/1578 (76.0%)
⚠️  Only 24.0% of skills have embeddings!
```

**Fixes:**

1. **Run embedding generation first**
   - Check if you have an embedding generation script
   - Run it before this pipeline

2. **Use zero embeddings (fallback)**
   - System already handles this (uses zero vectors)
   - But performance will be degraded

3. **Generate embeddings on-the-fly**
   - Option: Use sentence-transformers to embed skill names
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   embeddings = model.encode(skill_names)
   ```

---

## Performance Benchmarks

### Small Dataset (Test)
```
Persons: 100-500
Skills: 200-500
Edges: 1000-5000

Export: <1 minute
Baselines: 1-2 minutes
Training: 2-5 minutes
Total: ~10 minutes
```

### Medium Dataset (Typical)
```
Persons: 500-2000
Skills: 500-2000
Edges: 5000-20000

Export: 1-3 minutes
Baselines: 3-5 minutes
Training: 10-20 minutes (GPU) / 30-60 min (CPU)
Total: ~30 minutes (GPU)
```

### Large Dataset (Production)
```
Persons: 2000-10000
Skills: 2000-5000
Edges: 20000-100000

Export: 3-10 minutes
Baselines: 10-15 minutes
Training: 20-40 minutes (GPU) / 2-4 hours (CPU)
Total: ~1 hour (GPU)
```

---

## Continuous Testing

### After Data Updates

```powershell
# Re-export data
python scripts/export_neo4j_to_pyg_lp.py

# Check statistics changed
Get-Content output/dataset_stats.json

# Re-train (baselines already cached)
python scripts/train_linkpred_gnn.py
```

### After Code Changes

```powershell
# Validate setup still works
python validate_setup.py

# Run overfit test only (fast sanity check)
# Comment out full training in train_linkpred_gnn.py
# Or modify config temporarily:
MAX_EPOCHS = 1  # Just test one epoch

python scripts/train_linkpred_gnn.py
```

### Regression Testing

```powershell
# Save baseline results
Copy-Item output/gnn_results.json output/gnn_results_baseline.json

# After changes, compare
$old = Get-Content output/gnn_results_baseline.json | ConvertFrom-Json
$new = Get-Content output/gnn_results.json | ConvertFrom-Json

Write-Host "Hits@10: $($old.'hits@10') → $($new.'hits@10')"
Write-Host "MRR: $($old.mrr) → $($new.mrr)"
```

---

## Success Checklist

Before declaring success, verify:

- [ ] Validation script passes
- [ ] Export completes without errors
- [ ] Baselines complete successfully
- [ ] Overfit test **PASSES**
- [ ] Training converges (loss decreases)
- [ ] Validation metrics improve over epochs
- [ ] GNN beats both baselines
- [ ] Hits@10 ≥ 0.10
- [ ] MRR ≥ 0.05
- [ ] Final decision is **GO**
- [ ] All output files created
- [ ] Model checkpoint saved
- [ ] Results reproducible (run twice, same results)

---

## Getting Help

1. **Check logs:**
   ```powershell
   Get-Content output/gnn_linkpred.log
   ```

2. **Check statistics:**
   ```powershell
   Get-Content output/dataset_stats.json | ConvertFrom-Json
   ```

3. **Check Neo4j data:**
   ```cypher
   // In Neo4j browser
   MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
   RETURN count(*) as total_edges
   
   MATCH (s:Skill)
   WHERE s.embedding IS NOT NULL
   RETURN count(s) as skills_with_embeddings
   ```

4. **Review full documentation:**
   - [README.md](README.md) - Complete guide
   - [QUICKSTART.md](QUICKSTART.md) - Quick reference
   - [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Overview

---

**Ready to test?** Start with:
```powershell
python validate_setup.py
```
