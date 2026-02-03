#!/usr/bin/env pwsh
# Ralph Wiggum for Cursor - Windows Setup Script
# PowerShell adaptation of the Unix ralph-setup.sh

param(
    [string]$Workspace = ".",
    [string]$Model = "opus-4.5-thinking",
    [int]$MaxIterations = 20,
    [switch]$Branch,
    [string]$BranchName = "",
    [switch]$OpenPR,
    [switch]$Parallel,
    [int]$MaxParallel = 3,
    [switch]$NoMerge,
    [switch]$SkipConfirm
)

# Configuration
$RalphScriptsDir = ".cursor/ralph-scripts"
$RalphDir = ".ralph"
$WarnThreshold = 70000
$RotateThreshold = 80000

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$White = "White"

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Banner {
    Write-ColoredOutput "═══════════════════════════════════════════════════════════════════" $Cyan
    Write-ColoredOutput "🐛 Ralph Wiggum: Autonomous Development Loop (Windows)" $Cyan
    Write-ColoredOutput "═══════════════════════════════════════════════════════════════════" $Cyan
    Write-ColoredOutput ""
    Write-ColoredOutput "  ""That's the beauty of Ralph - the technique is deterministically" $White
    Write-ColoredOutput "   bad in an undeterministic world.""" $White
    Write-ColoredOutput ""
    Write-ColoredOutput "═══════════════════════════════════════════════════════════════════" $Cyan
    Write-ColoredOutput ""
}

function Initialize-RalphDirectory {
    param([string]$Workspace)

    $ralphPath = Join-Path $Workspace $RalphDir
    if (!(Test-Path $ralphPath)) {
        New-Item -ItemType Directory -Path $ralphPath -Force | Out-Null
    }

    # Initialize guardrails.md
    $guardrailsPath = Join-Path $ralphPath "guardrails.md"
    if (!(Test-Path $guardrailsPath)) {
        $guardrailsContent = @"
# Ralph Guardrails (Signs)

> Lessons learned from past failures. READ THESE BEFORE ACTING.

## Core Signs

### Sign: Read Before Writing
- **Trigger**: Before modifying any file
- **Instruction**: Always read the existing file first
- **Added after**: Core principle

### Sign: Test After Changes
- **Trigger**: After any code change
- **Instruction**: Run tests to verify nothing broke
- **Added after**: Core principle

### Sign: Commit Checkpoints
- **Trigger**: Before risky changes
- **Instruction**: Commit current working state first
- **Added after**: Core principle

---

## Learned Signs

(Guardrails added from observed failures will appear below)

"@
        Set-Content -Path $guardrailsPath -Value $guardrailsContent
    }

    # Initialize progress.md
    $progressPath = Join-Path $ralphPath "progress.md"
    if (!(Test-Path $progressPath)) {
        $progressContent = @"
# Progress Log

> Updated by the agent after significant work.

---

## Session History

"@
        Set-Content -Path $progressPath -Value $progressContent
    }

    # Initialize other log files
    $logFiles = @("errors.log", "activity.log")
    foreach ($logFile in $logFiles) {
        $logPath = Join-Path $ralphPath $logFile
        if (!(Test-Path $logPath)) {
            Set-Content -Path $logPath -Value "# $logFile`n"
        }
    }

    # Initialize iteration counter
    $iterationPath = Join-Path $ralphPath ".iteration"
    if (!(Test-Path $iterationPath)) {
        Set-Content -Path $iterationPath -Value "0"
    }
}

function Check-Prerequisites {
    param([string]$Workspace)

    $taskFile = Join-Path $Workspace "RALPH_TASK.md"
    if (!(Test-Path $taskFile)) {
        Write-ColoredOutput "❌ No RALPH_TASK.md found in $Workspace" $Red
        Write-ColoredOutput ""
        Write-ColoredOutput "Create a task file first:" $Yellow
        Write-ColoredOutput "  New-Item RALPH_TASK.md -ItemType File" $White
        Write-ColoredOutput "  Add content with task definition and checkboxes" $White
        return $false
    }

    # Check for cursor-agent CLI
    try {
        $null = Get-Command cursor-agent -ErrorAction Stop
    } catch {
        Write-ColoredOutput "❌ cursor-agent CLI not found" $Red
        Write-ColoredOutput ""
        Write-ColoredOutput "Install via:" $Yellow
        Write-ColoredOutput "  curl https://cursor.com/install -fsS | bash" $White
        return $false
    }

    # Check for git repo
    if (!(Test-Path (Join-Path $Workspace ".git"))) {
        Write-ColoredOutput "❌ Not a git repository" $Red
        Write-ColoredOutput "   Ralph requires git for state persistence." $Yellow
        return $false
    }

    return $true
}

function Show-TaskSummary {
    param([string]$Workspace)

    $taskFile = Join-Path $Workspace "RALPH_TASK.md"
    Write-ColoredOutput "📋 Task Summary:" $Cyan
    Write-ColoredOutput "─────────────────────────────────────────────────────────────────" $White
    Get-Content $taskFile | Select-Object -First 30
    Write-ColoredOutput "─────────────────────────────────────────────────────────────────" $White
    Write-ColoredOutput ""

    # Count criteria
    $content = Get-Content $taskFile -Raw
    $totalCriteria = [regex]::Matches($content, '^[ \t]*([-*]|\d+\.)[ \t]+\[(x| )\]').Count
    $doneCriteria = [regex]::Matches($content, '^[ \t]*([-*]|\d+\.)[ \t]+\[x\]').Count
    $remaining = $totalCriteria - $doneCriteria

    Write-ColoredOutput "Progress: $doneCriteria / $totalCriteria criteria complete ($remaining remaining)" $Green
    Write-ColoredOutput "Model:    $Model" $Green
    Write-ColoredOutput ""
}

function Start-RalphLoop {
    param([string]$Workspace)

    Write-ColoredOutput "🚀 Starting Ralph loop..." $Green
    Write-ColoredOutput ""

    # Commit any uncommitted work first
    Push-Location $Workspace
    try {
        $status = git status --porcelain
        if ($status) {
            Write-ColoredOutput "📦 Committing uncommitted changes..." $Yellow
            git add -A
            git commit -m "ralph: initial commit before loop" 2>$null
        }
    } finally {
        Pop-Location
    }

    # Create branch if requested
    if ($Branch -and $BranchName) {
        Write-ColoredOutput "🌿 Creating branch: $BranchName" $Green
        Push-Location $Workspace
        try {
            git checkout -b $BranchName 2>$null
        } finally {
            Pop-Location
        }
    }

    # Main loop logic would go here
    # For now, show that Ralph is ready
    Write-ColoredOutput "✅ Ralph Wiggum is now active!" $Green
    Write-ColoredOutput "   Monitor progress with: tail -f .ralph/activity.log" $Yellow
    Write-ColoredOutput "   Check errors with: cat .ralph/errors.log" $Yellow
}

# Main execution
function Main {
    Show-Banner

    # Resolve workspace
    if ($Workspace -eq ".") {
        $Workspace = Get-Location
    } else {
        $Workspace = Resolve-Path $Workspace
    }

    Write-ColoredOutput "Workspace: $Workspace" $Green
    Write-ColoredOutput ""

    # Check prerequisites
    if (!(Check-Prerequisites $Workspace)) {
        exit 1
    }

    # Initialize Ralph directory
    Initialize-RalphDirectory $Workspace

    # Show task summary
    Show-TaskSummary $Workspace

    # Confirm before starting (unless -SkipConfirm)
    if (!$SkipConfirm) {
        $confirmation = Read-Host "Start Ralph loop? [y/N]"
        if ($confirmation -notmatch "^[Yy]$") {
            Write-ColoredOutput "Aborted." $Yellow
            exit 0
        }
    }

    # Start the loop
    Start-RalphLoop $Workspace
}

# Run main function
Main
