#!/usr/bin/dash
# User Profile Defaults Script
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

umask 0027

export PIP_USER=yes
export ERRFILE="/dev/null"

# Use to disable DRI3, remove line if causes issues. (linked to X11 conf file).
export LIBGL_DRI3_DISABLE=1

export SCREENRC="${HOME}/screen/screenrc"
export PYTHONUSERBASE="${HOME}/.local/lib/python"
export GTK_RC_FILES="${HOME}/.config/gtk-1.0/gtkrc"
export GTK2_RC_FILES="${HOME}/.config/gtk-2.0/gtkrc"
export _JAVA_OPTIONS=-Djava.util.prefs.userRoot="${HOME}/.config/java"

# XDG User items export
export XDG_DESKTOP_DIR="${HOME}"
export XDG_CACHE_HOME="${HOME}/.cache"
export XDG_CONFIG_HOME="${HOME}/.config"
export XDG_PICTURES_DIR="${HOME}/Pictures"
export XDG_DATA_HOME="${HOME}/.local/share"
export XDG_DOWNLOAD_DIR="${HOME}/Downloads"
export XDG_DOCUMENTS_DIR="${HOME}/Documents"
export XDG_STATE_HOME="${HOME}/.local/share"
export XDG_MUSIC_DIR="${HOME}/Documents/Music"
export XDG_VIDEOS_DIR="${HOME}/Documents/Videos"
export XDG_PUBLICSHARE_DIR="${HOME}/Documents/Public"
export XDG_TEMPLATES_DIR="${HOME}/Documents/Templates"
export XDG_RUNTIME_DIR="/run/user/$(/usr/bin/id --user)"

if [ -d "${HOME}/.local/bin" ] && [ ! "$USER" = "root" ]; then
    PATH=$PATH:${HOME}/.local/bin
fi

if [ ! -d "${PYTHONUSERBASE}/bin" ] && [ ! "$USER" = "root" ]; then
    mkdir -p "${PYTHONUSERBASE}/bin" 2> /dev/null
fi

PATH=/usr/lib/smd/bin:/usr/local/bin:$PATH:${PYTHONUSERBASE}/bin
export PATH

if [ ! -d "/tmp/.usercache/${USER}" ]; then
    mkdir "/tmp/.usercache/${USER}" 2> /dev/null
fi

if [ -d "${HOME}/.surf" ]; then
    rm -rf "${HOME}/.surf/cache" 2> /dev/null
    mkdir "/tmp/.usercache/${USER}/surf" 2> /dev/null
    ln -s "/tmp/.usercache/${USER}/surf" "${HOME}/.surf/cache" 2> /dev/null
fi
