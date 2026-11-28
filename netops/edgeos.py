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
  uv run netops/edgeos.py apply --commands-file <file> [--dry-run] [--minutes 5] [--ssh-host <user@host>]
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import os
import pathlib
import re
import shlex
import socket
import struct
import subprocess
import sys

import jinja2
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NETOPS_DIR = REPO_ROOT / "netops"
INVENTORY_FILE = NETOPS_DIR / "inventory" / "hosts.yaml"
TEMPLATE_FILE = NETOPS_DIR / "roles" / "edgeos-config" / "templates" / "edgeos-rtr01.cfg.j2"
SECRETS_FILE = NETOPS_DIR / "secrets" / "rtr01-secret.yaml"
BACKUP_DIR = pathlib.Path.home() / ".config" / "edgeos" / "backups"

SSH_BASE = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]

SECRET_PATTERNS = [
    re.compile(r"(encrypted-password\s+)(?:'[^']*'|\S+)"),
    re.compile(r"(plaintext-password\s+)(?:'[^']*'|\S+)"),
    re.compile(r"(service\s+\S+\s+(?:login|password)\s+)(?:'[^']*'|\S+)"),
    re.compile(r"(snmp\s+community\s+)(?:'[^']*'|\S+)"),
]


def load_inventory() -> tuple[str, dict]:
    data = yaml.safe_load(INVENTORY_FILE.read_text())
    rtr_group = data["rtr"]
    vars_dict = dict(rtr_group.get("vars", {}))
    hosts = rtr_group["hosts"]
    if len(hosts) != 1:
        raise RuntimeError(f"Expected exactly 1 router host in {INVENTORY_FILE}, found {len(hosts)}")
    host_entry = next(iter(hosts.values()))
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
        [*SSH_BASE, target, "/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip().startswith("set ")]
    if not lines:
        raise RuntimeError(f"Live config from {target} returned 0 'set' lines — aborting")
    return lines


def parse_edgeos_commands(commands_path: pathlib.Path) -> list[list[str]]:
    parsed: list[list[str]] = []
    for lineno, raw in enumerate(commands_path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = shlex.split(stripped)
        if len(tokens) < 2 or tokens[0] not in ("set", "delete"):
            raise ValueError(
                f"{commands_path}:{lineno}: only 'set <path...>' or 'delete <path...>' "
                f"commands are allowed, got: {stripped!r}"
            )
        parsed.append(tokens)
    if not parsed:
        raise ValueError(f"{commands_path}: no commands found")
    return parsed


def save_secure_backup(lines: list[str]) -> pathlib.Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.chmod(0o700)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"edgeos-backup-{ts}.cfg"
    fd = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return backup_path


def udp_dns_query(server_ip: str, qname: str, timeout: float = 3.0) -> None:
    """Send a minimal DNS A query over UDP to server_ip:53 and assert NOERROR."""
    txid = 0x4242
    header = struct.pack("!HHHHHH", txid, 0x0100, 1, 0, 0, 0)
    qbytes = b"".join(bytes([len(p)]) + p.encode("ascii") for p in qname.strip(".").split(".")) + b"\x00"
    packet = header + qbytes + struct.pack("!HH", 1, 1)  # QTYPE=A, QCLASS=IN
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(packet, (server_ip, 53))
        resp, _ = sock.recvfrom(512)
    if len(resp) < 12:
        raise RuntimeError(f"Short DNS response from {server_ip}:53")
    resp_id, flags = struct.unpack("!HH", resp[:4])
    rcode = flags & 0x000F
    if resp_id != txid or rcode != 0:
        raise RuntimeError(f"DNS query for {qname} via {server_ip}:53 failed (rcode={rcode})")


def run_smoke_tests(target: str, router_ip: str, site_domain: str) -> None:
    print("=== Smoke 1: Fresh SSH connection ===")
    res = subprocess.run(
        [*SSH_BASE, target, "echo SSH_OK"],
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

    test_host = f"example.com"
    print(f"=== Smoke 3: DNS forwarding via {router_ip}:53 ({test_host}) ===")
    udp_dns_query(router_ip, test_host)
    print(f"DNS OK ({router_ip}:53 resolved {test_host})")

    print("=== Smoke 4: Router WAN interface eth0 UP ===")
    eth0 = subprocess.run(
        [*SSH_BASE, target, "/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces ethernet eth0"],
        check=True,
        capture_output=True,
        text=True,
    )
    if "state UP" not in eth0.stdout:
        raise RuntimeError("WAN interface eth0 is not UP")
    print("Router WAN interface UP")


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


def build_inner_script(parsed_commands: list[list[str]], dry_run: bool, minutes: int) -> str:
    """Build a standalone bash script executed under `sg vyattacfg` without nested single quotes."""
    lines = [
        "#!/bin/bash",
        "set -euo pipefail",
        "export vyatta_sbindir=/opt/vyatta/sbin",
        "CMD=/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper",
        "export CMD_WRAPPER_SESSION_ID=$$",
        '"$CMD" begin',
        'trap \'"$CMD" end || true\' EXIT',
    ]
    for tokens in parsed_commands:
        quoted = " ".join(shlex.quote(t) for t in tokens)
        lines.append(f'"$CMD" {quoted}')

    if dry_run:
        lines.extend(
            [
                'session_env=$(/opt/vyatta/sbin/my_cli_shell_api getSessionEnv "$CMD_WRAPPER_SESSION_ID")',
                'eval "$session_env"',
                'echo "=== DRY-RUN CONFIG DIFF (NOT COMMITTED) ==="',
                "if /opt/vyatta/sbin/my_cli_shell_api sessionChanged; then",
                "  /opt/vyatta/sbin/my_cli_shell_api showConfig --show-show-defaults --show-context-diff",
                "else",
                '  echo "No configuration changes."',
                "fi",
                '"$CMD" discard',
            ]
        )
    else:
        lines.extend(
            [
                'if [ -n "$(find /var/run -maxdepth 1 -name \'confirm*\' 2>/dev/null)" ]; then',
                '  echo "ERROR: Another commit-confirm is already pending — aborting" >&2',
                "  exit 1",
                "fi",
                'echo "=== ARMING COMMIT-CONFIRM ROLLBACK TIMER ==="',
                f'sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=commit-confirm --minutes={minutes}"',
                'echo "=== COMMITTING ==="',
                'if ! "$CMD" commit; then',
                '  echo "ERROR: commit failed — disarming rollback timer" >&2',
                '  sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=confirm" || true',
                "  exit 1",
                "fi",
                'echo "=== COMMIT SUCCEEDED ==="',
            ]
        )
    return "\n".join(lines) + "\n"


def cmd_apply(args: argparse.Namespace) -> int:
    if not (2 <= args.minutes <= 30):
        raise ValueError("--minutes must be between 2 and 30")

    router_ip, vars_dict = load_inventory()
    target = ssh_target(args.ssh_host)
    parsed_commands = parse_edgeos_commands(pathlib.Path(args.commands_file))

    if not args.dry_run:
        live_lines = fetch_live_config(target)
        backup_path = save_secure_backup(live_lines)
        print(f"Saved pre-change backup (0600) to {backup_path}")

    inner_script = build_inner_script(parsed_commands, dry_run=args.dry_run, minutes=args.minutes)

    # Upload to a private mktemp file on the router and execute under sg vyattacfg
    mk = subprocess.run(
        [*SSH_BASE, target, "f=$(mktemp /tmp/edgeos-apply.XXXXXX) && chmod 700 \"$f\" && echo \"$f\""],
        check=True,
        capture_output=True,
        text=True,
    )
    remote_path = mk.stdout.strip().splitlines()[-1].strip()
    if not remote_path.startswith("/tmp/edgeos-apply."):
        raise RuntimeError(f"Unexpected remote temp path: {remote_path!r}")

    try:
        subprocess.run(
            [*SSH_BASE, target, f"cat > {shlex.quote(remote_path)}"],
            input=inner_script,
            text=True,
            check=True,
        )
        run_cmd = f"sg vyattacfg -c {shlex.quote(f'bash {remote_path}')}"
        if args.dry_run:
            subprocess.run([*SSH_BASE, target, run_cmd], check=True)
            return 0

        print(f"Committing {len(parsed_commands)} commands with commit-confirm {args.minutes}m...")
        subprocess.run(
            [*SSH_BASE, "-tt", target, run_cmd],
            input="y\n",
            text=True,
            check=True,
        )
    finally:
        subprocess.run(
            [*SSH_BASE, target, f"rm -f {shlex.quote(remote_path)}"],
            check=False,
            capture_output=True,
        )

    # Automated smoke tests before confirming
    run_smoke_tests(target, router_ip, vars_dict.get("site_domain", ""))

    # Confirm & save
    print("=== All smoke tests passed — confirming & saving ===")
    subprocess.run(
        [
            *SSH_BASE,
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
    p_apply.add_argument("--dry-run", action="store_true", help="Preview EdgeOS context diff without committing")
    p_apply.add_argument("--minutes", type=int, default=5, help="commit-confirm rollback timer (2-30, default: 5)")
    p_apply.add_argument("--ssh-host", help="Override SSH target (default: admin@<ansible_host>)")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
