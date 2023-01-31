"""Library for running shell commands."""

import logging
import subprocess


_LOGGER = logging.getLogger(__name__)


class CommandException(Exception):
    """Error while running a command."""


def run_piped_commands(cmds: list[list[str]]) -> str:
    """Run a set of commands, piping output between them, returnign stdout"""
    stack = []
    procs = []
    for cmd in cmds:
        _LOGGER.debug(cmd)
        stdin = procs[-1].stdout if procs else None
        proc = subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE)
        procs.append(proc)
    if len(procs) > 1:
        for proc in procs[:-1]:
            proc.stdout.close()  # Allow SIGPIPE if proc exists
    (out, err) = procs[-1].communicate()
    if procs[-1].returncode:
        _LOGGER.info(out.decode("utf-8"))
        _LOGGER.error(err.decode("utf-8"))
        raise CommandException(
            "Subprocess failed %s with return code %s", cmds, procs[-1].returncode
        )
    return out.decode("utf-8")


def run_command(cmd: list[str]) -> str:
    """Run the specified command and return stdout."""
    return run_piped_commands([cmd])
