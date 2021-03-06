#!/usr/bin/bash
# Cache Links Configuration
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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
chown root:root -R "/var/lib/NetworkManager/system-connections"

chmod 2755 -R "/var/cache/fontconfig"
chmod 644 /var/cache/fontconfig/*
chown root:root -R "/var/cache/fontconfig"

chmod 2750 -R "/var/cache/pacman/pkg"
chmod 640 /var/cache/pacman/pkg/*
chown root:root -R "/var/cache/pacman/pkg"

chmod 2755 "/var/lib/pacman/sync"
chmod 644 /var/lib/pacman/sync/*
chown root:root -R "/var/lib/pacman/sync"

chmod 2755 "/var/lib/pacman/local"
chown root:root -R "/var/lib/pacman/local"

chmod 2700 "/var/cache/ldconfig"
chown root:root -R "/var/cache/ldconfig"
