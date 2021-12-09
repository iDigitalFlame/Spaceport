#!/usr/bin/bash
# Theme Icons Configuration
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

if [ $UID -ne 0 ]; then
    printf "[!] Only root can do this!\n"
    exit 1
fi

if ! [ -d "/usr/share/icons/DarkSky" ]; then
    bash "/usr/share/themes/DarkSky/build-icons.sh"
fi

find "/usr/share/icons" -xdev -xtype l -delete
find "/usr/share/themes" -xdev -xtype l -delete
find "/usr/share/icons/DarkSky" -xdev -type f -name .directory -delete
find "/usr/share/themes/DarkSky" -xdev -type f -name .directory -delete
