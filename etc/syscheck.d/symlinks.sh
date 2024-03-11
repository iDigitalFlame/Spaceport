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
    echo "Error: root is required!"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Udev Device Names Link
linkcheck "/etc/udev/rules.d/80-net-setup-link.rules" "/dev/null"

# Firefox file Link
linkcheck "/usr/lib/librewolf/browser/extensions" "/usr/lib/firefox/browser/extensions"
linkcheck "/usr/lib/firefox/firefox.cfg" "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg"
linkcheck "/usr/lib/librewolf/librewolf.cfg" "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg"
linkcheck "/usr/lib/librewolf/defaults/pref/librewolf.cfg" "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg"

chown root:root "/usr/lib/firefox/firefox.cfg"
chown root:root "/usr/lib/librewolf/librewolf.cfg"
chown root:root "/usr/lib/librewolf/defaults/pref/librewolf.cfg"
chmod 0444 "/usr/lib/firefox/firefox.cfg"
chmod 0444 "/usr/lib/librewolf/librewolf.cfg"
chmod 0444 "/usr/lib/librewolf/defaults/pref/librewolf.cfg"

# Less Syskeys
linkcheck "/etc/syslesskey" "/etc/sysless"
linkcheck "/usr/local/etc/syslesskey" "/etc/sysless"

chmod 0444 "/etc/sysless"
chmod 0444 "/etc/syslesskey"
chmod 0444 "/usr/local/etc/syslesskey"

# Fontconfig Links
linkcheck "/etc/fonts/conf.d/70-yes-bitmaps.conf" "/usr/share/fontconfig/conf.avail/70-yes-bitmaps.conf"
linkcheck "/etc/fonts/conf.d/10-sub-pixel-rgb.conf" "/usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf"
linkcheck "/etc/fonts/conf.d/11-lcdfilter-light.conf" "/usr/share/fontconfig/conf.avail/11-lcdfilter-light.conf"

# Setup Links for Bin
for module in $(/usr/bin/python3 ${BASE_DIR}/usr/lib/smd/bin/powerctl modules 2> /dev/null | grep -v log); do
    linkcheck "/usr/local/bin/${module}" "${BASE_DIR}/usr/lib/smd/bin/powerctl"
    linkcheck "/usr/local/bin/${module}ctl" "${BASE_DIR}/usr/lib/smd/bin/powerctl"
    chown root:root "/usr/local/bin/${module}"
    chown root:root "/usr/local/bin/${module}ctl"
    chmod 0555 "/usr/local/bin/${module}"
    chmod 0555 "/usr/local/bin/${module}ctl"
done
