# Windows Path Contract

Status: generic canonical path contract for VelvetOS Windows hosts.

VelvetOS project/runtime data must not use `%USERPROFILE%` as a generic workspace root. Windows profile state remains profile-bound, while repositories, VelvetOS runtime data and VelvetOS state are addressed through explicit machine-level environment variables.

Concrete host ids and absolute paths are **instance/private deployment bindings**, not Core defaults. A selected instance may declare a `windowsHostBinding` surface; machine-level environment variables must match that deployment binding before host bootstrap.

## Required machine variables

```text
VELVET_ROOT=<absolute Windows root for VelvetOS work>
VELVETOS_REPO_ROOT=<absolute checkout path for velvetos-core>
VELVETOS_RUNTIME_ROOT=<absolute rebuildable/runtime root>
VELVETOS_STATE_ROOT=<absolute persistent host-state root>
VELVETOS_HOST_ID=<explicit host identifier>
```

These variables are machine-scoped so boot-time SYSTEM tasks can resolve them before interactive logon. Core does not define a business location, drive letter, username or host id.

## Ownership

All portable lanes are derived from `%VELVET_ROOT%` unless a domain-specific contract explicitly says otherwise:

- source repositories: `%VELVET_ROOT%\Repos`;
- transient assistant/dev worktrees and task scratch roots: `%VELVET_ROOT%\Workspaces`;
- persistent project/application data: `%VELVET_ROOT%\Data`;
- generated exports, handoffs and deliverables: `%VELVET_ROOT%\Artifacts`;
- operational logs: `%VELVET_ROOT%\Logs`;
- disposable project caches: `%VELVET_ROOT%\Cache`;
- Velvet-specific temporary files: `%VELVET_ROOT%\Tmp`;
- shared portable tooling: `%VELVET_ROOT%\Tools`;
- long-lived local services that are not repositories: `%VELVET_ROOT%\Services`;
- migration evidence and rollback manifests: `%VELVET_ROOT%\Migration`;
- retained rollback copies: `%VELVET_ROOT%\Backups`;
- archives and retained handoffs: `%VELVET_ROOT%\Archive`.

Repository, runtime and persistent host-state roots are taken from `VELVETOS_REPO_ROOT`, `VELVETOS_RUNTIME_ROOT` and `VELVETOS_STATE_ROOT` respectively. Bootstraps must not infer them from `VELVET_ROOT` when an explicit variable is required.

## Default working path and forbidden locations

On a Windows host, every agent and local script uses `%VELVET_ROOT%` as the default working root for VelvetOS work and places each output in the matching lane above.

- The Windows Desktop folder (`%USERPROFILE%\Desktop`, including a OneDrive-redirected Desktop) must never be used for clones, worktrees, scratch, downloads, exports, artifacts, logs, handoffs or other VelvetOS output.
- Do not create new VelvetOS files on the system drive outside the profile-bound exceptions listed below.
- If a tool defaults to the Desktop or system drive, override it to the matching `%VELVET_ROOT%` lane.
- If a required machine variable is unavailable, stop and report it; never infer a user-profile or temporary-directory fallback.

## Profile-bound state

Do not relocate or globally override `USERPROFILE`, `HOME`, `APPDATA`, `LOCALAPPDATA`, Windows Credential Manager, DPAPI data, browser profiles, certificates, `.ssh`, `.codex`, or `.agents` merely to satisfy this contract.

Installed applications remain in their installer-supported locations unless their vendor supports relocation.

## Compatibility rule

On Windows, VelvetOS code resolves repository, runtime, state, scratch and host identity only through `VELVET_ROOT`, `VELVETOS_REPO_ROOT`, `VELVETOS_RUNTIME_ROOT`, `VELVETOS_STATE_ROOT` and `VELVETOS_HOST_ID`. Legacy `%USERPROFILE%\.velvetos` and `%USERPROFILE%\velvetos-core` fallbacks are closed (fail closed): when a required variable is missing, the tool stops with a clear error naming that variable instead of falling back to profile storage.

This covers Windows bootstraps, the Cognee adapter/runtime updater, and the vfmem Cognee interpreter lookup. Explicit process-scoped `VFMEM_COGNEE_*` overrides still take precedence where their existing contracts allow them.

macOS hosts are out of scope for this Windows contract and keep their existing platform-specific state semantics.

New Core code must not add user-specific absolute paths, business-location host labels, or concrete Windows drive/root values. Concrete deployment values belong in the selected instance/private host-binding surface and machine environment.

## Cutover rule

1. create or verify the selected instance/private host binding;
2. set the required machine-level environment variables from that deployment binding;
3. build or copy the target into the resolved machine roots;
4. verify hashes, Git state, runtime health and required receipts;
5. restart only the affected component and verify it from the resolved roots;
6. perform boot/no-login validation for boot-critical services and tasks;
7. retain old compatibility paths until legacy-reference scans are clean and rollback evidence exists;
8. remove legacy data only after explicit retirement authorization.

A junction may preserve compatibility temporarily, but it must never become the canonical source of truth.
