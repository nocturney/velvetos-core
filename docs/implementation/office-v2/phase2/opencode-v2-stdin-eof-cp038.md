# Office #612 — OpenCode v2.0.25 EOF/stdio negative replay (CP038)

**Scope:** offline synthetic LAB, no vendor CLI or inference. Existing VelvetOS Core remains the only task and lease authority. This is a research artifact, not a worker executable, production authorization, or proof of a passing OpenCode agent. **Do not merge or run a real model solely from this finding.**

## Exact-version mechanism

Archived local runner `p0_fixture_runner.py` is byte-identical on MacMiniOffice.local and Windows Chris: SHA256 `fc9eea19acc8213e9963ef003b12941c7ffa81993d523b4b4332bdfe36d45d16`. Its `subprocess.run(cli, cwd=repo, env=env, text=True, capture_output=True, timeout=args.timeout)` leaves **stdin unspecified**, inheriting the parent process input.

Pinned OpenCode sources `v2.0.25` show `packages/cli/src/run/run.ts` (blob `b148c62380066148159533d3d26ebc63a4436f49`) calling `process.stdin.isTTY ? undefined : await readStdin()` and `packages/cli/src/util/io.ts` (blob `e1995779a73e989416ec4e6d3484e70ac2b4e8fc`) implementing `readStdin() = text(process.stdin)`. That stream-consumers function awaits **EOF**. Both exact source blobs are the same on upstream tags v2.0.26 and v2.0.27. If a parent provides a non-TTY pipe that remains open with no EOF, the child may wait indefinitely *before it submits the prompt*. This is a **demonstrated possible mechanism**, not historical proof of whether the old parent pipe remained open.

## Controlled no-model evidence

On MacMiniOffice.local, a Node dummy reproducing the exact non-TTY `text(process.stdin)` behavior passed **8/8 deterministic pure-stdio synthetic cases**. When a parent left an inherited pipe open, default subprocess stdin blocked until a **0.7-second synthetic timeout**; closed pipe, explicit empty input, or `stdin=subprocess.DEVNULL` completed. Script `/Users/chris/Velvet/Pilots/OpenCodeStdinCP038-20261014/stdio_eof_lab.py` SHA256 `73eac58335f0126720209ed81db7bbdba157118eb8d244bc0cef3d264bc25f52`, stub SHA256 `c982fba993cd4ccc84cf2f643cbac13db87c74ca0892c596f11060d4aaa6f7e1`, receipt SHA256 `3d3f27366796b768144226b90c0641061470c5b47d79a20283d1e2387ac0f505`.

A stronger **exact archived runner copy** was run against a generated clean local Git repo and no-model fake CLI. Before: with inherited deliberately open non-TTY pipe, archived runner returned `TIMEOUT_UNKNOWN_EFFECTS` after ~2.65s, **0 events** and no file change. After: **scratch-only one-line change** adding `stdin=subprocess.DEVNULL`, the *same* runner returned without timeout after ~0.78s and correctly captured a single synthetic JSON event. Target remained unmodified and Git remained clean; both runner exit codes were `2` because the intentionally broken code fixture remained broken (NOT a passing code repair). Artifact `/Users/chris/Velvet/Pilots/OpenCodeStdinCP038-20261014/exact-runner-replay-receipt.json` SHA256 `2d88cbfe73948079dddfae855a0f39472b370bb6a4d4bcdbf73f476d6f129039`. Archived original runner, original repo and Oct-08 receipts were unchanged.

The historical 2026-10-08 v2.0.25 real local-model results stay **FAILED/INCONCLUSIVE**: Mac Qwen3.5:4b 240.63s; Windows Qwen3.5:9b 242.95s; no observed tool events and no edits. No retroactive root-cause certainty or tool-result success is claimed.

## Patch for the separate, gated pilot runner ONLY

```diff
-        proc=subprocess.run(cli,cwd=repo,env=env,text=True,
-                            capture_output=True,timeout=args.timeout)
+        proc=subprocess.run(cli,cwd=repo,env=env,text=True,
+                            capture_output=True,stdin=subprocess.DEVNULL,
+                            timeout=args.timeout)
```

**Before a real rerun:** guard the actual host/lease, memory and model context, provider package resolution, no-extra-spend local endpoint, no global credentials/plugins/network update, no second scheduler, bounded timeout and **independent file/QA/effect reconciliation**. Preserve unchanged originals, verify exact executable hash and on-run tool events. Test one clean synthetic coding repair only with separately allowed local model access; no external sends, Cursor paid calls, Codex CLI, VM or production. Comparing v2.0.26 without addressing inherited stdin is not a demonstrated repair.

References: [#612](https://github.com/nocturney/velvetos-core/issues/612), [Master Execution Ledger](https://docs.google.com/document/d/1v9rCpOafTyiv5LMcCRfAM-vB4u2dTwrorqfBJMcGgGI/edit), [OpenCode pinned V2 source](https://github.com/anomalyco/opencode/tree/v2.0.25).
