# Windows Path Contract

Status: canonical path contract for the Sderot Windows VelvetOS host.

VelvetOS project/runtime data must not use `%USERPROFILE%` as a generic workspace root. Windows profile state remains profile-bound, while repositories, VelvetOS runtime data and VelvetOS state are addressable through machine-level environment variables.

## Canonical machine variables

```text
VELVET_ROOT=D:\Velvet
VELVETOS_REPO_ROOT=D:\Velvet\Repos\velvetos-core
VELVETOS_RUNTIME_ROOT=D:\Velvet\Runtime\VelvetOS
VELVETOS_STATE_ROOT=D:\Velvet\State\VelvetOS
```

These variables are machine-scoped on the office Windows host so boot-time SYSTEM tasks can resolve them before interactive logon.

## Ownership

- source repositories live under `D:\Velvet\Repos`;
- transient assistant/dev worktrees and task scratch roots live under `D:\Velvet\Workspaces`;
- VelvetOS rebuildable/runtime material lives under `%VELVETOS_RUNTIME_ROOT%`;
- VelvetOS persistent host state lives under `%VELVETOS_STATE_ROOT%`;
- persistent project/application data lives under `D:\Velvet\Data`;
- generated exports, handoffs and deliverables live under `D:\Velvet\Artifacts`;
- operational logs live under `D:\Velvet\Logs`;
- disposable project caches live under `D:\Velvet\Cache`;
- Velvet-specific temporary files live under `D:\Velvet\Tmp`; Edge/Speech/Manim bootstrap scratch and smoke output must resolve through `VELVET_ROOT\Tmp` after migration, with the Windows temp directory allowed only as a legacy fallback;
- shared portable tooling lives under `D:\Velvet\Tools`;
- long-lived local services that are not repositories live under `D:\Velvet\Services` (for example OpenPost staging);
- migration evidence and rollback manifests live under `D:\Velvet\Migration`;
- retained rollback copies live under `D:\Velvet\Backups`;
- archives and retained handoffs live under `D:\Velvet\Archive`.

## Default working path and forbidden locations

On the Windows host, every agent (ChatGPT, Codex, Grok Bot, Cursor, Gemini, Perplexity and local scripts) uses `D:\Velvet` (`VELVET_ROOT`) as its default working directory for all VelvetOS work, and places each output in the matching lane of the ownership map above.

- The Windows Desktop folder (`%USERPROFILE%\Desktop`, including a OneDrive-redirected Desktop) must never be used for clones, worktrees, scratch, downloads, exports, artifacts, logs, handoffs or any other output.
- Do not create new VelvetOS files under C: outside the profile-bound exceptions listed below.
- If a tool defaults to the Desktop or to C:, override it to the matching `D:\Velvet` path (for example `D:\Velvet\Workspaces`, `D:\Velvet\Artifacts` or `D:\Velvet\Tmp`).
- If D: is unavailable, stop and report it; never fall back to the Desktop.

The legacy `%USERPROFILE%\.velvetos` fallback is being retired on this host: the Cognee runtime was consolidated to D: on 2026-09-28.

## Profile-bound state that stays on C:

Do not relocate or globally override `USERPROFILE`, `HOME`, `APPDATA`, `LOCALAPPDATA`, Windows Credential Manager, DPAPI data, browser profiles, certificates, `.ssh`, `.codex`, or `.agents` merely to satisfy this contract.

Installed applications remain in their installer-supported locations unless their vendor supports relocation.

## Compatibility rule

Windows bootstraps must prefer the `VELVETOS_*` variables. During migration only, they may fall back to the legacy `%USERPROFILE%\velvetos-core` and `%USERPROFILE%\.velvetos` locations when the variables are absent.

The fallback is a rollback/commissioning safety net, not the target architecture. New code must not add Chris-specific absolute paths. New assistant/dev work must not create project clones, worktrees, review folders, patch staging, generated artifacts, or task scratch directly under `%USERPROFILE%`; derive those locations from `VELVET_ROOT` and use the ownership map above.

## Cutover rule

1. build or copy the target on D:;
2. verify hashes, Git state, runtime health and required receipts;
3. set the machine-level path variables;
4. restart only the affected component and verify it from D:;
5. perform boot/no-login validation for boot-critical services and tasks;
6. retain the old C: copy or a compatibility junction until legacy-reference scans are clean;
7. remove legacy data only after rollback evidence exists.

A junction may preserve compatibility temporarily, but it must never become the canonical source of truth.
