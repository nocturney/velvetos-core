param(
    [switch]$SkipVoiceStudioInstall
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$HostId = "sderot-windows"
$Repo = Join-Path $env:USERPROFILE "velvetos-core"
$StateDir = Join-Path $env:USERPROFILE ".velvetos"
$SpeechState = Join-Path $StateDir "speech-host.json"
$EdgeState = Join-Path $StateDir "edge-host.json"

function Fail([string]$Message) {
    throw "FAIL $Message"
}

function Resolve-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python --version *> $null
        if ($LASTEXITCODE -eq 0) { return @("python") }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 --version *> $null
        if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
    }
    Fail "Python 3 is required; run scripts/bootstrap-edge-host-windows.ps1 first"
}

function Invoke-Python([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args) {
    if ($script:Python.Count -eq 1) {
        & $script:Python[0] @Args
    } else {
        & $script:Python[0] $script:Python[1] @Args
    }
    if ($LASTEXITCODE -ne 0) { Fail "Python command failed: $($Args -join ' ')" }
}

function Test-SpeechService {
    try {
        $result = Invoke-RestMethod -Uri "http://127.0.0.1:3900/.well-known/voicestudio-speech" -TimeoutSec 3
        return $result
    } catch {
        return $null
    }
}

function Find-VoiceStudioExe {
    $candidates = @()
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "VoiceStudio (Current User)\VoiceStudio.exe")
    }
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "VoiceStudio\VoiceStudio.exe")
    }
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ($programFilesX86) {
        $candidates += (Join-Path $programFilesX86 "VoiceStudio\VoiceStudio.exe")
    }
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Fail "this bootstrap is for the canonical Windows fallback host only"
}
if (-not (Test-Path $Repo)) {
    Fail "repo missing at $Repo; run scripts/bootstrap-edge-host-windows.ps1 first"
}
Set-Location $Repo

$ConfigPath = Join-Path $Repo "packages\vfom\SPEECH-BACKEND.json"
if (-not (Test-Path $ConfigPath)) { Fail "speech backend config missing: $ConfigPath" }
$config = Get-Content -Raw -Encoding UTF8 $ConfigPath | ConvertFrom-Json
$VoiceStudioVersion = [string]$config.provider.version
$TtsModel = [string]$config.defaults.ttsModel
$AsrModel = [string]$config.defaults.asrModelWindows
$MinSimilarity = [double]$config.defaults.qaMinimumSimilarity
$artifact = "VoiceStudio_Current_User_${VoiceStudioVersion}_x64_en-US.msi"
$url = "https://github.com/debpalash/VoiceStudio/releases/download/v$VoiceStudioVersion/$artifact"

Write-Host "=== VelvetOS Windows Speech Fallback ==="
Write-Host "host=$HostId provider=VoiceStudio/$VoiceStudioVersion tts=$TtsModel asr=$AsrModel"

$exe = Find-VoiceStudioExe
if (-not $exe -and -not $SkipVoiceStudioInstall) {
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ("velvet-voicestudio-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    try {
        $msi = Join-Path $tmp $artifact
        $log = Join-Path $tmp "voicestudio-install.log"
        Write-Host "Downloading pinned VoiceStudio $VoiceStudioVersion current-user installer..."
        Invoke-WebRequest $url -OutFile $msi
        Write-Host "Installing VoiceStudio for the current Windows user..."
        $args = @("/i", "`"$msi`"", "/qn", "/norestart", "/L*V", "`"$log`"")
        $proc = Start-Process msiexec.exe -ArgumentList $args -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            Copy-Item $log (Join-Path $StateDir "voicestudio-install.log") -Force -ErrorAction SilentlyContinue
            Fail "VoiceStudio MSI failed exit=$($proc.ExitCode); log copied to $StateDir\voicestudio-install.log"
        }
    }
    finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }
    $exe = Find-VoiceStudioExe
}
if (-not $exe) {
    Fail "VoiceStudio.exe not found. Install VoiceStudio $VoiceStudioVersion or rerun without -SkipVoiceStudioInstall"
}

$discovery = Test-SpeechService
if (-not $discovery) {
    Write-Host "Launching VoiceStudio..."
    Start-Process -FilePath $exe | Out-Null
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 2
        $discovery = Test-SpeechService
        if ($discovery) { break }
    }
}
if (-not $discovery) {
    Fail "VoiceStudio is installed but speech API is not ready. Open VoiceStudio once and complete its explicit first-run setup (Start installation), then rerun this command."
}

$reported = [string]($discovery.service_version)
if ($reported -and $reported -ne $VoiceStudioVersion) {
    Fail "VoiceStudio version mismatch: expected $VoiceStudioVersion, service reports $reported"
}

$script:Python = Resolve-Python
Write-Host "Running VelvetOS speech doctor..."
Invoke-Python "scripts/vf_speech.py" "doctor"

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) "velvet-speech-windows-smoke"
if (Test-Path $SmokeRoot) { Remove-Item -Recurse -Force $SmokeRoot }
New-Item -ItemType Directory -Force -Path $SmokeRoot | Out-Null
$audio = Join-Path $SmokeRoot "hebrew-smoke.wav"
$qa = Join-Path $SmokeRoot "hebrew-smoke.qa.json"
$SmokeText = -join @([char]0x05D1,[char]0x05D3,[char]0x05D9,[char]0x05E7,[char]0x05EA,[char]0x0020,[char]0x05E7,[char]0x05D5,[char]0x05DC,[char]0x0020,[char]0x05E9,[char]0x05DC,[char]0x0020,[char]0x05DE,[char]0x05E2,[char]0x05E8,[char]0x05DB,[char]0x05EA,[char]0x0020,[char]0x05D5,[char]0x05DC,[char]0x05D5,[char]0x05D5,[char]0x05D8)
$request = [ordered]@{
    jobId = "windows-speech-smoke"
    operation = "synthesize"
    text = $SmokeText
    outputAudio = $audio
    outputTranscript = $qa
    language = "he"
    ttsModel = $TtsModel
    asrModel = $AsrModel
    commercialPublish = $true
    qaBackTranscribe = $true
    minimumSimilarity = $MinSimilarity
}
$requestPath = Join-Path $SmokeRoot "request.json"
[IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Write-Host "Running real Hebrew TTS + back-transcription smoke..."
try {
    Invoke-Python "scripts/vf_speech.py" "run" $requestPath
} catch {
    Fail "VoiceStudio service is healthy but the required commercial Hebrew speech stack is not ready. In VoiceStudio Model Catalogue install/enable '$TtsModel' plus '$AsrModel', then rerun. Details: $($_.Exception.Message)"
}

$receiptPath = "$audio.speech.receipt.json"
if (-not (Test-Path $receiptPath)) { Fail "speech smoke receipt missing: $receiptPath" }
if (-not (Test-Path $qa)) { Fail "speech QA receipt missing: $qa" }
$qaData = Get-Content -Raw -Encoding UTF8 $qa | ConvertFrom-Json
if ($qaData.status -ne "PASS") { Fail "speech back-transcription QA did not PASS" }

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$state = [ordered]@{
    schemaVersion = 1
    hostId = $HostId
    platform = "Windows"
    provider = "voicestudio"
    providerVersion = $VoiceStudioVersion
    ttsModel = $TtsModel
    asrModel = $AsrModel
    doctor = "pass"
    speechSmoke = "pass"
    qaStatus = [string]$qaData.status
    qaSimilarity = [double]$qaData.similarity
    speechReceipt = $receiptPath
    qaReceipt = $qa
    repoHead = (& git rev-parse HEAD).Trim()
    verifiedAt = (Get-Date).ToUniversalTime().ToString("o")
}
[IO.File]::WriteAllText($SpeechState, ($state | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

if (Test-Path $EdgeState) {
    $edge = Get-Content -Raw -Encoding UTF8 $EdgeState | ConvertFrom-Json
    $edge | Add-Member -NotePropertyName speechDoctor -NotePropertyValue "pass" -Force
    $edge | Add-Member -NotePropertyName speechSmoke -NotePropertyValue "pass" -Force
    $edge | Add-Member -NotePropertyName voiceStudioVersion -NotePropertyValue $VoiceStudioVersion -Force
    $edge | Add-Member -NotePropertyName speechState -NotePropertyValue $SpeechState -Force
    [IO.File]::WriteAllText($EdgeState, ($edge | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
}

Write-Host "OK Windows VoiceStudio speech doctor + Hebrew TTS/STT QA smoke"
Write-Host "Speech state: $SpeechState"
Write-Host "Edge state: $EdgeState"
