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
## User-specific Mount Configration
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

if ! [ "$USER" = "root" ] && [ -d "${XDG_RUNTIME_DIR}" ]; then
    # Make User Cache Dirs
    ! [ -d "${SRCDEST}" ]                  && mkdir -p "${SRCDEST}"                  2> /dev/null
    ! [ -d "${BUILDDIR}" ]                 && mkdir -p "${BUILDDIR}"                 2> /dev/null
    ! [ -d "${PYTHONUSERBASE}/bin" ]       && mkdir -p "${PYTHONUSERBASE}/bin"       2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/qt" ]       && mkdir    "${XDG_RUNTIME_DIR}/qt"       2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/gtk" ]      && mkdir    "${XDG_RUNTIME_DIR}/gtk"      2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/mesa" ]     && mkdir    "${XDG_RUNTIME_DIR}/mesa"     2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/slack" ]    && mkdir    "${XDG_RUNTIME_DIR}/slack"    2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/discord" ]  && mkdir    "${XDG_RUNTIME_DIR}/discord"  2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/firefox" ]  && mkdir    "${XDG_RUNTIME_DIR}/firefox"  2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/mesa/DB" ]  && mkdir    "${XDG_RUNTIME_DIR}/mesa/DB"  2> /dev/null
    ! [ -d "${XDG_RUNTIME_DIR}/chromium" ] && mkdir    "${XDG_RUNTIME_DIR}/chromium" 2> /dev/null

    # Make User Mount Path
    if ! [ -d "${XDG_RUNTIME_DIR}/mounts" ]; then
        mkdir      "${XDG_RUNTIME_DIR}/mounts" 2> /dev/null
        chmod 0700 "${XDG_RUNTIME_DIR}/mounts"
    fi
fi
