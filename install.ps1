$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$HOME\.local\bin;$env:Path"
}
$env:PYTHONPATH = $Repo
$env:PYTHONUTF8 = "1"
& uv run --directory $Repo --no-project --python "3.12" python -m installer @args
exit $LASTEXITCODE
