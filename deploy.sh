#!/usr/bin/bash
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

DIR_BASE="$(pwd)"
DIR_DEST="/opt/spaceport"

# Lint
dash "./usr/lib/smd/assets/smd-lint.sh"

# Remove pycache
find "${DIR_BASE}" -type f -name "*.pyc" -delete
find "${DIR_BASE}" -type d -name "*pycache*" -exec rm -rf {} \;

cat<<EOF | sudo -i --
    set -u
    mount -o rw,remount /
    rm -f  "/etc/.pwd.lock" "/root/.bash_history"
    rm -rf "${DIR_DEST}/.git" "${DIR_DEST}/.github" "${DIR_DEST}/.vscode" "${DIR_DEST}/*.md"
    printf 'Copying "\x1b[96m\x1b[1m%s\x1b[0m" to "\x1b[96m\x1b[1m%s\x1b[0m"..\n' "$DIR_BASE" "$DIR_DEST"
    rsync --ignore-times --recursive \
          --exclude=.git* --exclude=*.md --exclude=.vscode --exclude="deploy.sh" \
          --exclude="LICENSE" --exclude=*.code-workspace \
          --exclude ".github" --exclude ".vscode" "${DIR_BASE}/" "${DIR_DEST}/"
    syslink
    diff -r "${DIR_DEST}/" "${DIR_BASE}/" | grep "Only in ${DIR_DEST}" | grep -vE '.json$'
    mount -ro remount,ro / 2> /dev/null || mount -Rro remount,ro /
EOF

cp "/etc/fstab"                  "${DIR_BASE}/fstab.md"
cp "${DIR_DEST}/units.md"        "${DIR_BASE}/units.md"
cp "${DIR_DEST}/masked.md"       "${DIR_BASE}/masked.md"
cp "${DIR_DEST}/packages.md"     "${DIR_BASE}/packages.md"
cp "${DIR_DEST}/indirect.md"     "${DIR_BASE}/indirect.md"
cp "${DIR_DEST}/packages-aur.md" "${DIR_BASE}/packages-aur.md"

chmod 0660 "${DIR_BASE}/fstab.md"
chmod 0660 "${DIR_BASE}/units.md"
chmod 0660 "${DIR_BASE}/masked.md"
chmod 0660 "${DIR_BASE}/packages.md"
chmod 0660 "${DIR_BASE}/indirect.md"
chmod 0660 "${DIR_BASE}/packages-aur.md"

if [ "$1" = "reload" ]; then
    systemctl --user stop smd-client.service
    sudo sh -c "systemctl daemon-reload; systemctl restart smd-daemon.service"
    systemctl --user daemon-reload
    systemctl --user restart smd-client.service
fi
