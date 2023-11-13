#!/usr/bin/dash
################################
### iDigitalFlame  2016-2024 ###
#                              #
#            -/`               #
#            -yy-   :/`        #
#         ./-shho`:so`         #
#    .:- /syhhhh//hhs` `-`     #
#   :ys-:shhhhhhshhhh.:o- `    #
#   /yhsoshhhhhhhhhhhyho`:/.   #
#   `:yhyshhhhhhhhhhhhhh+hd:   #
#     :yssyhhhhhyhhhhhhhhdd:   #
#    .:.oyshhhyyyhhhhhhddd:    #
#    :o+hhhhhyssyhhdddmmd-     #
#     .+yhhhhyssshdmmddo.      #
#       `///yyysshd++`         #
#                              #
########## SPACEPORT ###########
### Spaceport + SMD
## Symlinks Configuration
#
# Copyright (C) 2016 - 2024 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

if ! [ "$USER" = "root" ]; then
    echo "[!] Only root can do this!"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Udev Device Names Link
if ! [ -h "/etc/udev/rules.d/80-net-setup-link.rules" ]; then
    rm -f "/etc/udev/rules.d/80-net-setup-link.rules"
    ln -s "/dev/null" "/etc/udev/rules.d/80-net-setup-link.rules" 2> /dev/null
fi

# CUPS Startup Link
ln -s "/usr/lib/systemd/system/cups.service" "/etc/systemd/system/multi-user.target.wants/cups.service" 2> /dev/null

# Firefox file Link
rm -f "/usr/lib/firefox/firefox.cfg"
rm -f "/usr/lib/librewolf/librewolf.cfg"
rm -f "/usr/lib/librewolf/browser/extensions"
ln -s "/usr/lib/firefox/browser/extensions" "/usr/lib/librewolf/browser/extensions"
ln -s "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg" "/usr/lib/firefox/firefox.cfg"
ln -s "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg" "/usr/lib/librewolf/librewolf.cfg"
ln -s "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg" "/usr/lib/librewolf/defaults/pref/librewolf.cfg" 2> /dev/null
chown root:root "/usr/lib/firefox/firefox.cfg"
chown root:root "/usr/lib/librewolf/librewolf.cfg"
chown root:root "/usr/lib/librewolf/defaults/pref/librewolf.cfg"
chmod 0444 "/usr/lib/firefox/firefox.cfg"
chmod 0444 "/usr/lib/librewolf/librewolf.cfg"
chmod 0444 "/usr/lib/librewolf/defaults/pref/librewolf.cfg"

# Less Syskeys
ln -s "/etc/sysless" "/etc/syslesskey" 2> /dev/null
ln -s "/etc/sysless" "/usr/local/etc/syslesskey" 2> /dev/null
chmod 0444 "/etc/sysless"
chmod 0444 "/etc/syslesskey"
chmod 0444 "/usr/local/etc/syslesskey"

# Fontconfig Links
ln -s "/usr/share/fontconfig/conf.avail/70-yes-bitmaps.conf" "/etc/fonts/conf.d/70-yes-bitmaps.conf" 2> /dev/null
ln -s "/usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf" "/etc/fonts/conf.d/10-sub-pixel-rgb.conf" 2> /dev/null
ln -s "/usr/share/fontconfig/conf.avail/11-lcdfilter-light.conf" "/etc/fonts/conf.d/11-lcdfilter-light.conf" 2> /dev/null

# Setup Links for Bin
for module in $(/usr/bin/python3 ${BASE_DIR}/usr/lib/smd/bin/powerctl modules 2> /dev/null | grep -v log); do
    rm -f "/usr/local/bin/${module}"
    rm -f "/usr/local/bin/${module}ctl"
    ln -s "${BASE_DIR}/usr/lib/smd/bin/powerctl" "/usr/local/bin/${module}"
    ln -s "${BASE_DIR}/usr/lib/smd/bin/powerctl" "/usr/local/bin/${module}ctl"
    chown root:root "/usr/local/bin/${module}"
    chown root:root "/usr/local/bin/${module}ctl"
    chmod 0555 "/usr/local/bin/${module}"
    chmod 0555 "/usr/local/bin/${module}ctl"
done
