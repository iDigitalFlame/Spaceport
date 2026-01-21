#!/usr/bin/bash
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
## Deployment Helper Script
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

DIR_BASE="$(pwd)"
DIR_DEST="/opt/spaceport"

printf '\e[0;32;40mChecking Python files and linting..\x1b[0m\n'
# Lint
dash "./usr/lib/smd/assets/smd-lint.sh"

printf '\e[0;32;40mRemoving cache files..\x1b[0m\n'
# Remove pycache
find "${DIR_BASE}" -xdev -type f -name "*.pyc" -delete
find "${DIR_BASE}" -xdev -type d -name "*pycache*" -exec rm -rf {} \;

printf '\e[0;34;40mFiles missing newlines:\x1b[0m\n'
# Check for missing newlines at the end
pcregrep -LMr '\n\Z' . 2> /dev/null | grep -vE 'ghr$|hostname$|\.issue$|sysless$|/themes/|\.git|\.json$|\.md$|\.html$|\.code-workspace$|/ld.so|/etc/motd$'
printf '\e[0;34;40m==================================\x1b[0m\n'

printf '\e[0;37;40mPreparing file copy.. (\e[1;37;41msudo\e[0;37;40m prompt ahead)\x1b[0m\n'
cat<<EOF | sudo -i --
    set -u
    mount -o rw,remount /
    rm -f  "/etc/.pwd.lock" "/root/.bash_history"
    rm -rf "${DIR_DEST}/.git" "${DIR_DEST}/.github" "${DIR_DEST}/.vscode" "${DIR_DEST}/*.save" "${DIR_DEST}/*.md"
    printf '\e[0;37;41mCopying "\e[1;37;42m%s\e[0;37;41m" to "\e[1;37;44m%s\e[0;37;41m"..\x1b[0m\n' "$DIR_BASE" "$DIR_DEST"
    rsync --ignore-times --recursive \
          --exclude=.git* --exclude=*.save --exclude=.vscode --exclude="deploy.sh" \
          --exclude="LICENSE" --exclude="README.md" --exclude=*.code-workspace \
          --exclude=".github" --exclude=".vscode" "${DIR_BASE}/" "${DIR_DEST}/"
    printf '\e[0;37;41mSyncing permissions..\x1b[0m\n'
    syslink
    printf '\e[0;37;41mFile Diff:\x1b[0m\n'
    diff -r "${DIR_DEST}/" "${DIR_BASE}/" | grep "Only in ${DIR_DEST}" | grep -vE '.json$'
    printf '\e[0;37;41m==================================\x1b[0m\n'
    mount -ro remount,ro / 2> /dev/null || mount -Rro remount,ro /
    printf '\e[0;37;41mSync Complete!\x1b[0m\n'
EOF

cp "/etc/fstab"                    "${DIR_BASE}/fstab.save"
cp "${DIR_DEST}/units.save"        "${DIR_BASE}/units.save"
cp "${DIR_DEST}/masked.save"       "${DIR_BASE}/masked.save"
cp "${DIR_DEST}/packages.save"     "${DIR_BASE}/packages.save"
cp "${DIR_DEST}/indirect.save"     "${DIR_BASE}/indirect.save"
cp "${DIR_DEST}/packages-aur.save" "${DIR_BASE}/packages-aur.save"

chmod 0660 "${DIR_BASE}/fstab.save"
chmod 0660 "${DIR_BASE}/units.save"
chmod 0660 "${DIR_BASE}/masked.save"
chmod 0660 "${DIR_BASE}/packages.save"
chmod 0660 "${DIR_BASE}/indirect.save"
chmod 0660 "${DIR_BASE}/packages-aur.save"

if [ "$1" = "reload" ]; then
    printf '\e[0;36;40mReloading services..\x1b[0m\n'
    systemctl --user stop smd-client.service
    sudo sh -c "systemctl daemon-reload; systemctl restart smd-daemon.service"
    systemctl --user daemon-reload
    systemctl --user restart smd-client.service
fi

printf '\e[0;32;40mDone!\x1b[0m\n'
