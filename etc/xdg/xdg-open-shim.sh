#!/usr/bin/sh
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
## XDG Open Whitespace Fix Shim
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

get_key() {
    local file="${1}"
    local key="${2}"
    local desktop_entry=""

    IFS_="${IFS}"
    IFS=""

    while read -r line
    do
        case "$line" in
            "[Desktop Entry]")
                desktop_entry="y"
            ;;
            # Reset match flag for other groups
            "["*)
                desktop_entry=""
            ;;
            # Match with spaces
            "${key}"*"="*)
                # Only match Desktop Entry group
                if [ -n "${desktop_entry}" ]
                then
                    # Remove leading whitespaces
                    echo "${line}" | cut -d= -f 2- | sed 's/^[[:space:]]*//'
                fi
        esac
    done < "${file}"
    IFS="${IFS_}"
}
