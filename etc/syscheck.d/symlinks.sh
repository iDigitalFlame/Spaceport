#!/usr/bin/bash
# Symlinks Configuration
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

if [ $UID -ne 0 ]; then
    printf "[!] Only root can do this!\n"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# CUPS Startup Link
ln -s "/usr/lib/systemd/system/cups.service" "/etc/systemd/system/multi-user.target.wants/cups.service" 2> /dev/null

# Firefox file Link
rm -f "/usr/lib/firefox/firefox.cfg" 2> /dev/null
ln -s "${BASE_DIR}/usr/lib/firefox/defaults/pref/firefox.cfg" "/usr/lib/firefox/firefox.cfg" 2> /dev/null

# Fontconfig Links
ln -s "/usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf" "/etc/fonts/conf.d/10-sub-pixel-rgb.conf" 2> /dev/null
ln -s "/usr/share/fontconfig/conf.avail/11-lcdfilter-light.conf" "/etc/fonts/conf.d/11-lcdfilter-light.conf" 2> /dev/null
ln -s "/usr/share/fontconfig/conf.avail/70-yes-bitmaps.conf" "/etc/fonts/conf.d/70-yes-bitmaps.conf" 2> /dev/null

# Setup Links for Bin
for module in $(/usr/bin/python3 ${BASE_DIR}/usr/lib/smd/bin/powerctl modules 2> /dev/null); do
    rm -f "/usr/local/bin/${module}" 2> /dev/null
    rm -f "/usr/local/bin/${module}ctl" 2> /dev/null
    ln -s "${BASE_DIR}/usr/lib/smd/bin/powerctl" "/usr/local/bin/${module}" 2> /dev/null
    ln -s "${BASE_DIR}/usr/lib/smd/bin/powerctl" "/usr/local/bin/${module}ctl" 2> /dev/null
done
