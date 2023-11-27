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
    echo "[!] Only root can do this!"
    exit 1
fi

rm -f "/etc/ld.so.cache"
rm -f "/etc/cups/printers.conf"
rm -f "/etc/NetworkManager/system-connections"
rmdir "/etc/NetworkManager/system-connections" 2> /dev/null
rm -f "/var/lib/NetworkManager/system-connections/system-connections"

ln -sT "/var/cache/ld.so.cache" "/etc/ld.so.cache"
ln -sT "/var/cache/cups/printers.conf" "/etc/cups/printers.conf"
ln -sT "/var/lib/NetworkManager/system-connections" "/etc/NetworkManager/system-connections"

chmod 0644 "/var/cache/ld.so.cache"
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
chmod 2640 /var/cache/pacman/pkg/*
chown -R root:root "/var/cache/pacman/pkg"

chmod 2755 "/var/lib/pacman/sync"
chmod 2644 /var/lib/pacman/sync/*
chown -R root:root "/var/lib/pacman/sync"

chmod 2755 "/var/lib/pacman/local"
chown -R root:root "/var/lib/pacman/local"

chmod 2700 "/var/cache/ldconfig"
chown -R root:root "/var/cache/ldconfig"
