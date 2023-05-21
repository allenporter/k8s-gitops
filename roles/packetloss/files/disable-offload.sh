#!/bin/sh

set -e

ETHTOOL=/sbin/ethtool
test -x $ETHTOOL || exit 1

[ "$IFACE" != "lo" ] || exit 0

# Exit if offload already disabled
${ETHTOOL} -k ${IFACE} | grep "segmentation-offload: on" || exit 0

echo "Disabling offload for ${IFACE}"
${ETHTOOL} -K ${IFACE} gso off
${ETHTOOL} -K ${IFACE} tso off
${ETHTOOL} --offload ${IFACE} tx off
echo "UPDATED"
