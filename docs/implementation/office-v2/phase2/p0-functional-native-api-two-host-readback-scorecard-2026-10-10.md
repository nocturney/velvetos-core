# Office 2.0 / #604 — function-first native control benchmark: real two-host fixture readback (2026-10-10)

**Experimentally observed on two connected physical hosts.** This is a narrow, synthetic, non-GUI native API/CLI throughput pilot, NOT a general computer-use provider acceptance or benchmark against UI-TARS/UFO/Windows-MCP. It advances #604's owner correction: optimize **verified application outcome**, not isolation for its own sake. #604 remains OPEN.

## Question

For a trivial, deterministic, repeatedly verified read-only operation with no real user data, is a native API or host scripting entrypoint preferable to a full GUI agent? Contrast at least three significantly different routes **per physical host** before installing a third-party computer-use worker. Test exact postcondition first, basic duration second.

The complete synthetic fixture was **26 bytes**: ASCII `VF604_SYNTHETIC_API_BENCH\n`. Fixture locations were new one-time roots outside the product repository:
- Chris Windows: `D:\Velvet\Pilots\OfficeAccelerator\AgentEnvelopeLab\p0-604-native-provider-benchmark-win-20261010\fixture.txt`.
- MacMiniOffice.local: `/Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-native-provider-benchmark-mac-20261010/fixture.txt`.

Both hosts independently verified fixture byte length **26** and exact content. Each route was run **30 times** sequentially per host, timed in its native host invocation, with independent byte/encoding comparison on every iteration. This is an exploratory microbenchmark, not a population performance study; OS cache warming, terminal shell overhead, process launch and timing APIs differ. Observed p95 uses sorted index floor(0.95*(n-1)) at n=30; it is not a stable statistical latency bound.

## Real observed results

| Host / OS | Native route tested | Verified exact byte readbacks | Observed median (ms) | Observed p95 (ms) |
| --- | --- | ---: | ---: | ---: |
| Chris / Windows | Direct .NET `System.IO.File.ReadAllBytes` | 30/30 | **0.022** | **0.077** |
| Chris / Windows | COM `Scripting.FileSystemObject.OpenTextFile` + UTF-8 comparison | 30/30 | **0.067** | **0.089** |
| Chris / Windows | PowerShell `Get-Content -Raw` + UTF-8 comparison | 30/30 | **0.165** | **0.306** |
| MacMiniOffice.local / macOS | Python `pathlib.Path.read_bytes` | 30/30 | **0.080** | **0.086** |
| MacMiniOffice.local / macOS | Native `/bin/cat` spawned via `subprocess` | 30/30 | **7.857** | **8.422** |
| MacMiniOffice.local / macOS | `/bin/sh -c cat` via `subprocess` | 30/30 | **19.752** | **20.351** |

**Interpretation:** direct in-process native API was fastest for this 26-byte file-read fixture on both machines. The process-spawning Mac CLI results include child startup and shell startup where applicable, while the .NET/COM benchmark ran inside one PowerShell process. The numbers **must not** be used to rank complete apps, app APIs, automation frameworks, model inference, UIA/AX, or cross-platform performance. There was no calibration or randomized fixture order, and no tested browser UI.

**Functional quality:** all six paths returned the same exact synthetic content, not just zero process-exit codes. No file write by any measurement route after initial disposable fixture setup. No model call, paid API, credential, production service, GitHub ref mutation, user GUI interaction, screenshot or external network egress.

## Independent functional feasibility — do not mistake tool presence for capability

- **Windows Chris:** .NET `UIAutomationClient` assembly loads; existing COM FileSystemObject instance works and returns the fixture metadata. This is concrete local native API capability, **NOT Windows interactive GUI automation**. The Remote Desktop Commander executor is `NT AUTHORITY\\SYSTEM` in **Session 0**. Existing interactive `chris` console **Session 1** is separate. No Calculator/real-application UIA clicks were attempted, and running SYSTEM into the visible user's session was NOT proven or authorized. Functional next test should use a narrowly allowlisted existing user-context broker or owner-attended idle app session, not elevate untrusted agent code.
- **MacMiniOffice.local:** built-in `osascript`, `swift`, `automator`, `shortcuts`, `screencapture` exist and `osascript -e 'tell application "Finder" to get version'` returned **27.2**. A follow-up AppleScript Finder request for **synthetic fixture-file name/size** hung for over 30 seconds with no verified result. The single experiment-owned `osascript` process **PID 11184** was terminated without killing Finder or changing TCC. **Mark this Finder-file-metadata task FAILED/TIMEOUT**, not an AppleScript end-to-end success.
- **Windows virtualization limitation:** `Containers-DisposableClientVM` optional feature shows Enabled, but no confirmed Windows Sandbox executable/AppX guest was found in the SYSTEM command session. `wsl --list --quiet` explicitly returned `WSL_E_LOCAL_SYSTEM_NOT_SUPPORTED`. Existing `OfficeV2-Lab` WSL distro is an Office project asset and untouched. Do not infer ready Windows Sandbox or WSL worker from feature presence.
- Both machines' local Ollama instances were also independently found online, so #612 model QA could run in parallel on separate real coding fixtures without installing an extra model. This benchmark itself made ZERO model calls.

## Function-first decision / next benchmark matrix

For concrete requested future tasks, the **first choice should be native application API or CLI** where it supports exact target outcome + independent readback, not a visual agent for every step. Benchmark lanes without prematurely awarding a winner:

1. **Windows GUI named control:** UIAutomationClient/FlaUI baseline vs sbroenne mcp-windows vs CursorTouch Windows-MCP or UFO², using an attended quiet **Session 1** Calculator task `6 * 7 = 42` and an unrelated synthetic real app; verify actual post-action readback. Never run from SYSTEM Session 0 assuming the interactive desktop is accessible. Record PID/HWND, exact foreground app allowlist, failures and user interference. This requires a verified user-context controlled launcher or explicit attended GUI access.
2. **Mac native app control:** AppleScript/JXA/Accessibility/native app automation vs screenshot fallback, starting with synthetic scratch files and read-only target identities. The Finder-file metadata timeout is a known negative; verify TCC authorization and act within bounded per-app timeout, avoid busy user apps.
3. **Cross-platform headless browser:** Playwright/CDP in a disposable supported user-namespace/container/VM or native host with explicit no-real-data fixture, compare DOM selectors vs screenshot fallback. No assumption WSL under SYSTEM works or that WSL itself forms a strong host security boundary.
4. **Recorded/replayable workflows:** test OpenAdapt Flow capture/compile/replay on private-free test app only; independently verify drift recovery and postcondition, prevent customer/screen capture and network egress absent authorization.
5. **Vision-only fallback:** only if accessibility/native APIs fail, compare UI-TARS/OculiX/Agent-S3 on an isolated visual-only canvas, signed executable/model-weight provenance and local GPU feasibility before provisioning. Do not make a general winner claim from vendor benchmarks.

**Proposed scorecard fields:** target outcome, independent postcondition, repetitions and confidence, app+OS, context/user-session/PID, exact version and digest, accepted/denied/false-success, median/p95 wall time including process spawn, memory/CPU/GPU, paid inference, human minutes, remote egress and credentials, no-data/rollback, recovery after UI drift. Functional completion first, broader application scope second; security control remains proportionate and explicit.

## Safety and reproducibility

This is a read-only feasibility report from six actual native file fixture routes plus a separate Finder timeout, **not a production runner or isolation deployment**. All tests used newly created, synthetic 26-byte data. There was no new scheduler/provider/SoT, system ACL/account, credential helper read, firewall/Defender/TCC alteration, global installation, service change, GitHub native scratch ref push, paid model/Codex, Grokbot/Instagram/customer/CAD/printer effect.

Status: **BENIGN_NATIVE_API_READBACK_6_OF_6_PASS; MAC_FINDER_SYNTHETIC_METADATA_TIMEOUT; REAL_GUI_APP_UNTESTED; NO_PRODUCTION_AUTHORITY.** Owner #604 remains open; #612 two-host coding PRs may proceed in distinct worktrees independently of this read-only provider selection.
