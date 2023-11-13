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
## Icon Builder Utility for DarkSky
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
    echo "Only root can do this!"
    exit 1
fi

if ! [ -d "/usr/share/icons/kora" ]; then
    echo '"/usr/share/icons/kora" does not exist!'
    exit 1
fi
if ! [ -d "/usr/share/icons/Flatery-Dark" ]; then
    echo '"/usr/share/icons/Flatery-Dark" does not exist!'
    exit 1
fi
if ! [ -d "/usr/share/icons/Vimix-cursors" ]; then
    echo '"/usr/share/icons/Vimix-cursors" does not exist!'
    exit 1
fi

THEME_DIR="/usr/share/icons/DarkSky"
if [ -e "$THEME_DIR" ]; then
    rm -rf "$THEME_DIR"
fi

if ! cp -R "/usr/share/icons/Flatery-Dark" "$THEME_DIR"; then
    exit 0
fi

rm -rf "${THEME_DIR}/apps"
rm -f "${THEME_DIR}/index.theme"
rm -f "${THEME_DIR}/icon-theme.cache"
find "${THEME_DIR}/actions" -type l -name "go-*" -delete
find "${THEME_DIR}/actions" -type f -name "go-*" -delete

ln -s "/usr/share/icons/kora/apps" "${THEME_DIR}/apps"
ln -s "/usr/share/icons/Vimix-cursors/cursors" "${THEME_DIR}/cursors" 2> /dev/null
ln -s "/usr/share/themes/DarkSky/icons.theme" "${THEME_DIR}/index.theme"

for icon in $(find "/usr/share/icons/kora/actions" -type f -name "go-*" -ls | awk '{print $11}'); do
    for d in "${THEME_DIR}"/actions/*; do
        if [ -d "${THEME_DIR}/actions/${d}" ]; then
            ln -s "$icon" "${THEME_DIR}/actions/${d}/" 2> /dev/null
        fi
    done
done

chown -R root:root "$THEME_DIR"
find "$THEME_DIR" -type d -exec chmod 0755 {} \;
find "$THEME_DIR" -type f -exec chmod 0644 {} \;
exit 0
