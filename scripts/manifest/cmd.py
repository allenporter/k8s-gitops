"""Library for running shell commands."""

import asyncio
import logging
import subprocess
import shlex


_LOGGER = logging.getLogger(__name__)


class CommandException(Exception):
    """Error while running a command."""


async def run_piped_commands(cmds: list[list[str]]) -> str:
    """Run a set of commands, piping output between them, returnign stdout"""
    stdin = None
    out = None
    for cmd in cmds:
        cmd_text = " ".join([shlex.quote(arg) for arg in cmd])
        proc = await asyncio.create_subprocess_shell(
            cmd_text,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = await proc.communicate(stdin)
        if proc.returncode:
            if out:
                _LOGGER.error(out.decode("utf-8"))
            if err:
                _LOGGER.error(err.decode("utf-8"))
            raise CommandException(
                "Subprocess failed %s with return code %s, see error log"
                % (cmd_text, proc.returncode)
            )
        stdin = out
    return out.decode("utf-8")


async def run_command(cmd: list[str]) -> str:
    """Run the specified command and return stdout."""
    return await run_piped_commands([cmd])
