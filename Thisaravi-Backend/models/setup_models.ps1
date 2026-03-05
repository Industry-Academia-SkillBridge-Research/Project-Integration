Write-Host "--- Student Advisor Model Setup ---"

# Settings
$baseDir = "models"
$repoV1 = "Hashinika/gemma-3-4b-student-advisor-v1-GGUF"
$repoV2 = "Hashinika/gemma-3-4b-student-advisor-v2-GGUF"
$ggufFile = "gemma-3-4b-pt.Q4_K_M.gguf"

# Function to setup a specific model
function Setup-Model {
    param (
        [string]$version,
        [string]$repoId
    )

    $targetDir = Join-Path $baseDir $version
    $targetFile = Join-Path $targetDir $ggufFile
    $ollamaName = "student-advisor:$version"

    Write-Host "-----------------------------------"
    Write-Host "Processing: $ollamaName"
    Write-Host "-----------------------------------"

    # 1. Create directory
    if (-not (Test-Path -Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir | Out-Null
    }

    # 2. Download if missing
    if (-not (Test-Path -Path $targetFile)) {
        Write-Host "⬇️  Downloading $ggufFile from $repoId..."
        try {
            # Use Python to download directly to avoid CLI path issues
            $pyCode = "import sys; from huggingface_hub import hf_hub_download; hf_hub_download(repo_id=sys.argv[1], filename=sys.argv[2], local_dir=sys.argv[3], local_dir_use_symlinks=False)"
            python -c $pyCode $repoId $ggufFile $targetDir
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Failed to download $version. Skipping..." -ForegroundColor Red
                return
            }
        }
        catch {
            Write-Host "❌ Failed to execute python download. Ensure your virtual environment is active." -ForegroundColor Red
            return
        }
    } else {
        Write-Host "✅ Model file exists locally." -ForegroundColor Green
    }

    # 3. Create Modelfile
    Write-Host "Creating Modelfile for $version..."
    $modelFileContent = @"
FROM ./$ggufFile
TEMPLATE """<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
{{ .Response }}<end_of_turn>"""
PARAMETER stop "<end_of_turn>"
"@
    Set-Content -Path (Join-Path $targetDir "Modelfile") -Value $modelFileContent -Encoding UTF8

    # 4. Ollama Create
    Write-Host "Registering with Ollama as '$ollamaName'..."
    ollama create $ollamaName -f (Join-Path $targetDir "Modelfile")

    Write-Host "✅ Success: $ollamaName is ready." -ForegroundColor Green
}

# Main Logic
$chosen = $args[0]

if (-not $chosen) {
    Write-Host ""
    Write-Host "Select a model to download and register:"
    Write-Host "  [1] v1 - gemma-3-4b-student-advisor-v1 (text output)"
    Write-Host "  [2] v2 - gemma-3-4b-student-advisor-v2 (JSON output)"
    Write-Host "  [3] all - Download and register both models"
    Write-Host ""
    $selection = Read-Host "Enter your choice (1/2/3)"

    switch ($selection) {
        "1" { $chosen = "v1" }
        "2" { $chosen = "v2" }
        "3" { $chosen = "all" }
        Default {
            Write-Host "❌ Invalid selection. Exiting." -ForegroundColor Red
            exit 1
        }
    }
}

switch ($chosen) {
    "v1" { Setup-Model "v1-text" $repoV1 }
    "v2" { Setup-Model "v2-json" $repoV2 }
    { $_ -eq "all" } {
        Setup-Model "v1-text" $repoV1
        Setup-Model "v2-json" $repoV2
    }
    Default {
        Write-Host "Usage: ./setup_model.ps1 [v1|v2|all]"
        exit 1
    }
}

Write-Host "-----------------------------------"
Write-Host "All requested setups complete!"
Write-Host "Check your models using: ollama list"
