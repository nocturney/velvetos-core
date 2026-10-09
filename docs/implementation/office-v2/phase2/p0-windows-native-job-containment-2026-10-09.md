# Office 2.0 #612 — actual Windows native Job Object child containment (2026-10-09)

**Gate:** REAL_TWO_PROCESS_NATIVE_WINDOWS_JOB_LAB_PASS; 17/17 OFFLINE NEGATIVES PASS MAC+WINDOWS; NOT YET ACTUAL AIDER SUPERVISION; NO AUTOMATIC RETRY OR PRODUCTION WRITER.

## Test boundary and native API

A unique Windows LAB directory `D:\\Velvet\\Pilots\\OfficeAccelerator\\WindowsJobObjectLab\\20261009-a` launched only two pre-reviewed, short-lived Python fixture processes. The controller created an **unnamed** native Windows Job Object, set the `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` flag via `SetInformationJobObject(JobObjectExtendedLimitInformation)`, and assigned the fixture owner with `AssignProcessToJobObject` **before** permitting it to spawn its child. The child inherited Job membership normally (no `CREATE_BREAKAWAY_FROM_JOB`). Both OS process handles were checked with `IsProcessInJob`, `GetProcessTimes`, and a zero-timeout `WaitForSingleObject` before closing the sole owned Job handle. Both handles then became signaled within the bounded post-close wait. Subsequent Win32 CIM readback listed no processes with the fixture's historical PIDs. The Job Object never contained a user or Office process.

- Official documentation: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject), [JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information).
- Exact historical controller/owned child PIDs: `49760`, `57016`; kernel creation times (microseconds): `1791553962712716`, `1791553962762093`.
- Native job limit: `0x00002000`. Both processes inside the same unnamed job **before close**: `true`. Both observed exited **after close**: `true`.
- Original UNKNOWN model-task retry allowed: `false`. All potential escaped descendants excluded: `false`. Model invocations: `0`; cloud/API spend: `0`.
- Actual exact sealed historical receipt SHA256: `e44cb0fc832b57c8f194caf22646dab8b978381b83d3ca2e8bdb64486ac1b6ad`. This is a **selfhash, not an external digital signature**.
- Exact source Git blob `078c867a40ea869acc261d9b2802646ddf277ac3`, SHA256 `3f49a2f4a09c03d7e44506e5e034640547ba592eae498d99a90ab113ba21681f`, byte-identical on Chris Windows and Mac Mini.
- `selftest` **17/17 PASS** on both Windows and Mac, including 15 differently re-sealed false claims, plus corrupted selfhash. Exact proof copied to Mac and verified with pure `verify --evidence`: PASS, no native process call.

## CI and restrictions

`scripts/check-office-v2-contracts.py` runs the static `selftest` and real receipt `verify` only. Neither command calls `CreateJobObject`, starts any subprocess, touches models, enumerates the OS process table, contacts a business service, or writes production state. The explicit `live` action is Windows-only and bound to an exclusive temporary fixture, with natural 16-second self-expiry on assignment failure and a fail-closed cleanup of **only this script's unnamed Job handle**. No global registry, security, firewall, WSL, Autostart, approval or new scheduler changes.

Windows Job Objects contain ordinary inherited process creation by default, but application-specific breakaway behavior and `Win32_Process.Create` semantics require separate admission. Actual Aider/Ollama containment is **not** proven by this Python fixture, and macOS POSIX group emptiness has already been disproved by [the separate Mac negative](p0-orphan-escape-negative-2026-10-09.md). An unattended agent should not be admitted to recovery unless its *actual* worker uses a validated containment primitive, the original UNKNOWN journal is reconciled, and host lease/placement is authorized solely through #604. #612 P0 remains PARTIAL.
