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
## Themes Configuration
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

if ! [ "$USER" = "root" ]; then
    echo "Error: root is required!"
    exit 1
fi

if ! [ -d "/usr/share/icons/DarkSky" ]; then
    dash "/usr/share/themes/DarkSky/build-icons.sh"
fi
if ! [ -d "/usr/share/icons/MoonlightSky" ]; then
    dash "/usr/share/themes/MoonlightSky/build-icons.sh"
fi

find "/usr/share/icons" -xdev -xtype l -delete
find "/usr/share/themes" -xdev -xtype l -delete
find "/usr/share/icons/DarkSky" -xdev -type f -name .directory -delete
find "/usr/share/themes/DarkSky" -xdev -type f -name .directory -delete
find "/usr/share/icons/MoonlightSky" -xdev -type f -name .directory -delete
find "/usr/share/themes/MoonlightSky" -xdev -type f -name .directory -delete

linkcheck "/usr/share/icons/kora/apps/scalable/qtws.svg" "/usr/share/icons/kora/apps/scalable/youtube-music.svg"
linkcheck "/usr/share/icons/kora/apps/scalable/codium-url-handler.svg" "/usr/share/icons/kora/apps/scalable/vscodium.svg"
linkcheck "/usr/share/icons/kora/apps/scalable/gtk-dialog-warning.svg" "/usr/share/icons/kora/apps/scalable/firewall-config.svg"
