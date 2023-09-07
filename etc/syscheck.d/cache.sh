#!/usr/bin/dash
# Cache Links Configuration
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

rm "/etc/ld.so.cache" 2> /dev/null
rm "/etc/cups/printers.conf" 2> /dev/null
rm -f "/etc/NetworkManager/system-connections" 2> /dev/null
rmdir "/etc/NetworkManager/system-connections" 2> /dev/null
rm "/var/lib/NetworkManager/system-connections/system-connections" 2> /dev/null

ln -s "/var/cache/ld.so.cache" "/etc/ld.so.cache" 2> /dev/null
ln -s "/var/cache/cups/printers.conf" "/etc/cups/printers.conf" 2> /dev/null
ln -s "/var/lib/NetworkManager/system-connections" "/etc/NetworkManager/system-connections" 2> /dev/null

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
