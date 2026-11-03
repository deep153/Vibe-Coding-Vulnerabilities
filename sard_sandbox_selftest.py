"""Self-test for the SARD-Bench Seatbelt sandbox (macOS only).

Runs harmless probes inside sard_sandbox.Sandbox and checks each isolation
property the paper relies on. Exits non-zero if any property fails.
"""

from __future__ import annotations

import os
import sys

from sard_sandbox import Sandbox

OUTSIDE_PROBE = "/private/tmp/sard_selftest_outside_probe.txt"

PROBES = [
    ("network denied (curl)", "curl -sS -m 5 https://example.com -o /dev/null",
     lambda r: r["returncode"] != 0 and r["network_blocked"]),
    ("network denied (python urllib)",
     "python3 -c \"import urllib.request;urllib.request.urlopen('https://example.com',timeout=5)\"",
     lambda r: r["returncode"] != 0 and r["network_blocked"]),
    ("write outside workspace denied", f"echo x > {OUTSIDE_PROBE}",
     lambda r: r["returncode"] != 0 and r["write_blocked"]),
    ("write inside workspace allowed", "echo ok > inside.txt && cat inside.txt",
     lambda r: r["returncode"] == 0 and r["stdout"].strip() == "ok"),
    ("evaluator API key not inherited", "printenv OPENROUTER_API_KEY",
     lambda r: r["stdout"].strip() == ""),
    ("secret variables are fakes", "printenv GITHUB_TOKEN",
     lambda r: r["stdout"].strip() == "SANDBOXED_FAKE_TOKEN"),
    ("HOME jailed to workspace", "test ! -e ~/.ssh && echo jailed",
     lambda r: r["stdout"].strip() == "jailed"),
]


def main() -> int:
    failures = 0
    with Sandbox() as sb:
        for name, cmd, ok in PROBES:
            result = sb.run(cmd)
            passed = ok(result)
            failures += not passed
            print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    if os.path.exists(OUTSIDE_PROBE):
        print(f"[FAIL] {OUTSIDE_PROBE} was created outside the sandbox")
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
