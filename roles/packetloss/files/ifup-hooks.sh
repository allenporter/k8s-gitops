#!/bin/sh
# Script for ifupdown compatibility https://netplan.io/faq/

for d in up post-up; do
    hookdir=/etc/network/if-${d}.d
    [ -e $hookdir ] && /bin/run-parts $hookdir
done
exit 0
