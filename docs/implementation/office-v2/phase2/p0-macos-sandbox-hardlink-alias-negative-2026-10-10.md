# Office 2.0 / #604 — macOS kernel sandbox hard-link path alias bypass (2026-10-10)

**Security result: RED.** Real macOS `sandbox-exec` pathname denial worked for the original synthetic file and its symlink, but a **PREEXISTING hard link to the exact same file/inode outside the denied subtree remained readable** inside the sandbox. This was observed with both `literal` exact-file and `subpath` whole-directory policies. This is a bounded pathname-alias test, **not a general proof that every possible sandbox policy is bypassable**. It reinforces #675: filesystem path filters alone, or different PIDs sharing the same OS user, do not attest an exclusive native Git credential owner.

## Reproduction, provenance and constraints

- Code: `scripts/vf_office_v2_604_macos_sandbox_hardlink_alias_lab.py`
- Exact original Mac source SHA256: `f7d583fbaab683b69f96bfebae9cdb91c2a88609530beaae1153cf28f0a92add`
- Mac machine: MacMiniOffice.local, `chris` UID 501. New isolated mode-0700 directory `/Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-kernel-sandbox-hardlink-alias-20261010`.
- Mac native `/usr/bin/sandbox-exec` exists and operated in this trial. It is a deprecated interface; no persistent profile or system-wide sandbox setting was installed.
- Each run creates a fresh mode-0700 disposable directory containing **fake nonsecret marker bytes**, a mode-0600 file in a fake Sink-secrets directory, a symlink to that same file, and a preexisting hard link in the same filesystem **outside** the secrets directory. There are **no certificates, passwords, tokens, Keychain items, real Git helper files or production files**. The marker bytes never appear in the JSON report.
- Direct command-line `sandbox-exec -f <temporary-profile> /bin/cat <fake-path>` and direct Python file-open were tested. No daemon, real service, Git network write, global ACL/trust/firewall modification, account creation, VM, Codex CLI, paid API, customer/Instagram/Grokbot/printer/CAD effect or autostart change.
- The exact temp profile has `(version 1)`, `(allow default)` and a `(deny file-read*...)` rule, either `(literal <fake-key>)` or `(subpath <fake-secrets-directory>)`. A path-only profile permits a hardlink created *before* the sandboxed worker launches; this does NOT establish a sandboxed worker itself could create a hardlink after launch.

## Live Mac 15/15 checks (PASS means **negative** bypass observed)

1. Disposable fixture owned by executing UID.
2. Fake key mode 0600, verifiably synthetic.
3. Preexisting hardlink has same device+inode.
4. Symlink resolves to fake key, within disposable lab only.
5. Unsandboxed same-user process reads original fake key.
6. Unsandboxed same-user process reads hardlink alias.
7. `literal` denial blocks direct original pathname.
8. `literal` denial blocks symlink.
9. **`literal` denial allows preexisting hardlink alias — security negative.**
10. `subpath` directory denial blocks direct original pathname.
11. `subpath` directory denial blocks symlink.
12. **`subpath` denial still allows preexisting hardlink alias — security negative.**
13. Same sandbox permits benign nonsecret reads, so the profile is actually running.
14. Sandbox denies Python direct read of original fake key, not just `cat`.
15. There were zero remote GitHub credentials/effects or OS-global modifications.

Actual Mac integration exit 0, status `PASS_EXPECTED_NEGATIVE_HARDLINK_ALIAS`, 15 checks. Standalone portable `selftest`: **15/15 PASS** in Mac original test; `verify`: `DESIGN_ONLY_NOT_ADMITTED` with all live proof and production safety flags **false**. Both return JSON for CI. New disposable subdirectories were deleted and absence verified.

**Interpretation:** The security test passed because the *attack path was observed*, not because the isolation is good. The experiment does not test full macOS Seatbelt/App Sandbox production design, different effective UIDs, mandatory controls over file descriptors/inodes, or a properly isolated VM. Not all sandbox policies will share this limitation. The exact tested policy is proven insufficient; robust OS principal or virtualization separation remains required.

**Truthful portable QA correction:** The first independent Chris Windows test run failed two portable test assertions because `pathlib.Path('/tmp/...')` renders a Windows path instead of a POSIX path. No Mac live-bypass result was changed. Corrected only the portable test inputs to `pathlib.PurePosixPath`; reran Mac portable 15/15 and REAL Mac kernel 15/15 with source SHA updated. The original Windows failure was a genuine QA gate failure, not promoted to green; independent clean Windows checkout of the corrected exact PR head is required again.

## Windows and macOS independent read-only readiness

- Windows machine Chris Remote Desktop Commander executes as `NT AUTHORITY\\SYSTEM`, session 0. Separate interactive user console session 1 exists. Never run untrusted workers as SYSTEM just because the remote executor does.
- Windows optional feature `Containers-DisposableClientVM` reads **Enabled**, and `VirtualMachinePlatform` / `Microsoft-Windows-Subsystem-Linux` also read Enabled. However `C:\\Windows\\System32\\WindowsSandbox.exe` and other checked conventional Sandbox executables were NOT present in this noninteractive service context; listing installed Sandbox AppX entries returned no confirmed installed package. A running Windows Sandbox instance was NOT observed. So **the optional feature state is not an accepted Windows Sandbox capability proof**.
- Actual command `wsl --list --quiet` as SYSTEM reported `WSL_E_LOCAL_SYSTEM_NOT_SUPPORTED`. Therefore a worker/VM pilot launched from the existing Remote Commander SYSTEM session cannot assume WSL is available. No feature enable, DISM, reboot, Sandbox launch or session switch was attempted.
- Mac existing `nobody` and `_www` UIDs exist, but `sudo -n -u nobody id` reported a password required. So there is no proven passwordless owner-authorized route from the current Mac `chris` executor into an independently protected OS principal. The test did NOT ask for a password or change sudoers/accounts.

## Exact safe commands

Portable:
`python scripts/vf_office_v2_604_macos_sandbox_hardlink_alias_lab.py selftest`
`python scripts/vf_office_v2_604_macos_sandbox_hardlink_alias_lab.py verify`

Explicit Mac ephemeral lab only:
`python3 scripts/vf_office_v2_604_macos_sandbox_hardlink_alias_lab.py integration /Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-kernel-sandbox-hardlink-alias-20261010`

`integration` refuses non-Darwin hosts, absent `sandbox-exec`, wrong root name, symlink root, wrong owner, weak mode and injection into the restrictive policy. Never point it at existing real credentials; it owns and deletes its own fake bytes.

CI must pin source SHA, run 15 portable negative tests plus verify refusal, and never claim the Mac kernel sandbox was exercised by GitHub-hosted CI. Independently run genuine Mac 15/15 on the exact PR HEAD; ensure Windows and Mac source hashes and portable tests match, normal protected GitHub check-all and Chris Windows full `check-all` pass, and only merge with exact head. Postmerge same-main readback, CI and Windows full sensors required.

## Owner decision / remaining P0 gate

1. **Preferred security boundary:** a dedicated, narrowly permissioned OS account, or a genuinely isolated worker VM/container with *no* host Sink key/token mount or helper access. A separate running process or deprecated path-based Sandbox deny-only rule is insufficient if the same user can create/carry aliases or launch code outside the profile.
2. The ONE canonical #604 provider owns lease/epoch, an authenticated Sink client and durable unleased pending intent, and denies all worker writes with current Git SHA. Attest both client keys and effective OS principal isolation; do not auto-clear UNKNOWN and do not create another SoT/scheduler.
3. Explicit owner authorization is still needed to provision/move real credentials, change persistent OS accounts/ACLs, set up VM activation/reboot, or perform real GitHub scratch ref pushes. Removing business publishing downtime concerns does not turn unverified credential custody into safe writer admission.
4. After that gate, use an owner-approved disposable GitHub pilot and independently deny stale and unauthorized native writes mid-push, through real lease expiry/partition/lost ACK; historical #670 real expired owner acceptance remains unsafe. GitHub's observed repository ruleset ID 23284099 covers `~DEFAULT_BRANCH` only, not proven enforcement for historical LAB scratch refs.
5. #604 and downstream #612 remain OPEN/P0 PARTIAL. No Codex CLI or extra paid model.

**No production isolation was deployed in this PR.** The lab is a sharply scoped RED evidence/CI regression guard.
