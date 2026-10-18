# Requires the pinned ffmpeg verify-and-throw to be a top-level pair in the
# check-all-windows step body. PowerShell's parser is the allowlist.
# Linux does not run this file. #861 exact-matches that step body once it lands.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ThrowLine = 'if ($LASTEXITCODE -ne 0) { throw "ffmpeg zip sha256 mismatch: $expected" }'
$VerifyArg = 'scripts/verify_ffmpeg_zip_sha256.py'
$ThrowText = '"ffmpeg zip sha256 mismatch: $expected"'

function Count-Nodes($nodes) {
    if ($null -eq $nodes) { return 0 }
    $count = 0
    foreach ($node in @($nodes)) {
        if ($null -ne $node) { $count++ }
    }
    return $count
}

function Test-HasJump($stmt) {
    if ($null -eq $stmt) { return $false }
    if (
        $stmt -is [System.Management.Automation.Language.BreakStatementAst] -or
        $stmt -is [System.Management.Automation.Language.ContinueStatementAst] -or
        $stmt -is [System.Management.Automation.Language.ExitStatementAst] -or
        $stmt -is [System.Management.Automation.Language.ReturnStatementAst]
    ) {
        return $true
    }
    $hits = $stmt.FindAll({
        $args[0] -is [System.Management.Automation.Language.BreakStatementAst] -or
        $args[0] -is [System.Management.Automation.Language.ContinueStatementAst] -or
        $args[0] -is [System.Management.Automation.Language.ExitStatementAst] -or
        $args[0] -is [System.Management.Automation.Language.ReturnStatementAst]
    }, $true)
    return (Count-Nodes $hits) -gt 0
}

function Test-VerifyCommand($stmt) {
    if ($stmt -isnot [System.Management.Automation.Language.PipelineAst]) { return $false }
    if ($stmt.PipelineElements.Count -ne 1) { return $false }
    $cmd = $stmt.PipelineElements[0]
    if ($cmd -isnot [System.Management.Automation.Language.CommandAst]) { return $false }
    if ($cmd.Redirections.Count -gt 0) { return $false }
    if ($cmd.GetCommandName() -ne 'python') { return $false }
    foreach ($element in $cmd.CommandElements) {
        if ($element.Extent.Text -eq $script:VerifyArg) { return $true }
    }
    return $false
}

function Test-HashIf($stmt) {
    if ($stmt -isnot [System.Management.Automation.Language.IfStatementAst]) { return $false }
    if ($stmt.Clauses.Count -ne 1) { return $false }
    if ($null -ne $stmt.ElseClause) { return $false }
    $clause = $stmt.Clauses[0]
    $cond = $clause.Item1
    $body = $clause.Item2
    if ($cond -isnot [System.Management.Automation.Language.PipelineAst]) { return $false }
    if ($cond.PipelineElements.Count -ne 1) { return $false }
    $exprCmd = $cond.PipelineElements[0]
    if ($exprCmd -isnot [System.Management.Automation.Language.CommandExpressionAst]) { return $false }
    if ($exprCmd.Redirections.Count -gt 0) { return $false }
    $expr = $exprCmd.Expression
    if ($expr -isnot [System.Management.Automation.Language.BinaryExpressionAst]) { return $false }
    if ($expr.Operator -ne [System.Management.Automation.Language.TokenKind]::Ine) { return $false }
    if ($expr.Left -isnot [System.Management.Automation.Language.VariableExpressionAst]) { return $false }
    if ($expr.Left.VariablePath.UserPath -ne 'LASTEXITCODE') { return $false }
    $right = $expr.Right
    if ($right -isnot [System.Management.Automation.Language.ConstantExpressionAst]) { return $false }
    if ($null -eq $right.Value -or $right.Value -is [string] -or $right.Value -ne 0) { return $false }
    if ($body.Statements.Count -ne 1) { return $false }
    $throw = $body.Statements[0]
    if ($throw -isnot [System.Management.Automation.Language.ThrowStatementAst]) { return $false }
    if ($null -eq $throw.Pipeline) { return $false }
    if ($throw.Pipeline.Extent.Text -ne $script:ThrowText) { return $false }
    return $true
}

function Test-HashGate([string]$Source) {
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($Source, [ref]$tokens, [ref]$errors)
    if ($null -eq $ast -or (Count-Nodes $errors) -gt 0) { return 'parse-error' }
    if ($null -ne $ast.ParamBlock) { return 'param-block' }
    if ((Count-Nodes $ast.UsingStatements) -gt 0) { return 'using' }
    foreach ($block in @($ast.BeginBlock, $ast.ProcessBlock)) {
        if ($null -ne $block -and $null -ne $block.Statements -and $block.Statements.Count -gt 0) {
            return 'side-block'
        }
    }
    if ($null -eq $ast.EndBlock -or $null -eq $ast.EndBlock.Statements) { return 'no-endblock' }
    $traps = $ast.FindAll({
        $args[0] -is [System.Management.Automation.Language.TrapStatementAst]
    }, $true)
    if ((Count-Nodes $traps) -gt 0) { return 'trap' }

    $hashIfs = $ast.FindAll({
        $args[0] -is [System.Management.Automation.Language.IfStatementAst]
    }, $true)
    $nested = 0
    foreach ($node in @($hashIfs)) {
        if ($null -eq $node) { continue }
        if (-not (Test-HashIf $node)) { continue }
        if ($node.Parent -ne $ast.EndBlock) { $nested++ }
    }
    if ($nested -gt 0) { return 'nested' }

    $statements = @($ast.EndBlock.Statements)
    $verifyAt = -1
    $hashAt = -1
    for ($i = 0; $i -lt $statements.Count; $i++) {
        $stmt = $statements[$i]
        if ($null -eq $stmt) { return 'parse-error' }
        if ($stmt.Parent -ne $ast.EndBlock) { return 'nested' }
        if (Test-VerifyCommand $stmt) {
            if ($verifyAt -ge 0) { return 'duplicate-verify' }
            $verifyAt = $i
        }
        if (Test-HashIf $stmt) {
            if ($hashAt -ge 0) { return 'duplicate-throw' }
            $hashAt = $i
        }
    }
    if ($verifyAt -lt 0 -or $hashAt -lt 0) { return 'missing-pair' }
    for ($i = 0; $i -lt $hashAt; $i++) {
        if (Test-HasJump $statements[$i]) { return 'jump-before' }
    }
    if ($hashAt -ne ($verifyAt + 1)) { return 'not-adjacent' }
    return $null
}

function Get-FfmpegStepScript([string]$Workflow) {
    $text = $Workflow -replace "`r`n", "`n" -replace "`r", "`n"
    $lines = $text.Split("`n")
    $stepName = 'Install hashed sensor lock and pinned ffmpeg'
    $start = -1
    $hits = 0
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*- name:\s+(.+?)\s*$' -and $Matches[1] -eq $stepName) {
            $hits++
            $start = $i
        }
    }
    if ($hits -ne 1) { throw "FAIL ffmpeg step count=$hits" }
    $runAt = -1
    $runIndent = -1
    for ($i = $start + 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*- (name|uses):') { break }
        if ($lines[$i] -match '^(\s*)run:\s*\|\s*$') {
            $runAt = $i
            $runIndent = $Matches[1].Length
            break
        }
    }
    if ($runAt -lt 0) { throw 'FAIL ffmpeg step has no run block' }
    $body = New-Object System.Collections.Generic.List[string]
    for ($i = $runAt + 1; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line.Length -eq 0 -or $line.Trim().Length -eq 0) {
            $body.Add('')
            continue
        }
        if ($line -notmatch '^(\s*)\S') { throw 'FAIL ffmpeg step indent' }
        $indent = $Matches[1].Length
        if ($indent -le $runIndent) { break }
        $body.Add($line)
    }
    while ($body.Count -gt 0 -and $body[$body.Count - 1] -eq '') {
        $body.RemoveAt($body.Count - 1)
    }
    if ($body.Count -eq 0) { throw 'FAIL ffmpeg step body is empty' }
    $min = [int]::MaxValue
    foreach ($line in $body) {
        if ($line -eq '') { continue }
        if ($line -notmatch '^(\s*)\S') { throw 'FAIL ffmpeg step indent' }
        if ($Matches[1].Length -lt $min) { $min = $Matches[1].Length }
    }
    $dedented = New-Object System.Collections.Generic.List[string]
    foreach ($line in $body) {
        if ($line -eq '') {
            $dedented.Add('')
            continue
        }
        if (-not $line.StartsWith(' ' * $min)) { throw 'FAIL ffmpeg step indent' }
        $dedented.Add($line.Substring($min))
    }
    return (($dedented -join "`n") + "`n")
}

if (-not $PSScriptRoot) { throw 'FAIL parser script requires -File' }
$repo = Split-Path -Parent $PSScriptRoot
$workflowPath = Join-Path $repo '.github/workflows/check-all.yml'
if (-not (Test-Path -LiteralPath $workflowPath)) { throw "FAIL missing $workflowPath" }
$workflow = [System.IO.File]::ReadAllText($workflowPath)
$script = Get-FfmpegStepScript $workflow
$liveCount = ([regex]::Matches($script, [regex]::Escape($ThrowLine))).Count
if ($liveCount -ne 1) { throw "FAIL throw line count=$liveCount" }

$liveReason = Test-HashGate $script
if ($null -ne $liveReason) { throw "FAIL ffmpeg hash gate live script was refused: $liveReason" }

$nl = "`n"
$mutants = [ordered]@{
    'if-zero'         = 'if (0) { ' + $ThrowLine + ' }'
    'if-null'         = 'if ($null) { ' + $ThrowLine + ' }'
    'if-not'          = 'if (-not $true) { ' + $ThrowLine + ' }'
    'if-bang'         = 'if (!$true) { ' + $ThrowLine + ' }'
    'if-parens'       = 'if (($false)) { ' + $ThrowLine + ' }'
    'if-var'          = '$f = $false; if ($f) { ' + $ThrowLine + ' }'
    'if-backtick'     = 'if ($false) `' + $nl + '{ ' + $ThrowLine + ' }'
    'while-false'     = 'while ($false) { ' + $ThrowLine + ' }'
    'function-never'  = 'function Never { ' + $ThrowLine + ' }'
    'scriptblock'     = '$sb = { ' + $ThrowLine + ' }'
    'else-branch'     = 'if ($true) {} else { ' + $ThrowLine + ' }'
    'try-catch'       = 'try { ' + $ThrowLine + ' } catch { }'
    'trap'            = 'trap { continue }; ' + $ThrowLine
    'break-before'    = 'break' + $nl + $ThrowLine
    'midword-hash'    = 'Write-Host a#b; exit 0' + $nl + $ThrowLine
}
if ($mutants.Count -ne 15) { throw "FAIL mutant count $($mutants.Count)" }

foreach ($name in $mutants.Keys) {
    $mutated = $script.Replace($ThrowLine, [string]$mutants[$name])
    if ($mutated -eq $script) { throw "FAIL mutant did not replace the throw line: $name" }
    $reason = Test-HashGate $mutated
    if ($null -eq $reason) { throw "hidden ffmpeg hash gate was allowed: $name" }
    Write-Output "REFUSE $name reason=$reason"
}

Write-Output 'OK ffmpeg-hash-gate-parser live=pass mutants=15'
