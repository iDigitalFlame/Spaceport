#!/usr/bin/dash
################################
### iDigitalFlame  2016-2026 ###
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
# Copyright (C) 2016 - 2026 iDigitalFlame
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

# Disable Telemetry
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export POWERSHELL_TELEMETRY_OPTOUT=1

# Screen
export SCREENRC="${HOME}/.config/screen/screenrc"
export SCREENDIR="${XDG_RUNTIME_DIR}/screen"

# GTK
export GTK_RC_FILES="${HOME}/.config/gtk-1.0/gtkrc"
export GTK2_RC_FILES="${HOME}/.config/gtk-2.0/gtkrc"

# GTK / GDK
export GDK_SCALE=0.95
export GDK_DPI_SCALE=0.95

# Qt
export QT_QPA_PLATFORM="wayland;xcb"
export QT_ENABLE_HIGHDPI_SCALING=1
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# Java
export _JAVA_OPTIONS=-Djava.util.prefs.userRoot="${HOME}/.config/java"
export _JAVA_AWT_WM_NONREPARENTING="1"

# Python
export PYTHONUTF8=1
export PYTHON_COLORS=1
export PYTHON_HISTORY="${HOME}/.cache/python_history"
export PYTHONOPTIMIZE=2
export PYTHONUSERBASE="${HOME}/.local/lib/python"
export PYTHONCOERCECLOCALE="en_US.UTF-8"
export PYTHONPYCACHEPREFIX="/var/cache/python"

# XDG User Items Export
export XDG_DATA_HOME="${HOME}/.local/share"
export XDG_MUSIC_DIR="${HOME}/Documents/Music"
export XDG_CACHE_HOME="${HOME}/.cache"
export XDG_STATE_HOME="${HOME}/.local/share"
export XDG_VIDEOS_DIR="${HOME}/Documents/Videos"
export XDG_CONFIG_HOME="${HOME}/.config"
export XDG_DESKTOP_DIR="${HOME}"
export XDG_RUNTIME_DIR="/run/user/$(/usr/bin/id --user)"
export XDG_PICTURES_DIR="${HOME}/Pictures"
export XDG_DOWNLOAD_DIR="${HOME}/Downloads"
export XDG_DOCUMENTS_DIR="${HOME}/Documents"
export XDG_TEMPLATES_DIR="${HOME}/Documents/Templates"
export XDG_PUBLICSHARE_DIR="${HOME}/Documents/Public"

# SSH
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/gcr/ssh"

# Wayland Hints
export XDG_CURRENT_DESKTOP="sway"
export ELECTRON_OZONE_PLATFORM_HINT="wayland"

# Make / AUR
export PKGDEST="/var/cache/makepkg"
export SRCDEST="${XDG_RUNTIME_DIR}/temp/aur/src"
export BUILDDIR="${XDG_RUNTIME_DIR}/temp/aur/build"

# Misc
export ERRFILE="/dev/null"
export NO_AT_BRIDGE=1

if ! [ "$USER" = "root" ] && [ -d "${HOME}/.local/bin" ]; then
    PATH=$PATH:${HOME}/.local/bin
fi

export PATH=/usr/lib/smd/bin:/usr/local/bin:$PATH:${PYTHONUSERBASE}/bin
