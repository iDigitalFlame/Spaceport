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
## Cache and Links Configuration
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

rm    "/etc/.updated" "/etc/.pwd.lock"         2> /dev/null
rmdir "/etc/NetworkManager/system-connections" 2> /dev/null

linkcheck "/etc/ld.so.cache"                       "/var/cache/ld.so.cache"
linkcheck "/etc/pacman.d/gnupg"                    "/var/db/pacman/gnupg"
linkcheck "/etc/cups/printers.conf"                "/var/cache/cups/printers.conf"
linkcheck "/etc/pacman.d/mirrorlist"               "/var/cache/pacman/mirrorlist"
linkcheck "/etc/NetworkManager/system-connections" "/var/lib/NetworkManager/system-connections"

chmod 0644 "/var/cache/ld.so.cache"
chmod 0444 "/var/cache/pacman/mirrorlist"
chmod 0600 "/var/cache/cups/printers.conf"
chmod 0700 "/var/lib/NetworkManager/system-connections"
chmod 0600 "/var/lib/NetworkManager/system-connections/"* 2> /dev/null

chown -R root:root "/var/lib/NetworkManager/system-connections"

chown -R root:root "/var/cache/fontconfig"
chmod -R 2755      "/var/cache/fontconfig"
chmod    2644      "/var/cache/fontconfig/"* 2> /dev/null

chown -R alpm:root "/var/cache/pacman/pkg"
chmod -R 2750      "/var/cache/pacman/pkg"
chmod    2660      "/var/cache/pacman/pkg/"* 2> /dev/null

chown -R root:root "/var/lib/pacman/sync"
chmod    2755      "/var/lib/pacman/sync"
chmod    2644      "/var/lib/pacman/sync/"*.db 2> /dev/null

chown -hR root:root "/var/lib/pacman/local"
find "/var/lib/pacman/local" -xdev -type d -exec chmod 2755 {} \;
find "/var/lib/pacman/local" -xdev -type f -exec chmod 0644 {} \;

chown -R root:root "/var/cache/ldconfig"
chmod    2700      "/var/cache/ldconfig"

chown -R root:makepkg "/var/cache/makepkg"
chmod    3775         "/var/cache/makepkg"
chmod    3640         "/var/cache/makepkg/"* 2> /dev/null

chown root:root "/var/cache/python"
chmod 3777      "/var/cache/python"

chown -R root:smd "/var/cache/python/usr/lib/smd"
chmod    2770     "/var/cache/python/usr/lib/smd"
