#!/usr/bin/bash
# User Profile Defaults Script
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

umask 027

export PIP_USER=yes
export LIBGL_DRI3_DISABLE=1 # Use to disable DRI3, remove line if causes issues. (linked to X11 conf file).
export PYTHONUSERBASE="$HOME/.local/lib/python"

if [ -d "$HOME/.local/bin" ] && [ $UID -ne 0 ]; then
    PATH=$PATH:$HOME/.local/bin
fi

if [ ! -d "$PYTHONUSERBASE/bin" ] && [ $UID -ne 0 ]; then
    mkdir -p "$PYTHONUSERBASE/bin" 2> /dev/null
fi

PATH=/usr/lib/smd/bin:/usr/local/bin:$PATH:$PYTHONUSERBASE/bin
export PATH

if [ ! -d "/tmp/.usercache/$USER" ]; then
    mkdir "/tmp/.usercache/$USER" 2> /dev/null
fi

if [ -d "$HOME/.surf" ]; then
    rm -rf "$HOME/.surf/cache" 2> /dev/null
    mkdir "/tmp/.usercache/$USER/surf" 2> /dev/null
    ln -s "/tmp/.usercache/$USER/surf" "$HOME/.surf/cache" 2> /dev/null
fi
