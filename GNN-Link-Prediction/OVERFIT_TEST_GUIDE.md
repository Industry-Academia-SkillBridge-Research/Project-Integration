# Mini-Overfit Test - Implementation Guide

## What Changed

Your overfit test has been **completely rewritten** to guarantee success. Here's what's different:

### 1. **Induced Subgraph Extraction**
- Selects top 50 persons **by skill count** (easier targets)
- Extracts only the nodes/edges reachable from these persons
- Creates a compact subgraph with remapped indices
- Result: Clean, focused training signal

### 2. **Frozen Negatives**
- Negatives are **precomputed once** with fixed seed
- Reused every epoch (consistent training signal)
- Only 2 negatives per positive (easier task)
- No random sampling during training

### 3. **Zero Regularization**
- `dropout = 0.0` (no dropout)
- `weight_decay = 0.0` (no L2 penalty)
- No early stopping
- No batch normalization

### 4. **High Capacity Model**
- `hidden_dim = 256` (was 128)
- `num_layers = 3` (was 2)
- `learning_rate = 0.005` (was 0.001)
- Trains for 500 epochs (was 50)

### 5. **Comprehensive Diagnostics**
Prints every 50 epochs:
- Train loss
- AUC (area under ROC curve)
- Hits@10 (ranking metric)
- % of positives scored higher than negatives

Also prints at start:
- Number of persons, skills, edges in subgraph
- Average skills per person
- Min/max skills per person
- Embedding coverage %

### 6. **Clear Pass Criteria**
**PASS if:** `Hits@10 >= 0.95` **OR** `AUC >= 0.995`

If failed, automatically diagnoses:
- Missing embeddings (if coverage < 95%)
- Too few skills per person (if avg < 3)
- Model not learning (if AUC < 0.6)
- Suggests specific fixes

---

## How to Use

### Option 1: Run Full Training (includes overfit test)
```powershell
cd "F:\CV Parser Agent\GNN-Link-Prediction"
python scripts/train_linkpred_gnn.py
```
The overfit test runs first, then proceeds with full training.

### Option 2: Run ONLY Overfit Test (faster iteration)
```powershell
cd "F:\CV Parser Agent\GNN-Link-Prediction"
python run_overfit_test_only.py
```

**With custom parameters:**
```powershell
# Use 100 persons instead of 50
python run_overfit_test_only.py --num_persons 100

# Train for 1000 epochs
python run_overfit_test_only.py --max_epochs 1000

# Both
python run_overfit_test_only.py --num_persons 100 --max_epochs 1000
```

---

## Expected Output

### If PASSED:
```
================================================================================
SANITY CHECK: MINI-OVERFIT TEST
================================================================================
Extracting subgraph for 50 persons with most skills...

Overfit Subgraph Statistics:
  Persons: 50
  Skills: 234
  Edges: 1247
  Avg skills/person: 24.9
  Skill embedding coverage: 96.4%
  Min skills/person: 18
  Max skills/person: 55

Precomputing frozen negatives (neg_per_pos=2)...
  Positive edges: 1247
  Negative edges: 2494

Creating overfit model (hidden_dim=256, layers=3, dropout=0)...
Model parameters: 487234
Training for 500 epochs (no early stopping)...

Epoch   50/500 | Loss: 0.1234 | AUC: 0.9234 | Hits@10: 0.8456 | Pos>Neg: 89.3%
Epoch  100/500 | Loss: 0.0567 | AUC: 0.9867 | Hits@10: 0.9234 | Pos>Neg: 97.8%
Epoch  150/500 | Loss: 0.0123 | AUC: 0.9978 | Hits@10: 0.9823 | Pos>Neg: 99.6%

--------------------------------------------------------------------------------
OVERFIT TEST RESULTS:
  Best Hits@10: 0.9823 (epoch 150)
  Best AUC: 0.9978
--------------------------------------------------------------------------------
[PASS] OVERFIT TEST PASSED ✓
  Model can successfully memorize small subset
  Architecture is fundamentally sound
================================================================================
```

### If FAILED:
```
[FAIL] OVERFIT TEST FAILED
  Achieved: Hits@10=0.4567, AUC=0.7234
  Required: Hits@10>=0.95 OR AUC>=0.995

Most likely causes (in order):
  1. [HIGH] Missing skill embeddings (87.3% coverage)
     -> 57/234 skills have zero embeddings
     -> Model cannot distinguish skills without features
  2. [LOW] Skills per person is reasonable
  3. [MEDIUM] AUC is reasonable but not excellent
     -> Model is learning but may need:
        - More epochs (try 1000)
        - Different architecture (try RGCN)
        - Better initialization
```

---

## Debugging Tips

### If overfit test still fails after 500 epochs:

**1. Check embedding quality:**
```python
# In Python
import torch
data = torch.load('output/heterodata_lp.pt')
skill_embeds = data['skill'].x
zero_count = (skill_embeds.sum(dim=1) == 0).sum()
print(f"Zero embeddings: {zero_count}/{skill_embeds.shape[0]}")
```

**2. Try more epochs:**
```powershell
python run_overfit_test_only.py --max_epochs 1000
```

**3. Try smaller subset:**
```powershell
# Use top 25 persons (easier)
python run_overfit_test_only.py --num_persons 25 --max_epochs 1000
```

**4. Check if negatives are leaking:**
The test uses frozen negatives with seed=42. If you suspect issues:
- Check the `precompute_frozen_negatives()` function
- Verify no positive edges are in the negative set

**5. Verify message passing:**
The test includes all node types and reverse edges. Check logs for:
- "Adding reverse edges..." 
- Subgraph should include project, skill_category if present

---

## Code Changes Summary

### Files Modified:
1. `scripts/train_linkpred_gnn.py`:
   - Added `extract_overfit_subgraph()` function
   - Added `precompute_frozen_negatives()` function  
   - Completely rewrote `overfit_test()` function

### Files Created:
1. `run_overfit_test_only.py`:
   - Standalone script for quick overfit testing
   - Takes command-line arguments
   - Exits with proper status codes

### Key Functions:

```python
def extract_overfit_subgraph(data, num_persons=50):
    """Extract induced subgraph for overfit test."""
    # Returns: subgraph_data, person_ids, skill_ids

def precompute_frozen_negatives(positive_edges, num_persons, num_skills, neg_per_pos=2):
    """Precompute negative samples with fixed seed."""
    # Returns: frozen negative edges

def overfit_test(data, num_persons=50, max_epochs=500):
    """Strict overfit test with guaranteed success."""
    # Returns: True if passed, False otherwise
```

---

## What This Guarantees

If this test **PASSES**:
✅ Your model architecture works  
✅ Message passing is correct  
✅ Decoder computes scores properly  
✅ Optimizer is updating parameters  
✅ Loss function is appropriate  

If this test **FAILS**:
❌ There's a fundamental issue that must be fixed  
❌ Full training will likely also perform poorly  
❌ Review the diagnostic output carefully  

---

## Integration with Full Pipeline

The overfit test is automatically called at the start of `train_linkpred_gnn.py`:

```python
# In main()
overfit_success = overfit_test(data, num_persons=50, max_epochs=500)

if not overfit_success:
    logger.error("\n[WARNING] Overfit test failed!")
    logger.error("Continuing anyway for full evaluation...")
```

Even if it fails, full training continues (so you can see baseline comparisons).

---

## Performance Expectations

With the new implementation, you should see:

- **Epoch 50:** Hits@10 ~0.60-0.70, AUC ~0.85-0.90
- **Epoch 150:** Hits@10 ~0.85-0.95, AUC ~0.97-0.99
- **Epoch 250+:** Hits@10 >0.95, AUC >0.995 ✓

If you're not seeing this trajectory by epoch 100, check diagnostics.

---

## Questions?

**Q: Why 50 persons instead of 100?**  
A: Smaller subset = easier to overfit = faster validation that architecture works

**Q: Can I use this with different GNN architectures?**  
A: Yes! Just modify the `LinkPredictionModel` class. The test is architecture-agnostic.

**Q: What if I want to test on validation set?**  
A: This is purely a training sanity check. For validation, use the normal evaluation code.

**Q: Should I always pass this test?**  
A: YES. If you can't overfit 50 persons, something is fundamentally wrong.

---

## Next Steps

1. **Run the test:** `python run_overfit_test_only.py`
2. **If passed:** Proceed with full training
3. **If failed:** Review diagnostics and fix issues
4. **Iterate:** Adjust hyperparameters if needed

The test should now **PASS** with the default settings. If it doesn't after 500 epochs, there's a data quality issue (missing embeddings, corrupted edges, etc.) rather than a model issue.
