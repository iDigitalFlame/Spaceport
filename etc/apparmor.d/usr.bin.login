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

profile login /usr/bin/login flags=(enforce, attach_disconnected) {
    include <abstractions/base>
    include <abstractions/wutmp>
    include <abstractions/consoles>
    include <abstractions/dbus-system>
    include <abstractions/nameservice>
    include <abstractions/private-files>
    include <abstractions/authentication>

    capability                             kill,
    capability                             chown,
    capability                             fowner,
    capability                             fsetid,
    capability                             setgid,
    capability                             setuid,
    capability                             setpcap,
    capability                             audit_write,
    capability                             dac_override,
    capability                             sys_resource,
    capability                             sys_tty_config,
    capability                             dac_read_search,

    network                                netlink raw,

    signal send set=(hup, term),

    ptrace read,

    @{sysconfig}/etc/motd                  r,

    /                                      r,
    /etc/motd                              r,
    /etc/shells                            r,
    /usr/bin/login                         rm,
    /etc/machine-id                        r,
    /etc/environment                       r,
    /var/log/btmp{,.*}                     r,
    /etc/default/locale                    r,
    /etc/security/group.conf               r,
    /etc/security/limits.conf              r,
    /etc/security/pam_env.conf             r,
    /etc/security/limits.d/{,*}            r,

    /proc/1/limits                         r,
    /proc/@{pid}/cgroup                    r,

    @{run}/credentials/getty@tty*.service/ r,

    owner /proc/@{pid}/uid_map             r,

    /dev/tty*                              rw,

    /var/lib/faillock/*                    rwk,
    /var/lib/lastlog{,/}                   rw,

    @{run}/faillock/*                      rwk,
    @{run}/systemd/sessions/*.ref          rw,

    owner /proc/@{pid}/loginuid            rw,

    /usr/bin/{,ba,da,z}sh                  Ux,
    /usr/bin/gnome-keyring-daemon          Px -> gnome-keyring-daemon,

    unix type=stream addr="@*/bus/login/system",

    dbus (send, receive) bus=system interface=org.freedesktop.login1,

    include if exists <local/usr.bin.login>
}
