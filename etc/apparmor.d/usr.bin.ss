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
## AppArmor Configuration
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

include <tunables/spaceport>

profile ss /{,usr/}bin/{netstat,ss} flags=(enforce) {
    include <abstractions/command>
    include <abstractions/nameservice>

    capability                                      net_admin,
    capability                                      sys_ptrace,
    capability                                      dac_override,
    capability                                      dac_read_search,

    ptrace read,

    /usr/bin/{netstat,ss}                           rm,

    /proc/                                          r,
    /proc/@{pid}/fd/                                r,
    /proc/@{pid}/{cmdline,stat}                     r,
    /proc/sys/net/ipv4/ip_local_port_range          r,
    /proc/sys/net/ipv6/conf/all/disable_ipv6        r,
    /proc/@{pid}/net/{raw,tcp,udp,udplite,unix}{,6} r,

    include if exists <local/usr.bin.ss>
}
