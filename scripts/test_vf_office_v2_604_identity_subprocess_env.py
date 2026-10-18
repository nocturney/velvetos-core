#!/usr/bin/env python3
"""Identity-helper subprocess env is a constructed allowlist.

The child must not see parent names. A missing required name refuses the
spawn. This does not start etcd, openssl, or git, and it does not admit.
"""
import json
import os
import sys
import unittest
from unittest import mock

import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity


class IdentitySubprocessEnvTests(unittest.TestCase):
    def test_child_sees_only_allowlisted_keys(self):
        script = (
            "import json, os, sys\n"
            "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))\n"
        )
        poison = {
            "VF_CANARY_SECRET": "not-a-real-secret",
            "OPENSSL_CONF": "/tmp/not-a-real-openssl.cnf",
            "GIT_CONFIG_COUNT": "1",
        }
        with mock.patch.dict(os.environ, poison, clear=False):
            proc = identity.subprocess_safe(
                [sys.executable, "-c", script], timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        child = json.loads(proc.stdout)
        self.assertEqual(set(child), set(identity.IDENTITY_ENV_REQUIRED))
        self.assertEqual(child, identity.identity_subprocess_env())
        for name in poison:
            self.assertNotIn(name, child)

    def test_missing_required_name_refuses_before_spawn(self):
        def spawned(*args, **kwargs):
            raise AssertionError("child spawned without a required name")

        broken = dict(identity.identity_subprocess_env())
        del broken["PATH"]
        with mock.patch.object(identity, "identity_subprocess_env", lambda: broken):
            with mock.patch.object(identity.subprocess, "run", spawned):
                with self.assertRaises(RuntimeError) as caught:
                    identity.subprocess_safe([sys.executable, "-c", "raise SystemExit(9)"])
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")

        empty = identity.identity_subprocess_env()
        empty["LANG"] = ""
        with self.assertRaises(RuntimeError) as caught:
            identity.require_identity_env(empty)
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")


if __name__ == "__main__":
    unittest.main()
