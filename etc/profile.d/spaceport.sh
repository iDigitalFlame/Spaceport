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
## System Profile Configuration
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

umask 0027

export ERRFILE="/dev/null"

# Disable telemetry
export POWERSHELL_TELEMETRY_OPTOUT=1
export DOTNET_CLI_TELEMETRY_OPTOUT=1

export NO_AT_BRIDGE=1
export SCREENRC="${HOME}/.screen/screenrc"
export PYTHONUSERBASE="${HOME}/.local/lib/python"
export GTK_RC_FILES="${HOME}/.config/gtk-1.0/gtkrc"
export GTK2_RC_FILES="${HOME}/.config/gtk-2.0/gtkrc"
export _JAVA_OPTIONS=-Djava.util.prefs.userRoot="${HOME}/.config/java"

# *Just Wayland Things*
export QT_QPA_PLATFORM="wayland;xcb"
export _JAVA_AWT_WM_NONREPARENTING="1"

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

if ! [ -d "${PYTHONUSERBASE}/bin" ] && [ ! "$USER" = "root" ]; then
    mkdir -p "${PYTHONUSERBASE}/bin" 2> /dev/null
fi

PATH=/usr/lib/smd/bin:/usr/local/bin:$PATH:${PYTHONUSERBASE}/bin
export PATH

if ! [ -d "/tmp/.usercache/${USER}" ]; then
    mkdir "/tmp/.usercache/${USER}" 2> /dev/null
fi

if ! [ -d "/tmp/.usercache/${USER}/mesa" ]; then
    mkdir "/tmp/.usercache/${USER}/mesa" 2> /dev/null
fi
