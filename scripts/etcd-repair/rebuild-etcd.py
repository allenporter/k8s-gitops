#!/usr/bin/env python
"""Finds a busted etcd member and prints out the repair command."""

import logging
import os
import re
import subprocess


_LOGGER = logging.getLogger(__name__)


EXPECTED_MEMBERS = 3
FAILURE = r"Failed to get the status of endpoint ([a-z0-9:\.]+) \(.*"


def run(command, allow_failure=False):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    if proc.returncode:
        if allow_failure:
          return err.decode("utf-8") + out.decode("utf-8")
        _LOGGER.error(
            "Subprocess failed %s with return code %s", command, proc.returncode
        )
        _LOGGER.info(out.decode("utf-8"))
        _LOGGER.error(err.decode("utf-8"))
        return None
    return out.decode("utf-8")

def main():
  print("Gathering member list...")
  command = ["etcdctl", "member", "list"]
  members = run(command)
  targets = {}
  for line in members.splitlines():
    print(line)
    parts = line.split(",")
    etcdid = parts[0].strip()
    host = parts[2].strip()
    targets[etcdid] = host

  if len(targets) != EXPECTED_MEMBERS:
    raise Exception(f"Expected {EXPECTED_MEMBERS} but got: {members}")

  print("")
  print("Finding failed node...")
  command = ["etcdctl", "endpoint", "status"]
  status = run(command, allow_failure=True)
  failed = None
  for line in status.splitlines():
    print(line)
    match = re.match(FAILURE, line)
    if match:
      failed = match.group(1)
      continue
    parts = line.split(",")
    host = parts[0].strip()
    etcdid = parts[1].strip()
    if etcdid not in targets:
      raise Exception("Members found '{etcdid}' but not in {targets}")
    del targets[etcdid]
 
  if len(targets) != 1:
    raise Exception("Unable to reconcile which member has failed")

  (etcdid, host) = next(iter(targets.items()))
  if not failed.startswith(host):
    raise Exception(f"Unable to match failed host {failed} with members: {status}")
  (failed_host, port) = failed.split(":")

  print("")
  print(f"Determined failed node is {etcdid} at {host}. Run commands to repair:")
  print("")
  print(f"$ ansible-playbook cluster/etcd/rebuild-etcd.yml -l {failed_host} --extra-vars \"target={etcdid}\"")


if __name__ == "__main__":
  main()
