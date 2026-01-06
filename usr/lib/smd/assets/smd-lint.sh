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
## Python Linting Script
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

vet() {
    isort --color --no-sections --length-sort --force-sort-within-sections \
          --multi-line=3 --line-length=88 --order-by-type --combine-as \
          --trailing-comma --case-sensitive --float-to-top --use-parentheses \
          --honor-noqa "$1"
    black -q "$1"
}

for i in $(find ./usr/lib/smd/lib/ -xdev -type f -print); do
    vet "$i" | grep -v 'Skipped '
done

# Don't run isort on these, as the import for SMD needs to be first and isort
# doesn't understand that
black -q "usr/lib/smd/bin/powerctl"
black -q "usr/lib/smd/libexec/smd-daemon"
black -q "usr/lib/smd/libexec/smd-client"
black -q "usr/lib/smd/libexec/smd-locker"
black -q "usr/lib/smd/libexec/smd-message"
black -q "usr/lib/smd/libexec/smd-wait-sway"
