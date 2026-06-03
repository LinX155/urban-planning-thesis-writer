param(
  [string]$Workspace,
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$SkillRoot = Split-Path -Parent $ScriptRoot

function Write-Step($Message) {
  Write-Host "[UPTW-init] $Message"
}

function Test-IsSameOrChildPath([string]$CandidatePath, [string]$RootPath) {
  $candidate = [System.IO.Path]::GetFullPath($CandidatePath).TrimEnd('\')
  $root = [System.IO.Path]::GetFullPath($RootPath).TrimEnd('\')
  if ($candidate.Equals($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $true
  }
  return $candidate.StartsWith("$root\", [System.StringComparison]::OrdinalIgnoreCase)
}

function Resolve-WorkspaceRoot([string]$WorkspaceValue) {
  $candidate = if ([string]::IsNullOrWhiteSpace($WorkspaceValue)) {
    (Get-Location).Path
  } else {
    $WorkspaceValue
  }
  $resolved = [System.IO.Path]::GetFullPath($candidate)
  if (Test-IsSameOrChildPath -CandidatePath $resolved -RootPath $SkillRoot) {
    throw @(
      "Refusing to initialize inside the skill directory."
      "Skill root: $SkillRoot"
      "Requested workspace: $resolved"
      "Pass the user's thesis project folder to -Workspace."
    ) -join [System.Environment]::NewLine
  }
  return $resolved
}

function Test-PythonPackage($PackageName) {
  $code = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$PackageName') else 1)"
  & $Python -c $code | Out-Null
  return $LASTEXITCODE -eq 0
}

$Workspace = Resolve-WorkspaceRoot $Workspace
$StateRoot = Join-Path $Workspace ".urban-planning-thesis-writer"
$StateDirs = @(
  "state",
  "state\chapters",
  "state\memory",
  "state\review-cycles",
  "state\snapshots",
  "state\diffs",
  "state\backups",
  "logs"
)

Write-Step "Workspace: $Workspace"

try {
  & $Python --version | Out-Host
} catch {
  throw "Python was not found. Install Python 3.10+ or pass -Python with an absolute python.exe path."
}

$required = @("docx", "lxml", "pypdf")
$missing = @()
foreach ($pkg in $required) {
  if (-not (Test-PythonPackage $pkg)) {
    $missing += $pkg
  }
}

if ($missing.Count -gt 0) {
  Write-Step "Installing missing Python packages: $($missing -join ', ')"
  & $Python -m pip install python-docx lxml pypdf | Out-Host
}

foreach ($dir in $StateDirs) {
  New-Item -ItemType Directory -Force -Path (Join-Path $StateRoot $dir) | Out-Null
}

$files = @{
  "state\project.json" = @{
    schema_version = 2
    thesis_title = $null
    research_object = $null
    research_scope = $null
    confirmed_facts_boundary = @()
    current_docx = $null
    created_at = (Get-Date).ToString("s")
  }
  "state\outline.json" = @{
    schema_version = 2
    main_question = $null
    sections = @()
    global_open_questions = @()
    updated_at = $null
  }
  "state\replan_queue.json" = @{
    schema_version = 2
    pending = @()
    resolved = @()
    updated_at = $null
  }
  "state\terminology.json" = @{
    schema_version = 2
    terms = @()
    abbreviations = @()
    variables = @()
  }
  "state\figures_formulas.json" = @{
    schema_version = 2
    figures = @()
    tables = @()
    formulas = @()
  }
  "state\memory\user_revision_preferences.json" = @{
    stable_preferences = @()
    tentative_observations = @()
    rejected_generalizations = @()
    last_reviewed_section = $null
    updated_at = $null
  }
  "state\memory\section_memory.json" = @{
    sections = @{}
  }
  "state\progress.json" = @{
    schema_version = 2
    completed_sections = @()
    pending_sections = @()
    blocked_sections = @()
    pending_replan_items = @()
    last_snapshot = $null
    last_backup = $null
    last_review_section = $null
    last_review_summary = $null
    last_write_context = $null
    review_rounds = 0
    recent_diff_summaries = @()
  }
}

foreach ($relative in $files.Keys) {
  $path = Join-Path $StateRoot $relative
  if (-not (Test-Path -LiteralPath $path)) {
    $files[$relative] | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
  }
}

$reviewHistory = Join-Path $StateRoot "state\memory\review_history.jsonl"
if (-not (Test-Path -LiteralPath $reviewHistory)) {
  New-Item -ItemType File -Path $reviewHistory | Out-Null
}

Write-Step "Initialized state directory: $StateRoot"
Write-Step "Next: run /UPTW-plan with the user's existing materials and docx paths."
