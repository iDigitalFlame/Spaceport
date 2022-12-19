#!/usr/bin/dash
# Pipewire/Wireplumber Symlinks Configuration
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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

rm -rf "/etc/pipewire"
rm -rf "/etc/wireplumber/common"
rm -rf "/etc/wireplumber/scripts"

rm -f "/etc/wireplumber/policy.lua.d/00-functions.lua"
rm -f "/etc/wireplumber/policy.lua.d/90-enable-all.lua"

rm -f "/etc/wireplumber/bluetooth.lua.d/00-functions.lua"
rm -f "/etc/wireplumber/bluetooth.lua.d/90-enable-all.lua"
rm -f "/etc/wireplumber/bluetooth.lua.d/30-bluez-monitor.lua"

rm -f "/etc/wireplumber/main.lua.d/00-functions.lua"
rm -f "/etc/wireplumber/main.lua.d/90-enable-all.lua"
rm -f "/etc/wireplumber/main.lua.d/30-v4l2-monitor.lua"
rm -f "/etc/wireplumber/main.lua.d/30-alsa-monitor.lua"
rm -f "/etc/wireplumber/main.lua.d/20-default-access.lua"
rm -f "/etc/wireplumber/main.lua.d/30-libcamera-monitor.lua"

ln -ns "/usr/share/pipewire" "/etc/pipewire"
ln -ns "/usr/share/wireplumber/common" "/etc/wireplumber/common"
ln -ns "/usr/share/wireplumber/scripts" "/etc/wireplumber/scripts"

ln -ns "/usr/share/wireplumber/policy.lua.d/00-functions.lua" "/etc/wireplumber/policy.lua.d/00-functions.lua"
ln -ns "/usr/share/wireplumber/policy.lua.d/90-enable-all.lua" "/etc/wireplumber/policy.lua.d/90-enable-all.lua"

ln -ns "/usr/share/wireplumber/bluetooth.lua.d/00-functions.lua" "/etc/wireplumber/bluetooth.lua.d/00-functions.lua"
ln -ns "/usr/share/wireplumber/bluetooth.lua.d/90-enable-all.lua" "/etc/wireplumber/bluetooth.lua.d/90-enable-all.lua"
ln -ns "/usr/share/wireplumber/bluetooth.lua.d/30-bluez-monitor.lua" "/etc/wireplumber/bluetooth.lua.d/30-bluez-monitor.lua"

ln -ns "/usr/share/wireplumber/main.lua.d/00-functions.lua" "/etc/wireplumber/main.lua.d/00-functions.lua"
ln -ns "/usr/share/wireplumber/main.lua.d/90-enable-all.lua" "/etc/wireplumber/main.lua.d/90-enable-all.lua"
ln -ns "/usr/share/wireplumber/main.lua.d/30-v4l2-monitor.lua" "/etc/wireplumber/main.lua.d/30-v4l2-monitor.lua"
ln -ns "/usr/share/wireplumber/main.lua.d/30-alsa-monitor.lua" "/etc/wireplumber/main.lua.d/30-alsa-monitor.lua"
ln -ns "/usr/share/wireplumber/main.lua.d/20-default-access.lua" "/etc/wireplumber/main.lua.d/20-default-access.lua"
ln -ns "/usr/share/wireplumber/main.lua.d/30-libcamera-monitor.lua" "/etc/wireplumber/main.lua.d/30-libcamera-monitor.lua"

chown -hR root:root "/etc/pipewire"
chown -hR root:root "/etc/wireplumber"

chmod -R 0555 "/etc/pipewire"
chmod -R 0555 "/etc/wireplumber"

find "/etc/pipewire" -type f -exec chmod 0444 {} \;
find "/etc/wireplumber" -type f -exec chmod 0444 {} \;
find "/usr/share/pipewire" -type f -exec chmod 0444 {} \;
