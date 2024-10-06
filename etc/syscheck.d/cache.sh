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
## Cache and Links Configuration
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

rm "/etc/.updated" 2> /dev/null
rm "/etc/.pwd.lock" 2> /dev/null
rmdir "/etc/NetworkManager/system-connections" 2> /dev/null

linkcheck "/etc/ld.so.cache" "/var/cache/ld.so.cache"
linkcheck "/etc/pacman.d/gnupg" "/var/db/pacman/gnupg"
linkcheck "/etc/pacman.d/mirrorlist" "/var/cache/pacman/mirrorlist"
linkcheck "/etc/cups/printers.conf" "/var/cache/cups/printers.conf"
linkcheck "/etc/NetworkManager/system-connections" "/var/lib/NetworkManager/system-connections"

chmod 0644 "/var/cache/ld.so.cache"
chmod 0444 "/var/cache/pacman/mirrorlist"
chmod 0600 "/var/cache/cups/printers.conf"
chmod 0700 "/var/lib/NetworkManager/system-connections"
chmod 0600 /var/lib/NetworkManager/system-connections/*

chown root:root "/var/cache/ld.so.cache"
chown root:cups "/var/cache/cups/printers.conf"
chown -R root:root "/var/lib/NetworkManager/system-connections"

chmod -R 2755 "/var/cache/fontconfig"
chmod 2644 /var/cache/fontconfig/*
chown -R root:root "/var/cache/fontconfig"

chmod -R 2750 "/var/cache/pacman/pkg"
chmod 2660 /var/cache/pacman/pkg/*
chown -R alpm:root "/var/cache/pacman/pkg"

chmod 2755 "/var/lib/pacman/sync"
chmod 2644 /var/lib/pacman/sync/*.db
chown -R root:root "/var/lib/pacman/sync"

chmod 2755 -R "/var/lib/pacman/local"
find "/var/lib/pacman/local" -type f -exec chmod 644 {} \;
chown -R root:root "/var/lib/pacman/local"

chmod 2700 "/var/cache/ldconfig"
chown -R root:root "/var/cache/ldconfig"

chmod 2775 "/var/cache/makepkg"
chmod 2660 /var/cache/makepkg/*
chown root:makepkg -R "/var/cache/makepkg"
