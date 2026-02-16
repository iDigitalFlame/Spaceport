#!/usr/bin/dash
################################
### iDigitalFlame  2016-2026 ###
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
# Copyright (C) 2016 - 2026 iDigitalFlame
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
if [ -z "$SYSCONFIG" ]; then
    echo "Error: SYSCONFIG not found!"
    exit 1
fi

# Firefox Links
linkcheck "/etc/librewolf"                                 "/etc/firefox"
linkcheck "/usr/lib/firefox/firefox.cfg"                   "${SYSCONFIG}/usr/lib/firefox/defaults/pref/firefox.cfg"
linkcheck "/usr/lib/librewolf/librewolf.cfg"               "${SYSCONFIG}/usr/lib/firefox/defaults/pref/firefox.cfg"
linkcheck "/usr/lib/librewolf/browser/extensions"          "/usr/lib/firefox/browser/extensions"
linkcheck "/usr/lib/librewolf/defaults/pref/librewolf.cfg" "${SYSCONFIG}/usr/lib/firefox/defaults/pref/firefox.cfg"

# Less/Syskey Links
linkcheck "/etc/syslesskey"           "/etc/sysless"
linkcheck "/usr/local/etc/syslesskey" "/etc/sysless"

# Fontconfig Links
linkcheck "/etc/fonts/conf.d/70-yes-bitmaps.conf"     "/usr/share/fontconfig/conf.avail/70-yes-bitmaps.conf"
linkcheck "/etc/fonts/conf.d/10-sub-pixel-rgb.conf"   "/usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf"
linkcheck "/etc/fonts/conf.d/11-lcdfilter-light.conf" "/usr/share/fontconfig/conf.avail/11-lcdfilter-light.conf"

# Null Blocks Links
linkcheck "/etc/tmpfiles.d/audit.conf"                       "/dev/null"
linkcheck "/etc/tmpfiles.d/polkit-tmpfiles.conf"             "/dev/null"
linkcheck "/etc/udev/rules.d/80-net-setup-link.rules"        "/dev/null"
linkcheck "/etc/pacman.d/hooks/update-desktop-database.hook" "/dev/null"

# XDG Portal Links
linkcheck "/etc/xdg-desktop-portal/gtk-portals.conf"  "/etc/xdg-desktop-portal/portals.conf"
linkcheck "/etc/xdg-desktop-portal/sway-portals.conf" "/etc/xdg-desktop-portal/portals.conf"

# SMD PowerCTL Links
for i in $(/usr/bin/python3 -X pycache_prefix=/var/cache/python -OO ${SYSCONFIG}/usr/lib/smd/bin/powerctl modules 2> /dev/null | grep -v log); do
    linkcheck "/usr/local/bin/${i}"    "${SYSCONFIG}/usr/lib/smd/bin/powerctl"
    linkcheck "/usr/local/bin/${i}ctl" "${SYSCONFIG}/usr/lib/smd/bin/powerctl"
done
