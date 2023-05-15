#!/bin/bash
#
# Script to cleanup the pcap dump directoriy, preserving only the latest N files.

set -e

TCPDUMP_DIR="/var/lib/tcpdump"
# Files are rotated every hour, so this preserves one days worth of captures
FILES_TO_KEEP=24

cd ${TCPDUMP_DIR}
ls -tp | grep -v '/$' | tail -n +${FILES_TO_KEEP} | xargs -I {} rm {}
