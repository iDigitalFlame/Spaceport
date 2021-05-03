#!/usr/bin/bash
# System Management Daemon - Spaceport
# iDigitalFlame
#
# SYmlinks Configuration.

if [ $UID -ne 0 ]; then
    printf "[!] Only root can do this!\n"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Firefox file symlink
rm -f "/usr/lib/firefox/firefox.cfg" 2> /dev/null
ln -s "$BASE_DIR/usr/lib/firefox/defaults/pref/firefox.cfg" "/usr/lib/firefox/firefox.cfg"

# Setup Symlinks for Bin
for module in $(/usr/bin/python3 $BASE_DIR/bin/powerctl modules 2> /dev/null); do
    ln -s "$BASE_DIR/bin/powerctl" "/usr/local/bin/$module" 2> /dev/null
    ln -s "$BASE_DIR/bin/powerctl" "/usr/local/bin/${module}ctl" 2> /dev/null
done
