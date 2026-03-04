# GNN Link Prediction - Full Pipeline Runner
# Run this script to execute the complete pipeline

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "GNN LINK PREDICTION - FULL PIPELINE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not detected. Activating..." -ForegroundColor Yellow
    & "F:\CV Parser Agent\.venv\Scripts\Activate.ps1"
}

# Change to project directory
Set-Location "F:\CV Parser Agent\GNN-Link-Prediction"

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Step 1: Export Neo4j data
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "STEP 1/3: Export Neo4j → PyTorch Geometric HeteroData" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host ""

python scripts/export_neo4j_to_pyg_lp.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Export failed! Check logs and Neo4j connection." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Export completed successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Evaluate baselines
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "STEP 2/3: Evaluate Baselines (Popularity + Embedding Similarity)" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host ""

python scripts/eval_baselines.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Baseline evaluation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Baseline evaluation completed!" -ForegroundColor Green
Write-Host ""

# Step 3: Train GNN
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "STEP 3/3: Train GNN + Final Evaluation" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host ""

python scripts/train_linkpred_gnn.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ GNN training failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ GNN training completed!" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "PIPELINE COMPLETE!" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Results available in:" -ForegroundColor Green
Write-Host "  - output/final_comparison.csv    (Comparison table)" -ForegroundColor White
Write-Host "  - output/final_report.json       (GO/NO-GO decision)" -ForegroundColor White
Write-Host "  - output/gnn_linkpred.log        (Detailed logs)" -ForegroundColor White
Write-Host "  - models/best_gnn_linkpred.pt    (Trained model)" -ForegroundColor White
Write-Host ""

# Display final report
if (Test-Path "output/final_report.json") {
    Write-Host "📋 Final Report:" -ForegroundColor Yellow
    Write-Host ""
    $report = Get-Content "output/final_report.json" | ConvertFrom-Json
    
    if ($report.decision -eq "GO") {
        Write-Host "🟢 DECISION: GO - GNN is production-ready!" -ForegroundColor Green
    } else {
        Write-Host "🔴 DECISION: NO-GO - GNN needs improvement" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Check Passed:" -ForegroundColor Cyan
    $report.checks.PSObject.Properties | ForEach-Object {
        $checkName = $_.Name
        $checkValue = $_.Value
        $status = if ($checkValue) { "✓" } else { "✗" }
        $color = if ($checkValue) { "Green" } else { "Red" }
        Write-Host "  $status $checkName" -ForegroundColor $color
    }
    
    Write-Host ""
    Write-Host "Overfit Test: " -NoNewline
    if ($report.overfit_test_passed) {
        Write-Host "✓ PASSED" -ForegroundColor Green
    } else {
        Write-Host "✗ FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review results in output/" -ForegroundColor White
Write-Host "  2. Check detailed logs: output/gnn_linkpred.log" -ForegroundColor White
Write-Host "  3. If NO-GO, tune hyperparameters in config.py" -ForegroundColor White
Write-Host "  4. If GO, integrate model into production system" -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
