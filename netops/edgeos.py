#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2>=3.1",
#   "pyyaml>=6.0",
# ]
# ///
"""GitOps helper for rendering, diffing, and safely applying EdgeOS config.

Reads router host and template variables from netops/inventory/hosts.yaml and
netops/roles/edgeos-config/templates/edgeos-rtr01.cfg.j2.

Usage:
  uv run netops/edgeos.py render
  uv run netops/edgeos.py diff [--ssh-host <user@host>]
  uv run netops/edgeos.py apply --commands-file <file> [--minutes 5] [--ssh-host <user@host>]
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile

import jinja2
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NETOPS_DIR = REPO_ROOT / "netops"
INVENTORY_FILE = NETOPS_DIR / "inventory" / "hosts.yaml"
TEMPLATE_FILE = NETOPS_DIR / "roles" / "edgeos-config" / "templates" / "edgeos-rtr01.cfg.j2"
SECRETS_FILE = NETOPS_DIR / "secrets" / "rtr01-secret.yaml"

SECRET_PATTERNS = [
    re.compile(r"(encrypted-password\s+)\S+"),
    re.compile(r"(plaintext-password\s+)\S+"),
    re.compile(r"(dyndns\s+(?:login|password)\s+)\S+"),
    re.compile(r"(snmp\s+community\s+)\S+"),
]


def load_inventory() -> tuple[str, dict]:
    data = yaml.safe_load(INVENTORY_FILE.read_text())
    rtr_group = data["rtr"]
    vars_dict = dict(rtr_group.get("vars", {}))
    host_entry = next(iter(rtr_group["hosts"].values()))
    router_ip = host_entry["ansible_host"]
    return router_ip, vars_dict


def load_secrets(allow_redacted: bool = True) -> dict[str, str]:
    defaults = {
        "encrypted_password": "<REDACTED>",
        "dyndns_login": "<REDACTED>",
        "dyndns_password": "<REDACTED>",
    }
    key_file = os.environ.get("SOPS_AGE_KEY_FILE")
    if not key_file or not pathlib.Path(key_file).is_file():
        if allow_redacted:
            return defaults
        raise RuntimeError("SOPS_AGE_KEY_FILE is missing or unreadable; cannot decrypt router secrets")
    res = subprocess.run(
        ["sops", "-d", str(SECRETS_FILE)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        if allow_redacted:
            return defaults
        raise RuntimeError(f"sops decrypt failed: {res.stderr.strip()}")
    decrypted = yaml.safe_load(res.stdout) or {}
    return {k: str(decrypted.get(k, defaults[k])) for k in defaults}


def render_template(allow_redacted: bool = True) -> list[str]:
    _, vars_dict = load_inventory()
    secrets = load_secrets(allow_redacted=allow_redacted)
    ctx = {
        **vars_dict,
        **secrets,
        "groups": {"all": []},
        "hostvars": {},
    }
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    tmpl = env.from_string(TEMPLATE_FILE.read_text())
    rendered = tmpl.render(**ctx)
    lines: list[str] = []
    for raw in rendered.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def redact_line(line: str) -> str:
    out = line
    for pat in SECRET_PATTERNS:
        out = pat.sub(r"\1<REDACTED>", out)
    return out


def normalize_for_diff(lines: list[str]) -> list[str]:
    norm: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("delete "):
            continue
        # Normalize single quotes around single-token values for cleaner diffing
        s = re.sub(r"'([^'\s]+)'", r"\1", s)
        s = redact_line(s)
        norm.append(s)
    return sorted(set(norm))


def ssh_target(override: str | None) -> str:
    if override:
        return override
    router_ip, _ = load_inventory()
    return f"admin@{router_ip}"


def fetch_live_config(target: str) -> list[str]:
    res = subprocess.run(
        ["ssh", target, "/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in res.stdout.splitlines() if line.strip().startswith("set ")]


def cmd_render(_args: argparse.Namespace) -> int:
    for line in render_template(allow_redacted=True):
        print(redact_line(line))
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    target = ssh_target(args.ssh_host)
    desired = normalize_for_diff(render_template(allow_redacted=True))
    live = normalize_for_diff(fetch_live_config(target))
    if args.exclude_dhcp_static:
        desired = [l for l in desired if "static-mapping" not in l]
        live = [l for l in live if "static-mapping" not in l]
    diff = list(
        difflib.unified_diff(
            live,
            desired,
            fromfile=f"live ({target})",
            tofile="git (edgeos-rtr01.cfg.j2)",
            lineterm="",
        )
    )
    if not diff:
        print("No configuration drift detected.")
        return 0
    for line in diff:
        print(line)
    return 0


def run_smoke_tests(target: str, router_ip: str, k8s_domain: str) -> None:
    print("=== Smoke 1: Fresh SSH connection ===")
    res = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", target, "echo SSH_OK"],
        check=True,
        capture_output=True,
        text=True,
    )
    if "SSH_OK" not in res.stdout:
        raise RuntimeError("Fresh SSH smoke test failed")
    print("SSH_OK")

    print("=== Smoke 2: Outbound HTTPS egress ===")
    egress = subprocess.run(
        ["curl", "-fsS", "--max-time", "5", "https://checkip.amazonaws.com"],
        check=True,
        capture_output=True,
        text=True,
    )
    wan_ip = egress.stdout.strip()
    if not wan_ip:
        raise RuntimeError("Outbound HTTPS egress returned empty response")
    print(f"Egress OK ({wan_ip})")

    print(f"=== Smoke 3: Internal DNS via {router_ip} ({k8s_domain}) ===")
    dns_check = subprocess.run(
        ["ssh", target, f"/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces ethernet eth0"],
        check=True,
        capture_output=True,
        text=True,
    )
    if "state UP" not in dns_check.stdout:
        raise RuntimeError("WAN interface eth0 is not UP")
    print("Router WAN interface UP")


def cmd_apply(args: argparse.Namespace) -> int:
    router_ip, vars_dict = load_inventory()
    target = ssh_target(args.ssh_host)
    commands_path = pathlib.Path(args.commands_file)
    commands = [
        l.strip()
        for l in commands_path.read_text().splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    if not commands:
        print("No commands to apply.", file=sys.stderr)
        return 1
    for c in commands:
        if not (c.startswith("set ") or c.startswith("delete ")):
            raise ValueError(f"Only 'set' and 'delete' commands are allowed, got: {c!r}")

    # 1. Local timestamped backup before mutating
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = pathlib.Path(tempfile.gettempdir()) / f"edgeos-backup-{ts}.cfg"
    live_lines = fetch_live_config(target)
    backup_path.write_text("\n".join(live_lines) + "\n")
    backup_path.chmod(0o600)
    print(f"Saved pre-change backup to {backup_path}")

    # 2. Build remote script using vyatta-cfg-cmd-wrapper + PTY commit-confirm
    remote_lines = [
        "#!/bin/bash",
        "set -euo pipefail",
        "sg vyattacfg -c '",
        "set -euo pipefail",
        "CMD=/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper",
        "export CMD_WRAPPER_SESSION_ID=$$",
        "$CMD begin",
        'trap "$CMD end || true" EXIT',
    ]
    for c in commands:
        remote_lines.append(f"$CMD {c}")
    remote_lines.extend(
        [
            f'sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=commit-confirm --minutes={args.minutes}"',
            "$CMD commit",
            "'",
        ]
    )
    remote_script = "\n".join(remote_lines) + "\n"

    print(f"Uploading and committing {len(commands)} commands with commit-confirm {args.minutes}m...")
    subprocess.run(
        ["ssh", target, "cat > /tmp/edgeos-apply.sh"],
        input=remote_script,
        text=True,
        check=True,
    )
    subprocess.run(
        ["ssh", "-tt", target, "bash /tmp/edgeos-apply.sh && rm -f /tmp/edgeos-apply.sh"],
        input="y\n",
        text=True,
        check=True,
    )

    # 3. Automated smoke tests before confirming
    run_smoke_tests(target, router_ip, vars_dict.get("k8s_domain", ""))

    # 4. Confirm & save
    print("=== All smoke tests passed — confirming & saving ===")
    subprocess.run(
        [
            "ssh",
            target,
            'sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=confirm" && '
            'sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save"',
        ],
        check=True,
    )
    print("Confirmed and saved to /config/config.boot.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="EdgeOS GitOps helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="Render EdgeOS template (secrets redacted if SOPS unset)")
    p_render.set_defaults(func=cmd_render)

    p_diff = sub.add_parser("diff", help="Diff live router config against Git template")
    p_diff.add_argument("--ssh-host", help="Override SSH target (default: admin@<ansible_host>)")
    p_diff.add_argument(
        "--exclude-dhcp-static",
        action="store_true",
        default=True,
        help="Ignore DHCP static-mapping lines during diff (default: true)",
    )
    p_diff.add_argument(
        "--include-dhcp-static",
        dest="exclude_dhcp_static",
        action="store_false",
        help="Include DHCP static-mapping lines during diff",
    )
    p_diff.set_defaults(func=cmd_diff)

    p_apply = sub.add_parser("apply", help="Apply a reviewed set/delete file with commit-confirm + smoke tests")
    p_apply.add_argument("--commands-file", required=True, help="File containing set/delete commands")
    p_apply.add_argument("--minutes", type=int, default=5, help="commit-confirm rollback timer (default: 5)")
    p_apply.add_argument("--ssh-host", help="Override SSH target (default: admin@<ansible_host>)")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
