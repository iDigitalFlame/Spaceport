#!/usr/bin/bash
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Chrony Network Enable Script.

LANG='C'
STATUS=$2
INTERFACE=$1
CHRONY=$(which chronyc)

get_status() {
    [ "$(nmcli -t --fields STATE g)" = 'connected' ]
}

exec_chrony() {
    echo "Chrony going $1."
    exec $CHRONY -a $1
}

case "$STATUS" in
    up)
        exec_chrony online
    ;;
    vpn-up)
        exec_chrony online
    ;;
    down)
        get_status || exec_chrony offline
    ;;
    vpn-down)
        get_status || exec_chrony offline
    ;;
esac
