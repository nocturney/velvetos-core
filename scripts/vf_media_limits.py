"""Bound local media subprocesses. No shell/network configuration or approvals."""
from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import sys
import threading

MEMORY_BYTES = 1024 * 1024 * 1024
OUTPUT_BYTES = 64 * 1024
_WINDOWS_JOB = None


def _apply_limits(memory_bytes: int, timeout: int) -> None:
    """Set limits in an isolated worker before the decoder is even started."""
    global _WINDOWS_JOB
    if not (16*1024*1024 <= memory_bytes <= MEMORY_BYTES and 1 <= timeout <= 90):
        raise ValueError("Invalid media resource limits")
    if os.name == 'posix':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        return
    if os.name != 'nt':
        raise RuntimeError('No supported process memory limiter on this host')
    from ctypes import wintypes as wt

    class Basic(ctypes.Structure):
        _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                    ('flags', wt.DWORD), ('min_ws', ctypes.c_size_t),
                    ('max_ws', ctypes.c_size_t), ('active_processes', wt.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wt.DWORD),
                    ('scheduling', wt.DWORD)]

    class IoCounters(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in
                    ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

    class Extended(ctypes.Structure):
        _fields_ = [('basic', Basic), ('io', IoCounters),
                    ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                    ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
    kernel.CreateJobObjectW.restype = wt.HANDLE
    kernel.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
    kernel.SetInformationJobObject.restype = wt.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    kernel.AssignProcessToJobObject.restype = wt.BOOL
    kernel.GetCurrentProcess.restype = wt.HANDLE
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = Extended()
    # PROCESS_MEMORY | JOB_MEMORY | KILL_ON_JOB_CLOSE; no breakaway permission.
    limits.basic.flags = 0x100 | 0x200 | 0x2000
    limits.process_memory = limits.job_memory = memory_bytes
    if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
        raise ctypes.WinError(ctypes.get_last_error())
    # Keep the handle alive until os._exit. Descendants inherit this hard limit.
    _WINDOWS_JOB = job


def _worker(args: list[str], timeout: int, memory_bytes: int, capture: bool) -> int:
    _apply_limits(memory_bytes, timeout)
    expired = threading.Event()
    with subprocess.Popen(args, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL) as process:
        def stop() -> None:
            expired.set()
            try:
                process.kill()
            except OSError:
                pass
        timer = threading.Timer(timeout, stop)
        timer.daemon = True
        timer.start()
        try:
            data = process.stdout.read(OUTPUT_BYTES + 1) if capture else b''
            if len(data) > OUTPUT_BYTES:
                stop()
            code = process.wait(timeout=timeout + 1)
            if expired.is_set() or code != 0:
                return 2
            if capture:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            return 0
        finally:
            timer.cancel()


def run_bounded(args: list[str], *, timeout: int = 90, capture: bool = False,
                memory_bytes: int = MEMORY_BYTES) -> bytes:
    """Enforce memory, wall time and bounded stdout; stderr is never buffered."""
    if not args or not all(isinstance(x, str) for x in args):
        raise ValueError('Invalid media command')
    command = [sys.executable, os.path.abspath(__file__), '--worker',
               str(timeout), str(memory_bytes), str(int(capture)), json.dumps(args)]
    with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, start_new_session=os.name == 'posix') as process:
        try:
            data, _ = process.communicate(timeout=timeout + 5)
        except subprocess.TimeoutExpired as exc:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()  # Closing the worker's job kills its descendants.
            process.communicate()
            raise ValueError('Media subprocess time budget exceeded') from exc
        if process.returncode != 0 or len(data) > OUTPUT_BYTES:
            raise ValueError('Media subprocess failed or exceeded its resource/output budget')
        return data


if __name__ == '__main__':
    try:
        if len(sys.argv) != 6 or sys.argv[1] != '--worker':
            raise ValueError('Internal resource worker arguments required')
        result = _worker(json.loads(sys.argv[5]), int(sys.argv[2]),
                         int(sys.argv[3]), bool(int(sys.argv[4])))
    except Exception:
        result = 2
    # Do not explicitly close a Windows job containing the worker before exiting.
    os._exit(result)
