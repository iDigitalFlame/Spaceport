#!/usr/bin/dash
################################
### iDigitalFlame  2016-2025 ###
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
## System Profile Configuration
#
# Copyright (C) 2016 - 2025 iDigitalFlame
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

if [ $USER = "root" ]; then
    export PS1="\[\e[31m\][\[\e[m\]\[\e[38;5;172m\]\u\[\e[m\] ~ ᐅ \[\e[38;5;214m\]\W\[\e[m\]\[\e[31m\]]\[\e[m\]\\$ "
fi

export ERRFILE="/dev/null"

# Disable Telemetry
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export POWERSHELL_TELEMETRY_OPTOUT=1

export NO_AT_BRIDGE=1
export SCREENRC="${HOME}/.screen/screenrc"
export GTK_RC_FILES="${HOME}/.config/gtk-1.0/gtkrc"
export GTK2_RC_FILES="${HOME}/.config/gtk-2.0/gtkrc"
export _JAVA_OPTIONS=-Djava.util.prefs.userRoot="${HOME}/.config/java"

# *Just Wayland Things*
export XDG_CURRENT_DESKTOP=sway
export QT_QPA_PLATFORM="wayland;xcb"
export _JAVA_AWT_WM_NONREPARENTING="1"
export ELECTRON_OZONE_PLATFORM_HINT="wayland"

# Python Configuration
export PYTHONUTF8=1
export PYTHON_COLORS=1
export PYTHONOPTIMIZE=2
export PYTHONCOERCECLOCALE="en_US.UTF-8"
export PYTHONPYCACHEPREFIX="/var/cache/python"
export PYTHONUSERBASE="${HOME}/.local/lib/python"

# XDG User Items Export
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

if ! [ -d "${PYTHONUSERBASE}/bin" ] && [ ! "$USER" = "root" ]; then
    mkdir -p "${PYTHONUSERBASE}/bin" 2> /dev/null
fi

PATH=/usr/lib/smd/bin:/usr/local/bin:$PATH:${PYTHONUSERBASE}/bin
export PATH

if ! [ -d "${XDG_RUNTIME_DIR}/qt" ]; then
    mkdir "${XDG_RUNTIME_DIR}/qt" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/gtk" ]; then
    mkdir "${XDG_RUNTIME_DIR}/gtk" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/mesa" ]; then
    mkdir "${XDG_RUNTIME_DIR}/mesa" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/slack" ]; then
    mkdir "${XDG_RUNTIME_DIR}/slack" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/screen" ]; then
    mkdir "${XDG_RUNTIME_DIR}/screen" 2> /dev/null
    chmod 0700 "${XDG_RUNTIME_DIR}/screen" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/discord" ]; then
    mkdir "${XDG_RUNTIME_DIR}/discord" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/firefox" ]; then
    mkdir "${XDG_RUNTIME_DIR}/firefox" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/mesa_db" ]; then
    mkdir "${XDG_RUNTIME_DIR}/mesa_db" 2> /dev/null
fi
if ! [ -d "${XDG_RUNTIME_DIR}/chromium_cache" ]; then
    mkdir "${XDG_RUNTIME_DIR}/chromium_cache" 2> /dev/null
fi
