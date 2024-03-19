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
## AppArmor Links Configuration
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

chmod 0555 "/etc/apparmor"
chmod 0500 "/etc/apparmor.d"
chmod 0500 "/var/cache/apparmor"
chmod 0544 "/opt/spaceport/etc/apparmor"
chmod 0500 "/opt/spaceport/etc/apparmor.d"

chown -R root:root "/etc/apparmor"
chown -R root:root "/etc/apparmor.d"
chown -R root:root "/var/cache/apparmor"

chmod 500 "/etc/audit"
chmod 400 "/etc/audit/audit.rules"
chmod 400 "/etc/audit/auditd.conf"

ln -sT "/etc/apparmor.d/php-fpm" "/etc/apparmor.d/disable/php-fpm" 2> /dev/null
ln -sT "/etc/apparmor.d/bin.ping" "/etc/apparmor.d/disable/bin.ping" 2> /dev/null
ln -sT "/etc/apparmor.d/samba-bgqd" "/etc/apparmor.d/disable/samba-bgqd" 2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd" "/etc/apparmor.d/disable/samba-rpcd" 2> /dev/null
ln -sT "/etc/apparmor.d/lsb_release" "/etc/apparmor.d/disable/lsb_release" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.nmbd" "/etc/apparmor.d/disable/usr.sbin.nmbd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.nscd" "/etc/apparmor.d/disable/usr.sbin.nscd" 2> /dev/null
ln -sT "/etc/apparmor.d/samba-dcerpcd" "/etc/apparmor.d/disable/samba-dcerpcd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.ntpd" "/etc/apparmor.d/disable/usr.sbin.ntpd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.smbd" "/etc/apparmor.d/disable/usr.sbin.smbd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.mdnsd" "/etc/apparmor.d/disable/usr.sbin.mdnsd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.identd" "/etc/apparmor.d/disable/usr.sbin.identd" 2> /dev/null
ln -sT "/etc/apparmor.d/nvidia_modprobe" "/etc/apparmor.d/disable/nvidia_modprobe" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.dovecot" "/etc/apparmor.d/disable/usr.sbin.dovecot" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.apache2" "/etc/apparmor.d/disable/usr.sbin.apache2" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.winbindd" "/etc/apparmor.d/disable/usr.sbin.winbindd" 2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd-classic" "/etc/apparmor.d/disable/samba-rpcd-classic" 2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd-spoolss" "/etc/apparmor.d/disable/samba-rpcd-spoolss" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.log" "/etc/apparmor.d/disable/usr.lib.dovecot.log" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dict" "/etc/apparmor.d/disable/usr.lib.dovecot.dict" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.auth" "/etc/apparmor.d/disable/usr.lib.dovecot.auth" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.imap" "/etc/apparmor.d/disable/usr.lib.dovecot.imap" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.lmtp" "/etc/apparmor.d/disable/usr.lib.dovecot.lmtp" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.pop3" "/etc/apparmor.d/disable/usr.lib.dovecot.pop3" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.avahi-daemon" "/etc/apparmor.d/disable/usr.sbin.avahi-daemon" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.stats" "/etc/apparmor.d/disable/usr.lib.dovecot.stats" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.anvil" "/etc/apparmor.d/disable/usr.lib.dovecot.anvil" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.config" "/etc/apparmor.d/disable/usr.lib.dovecot.config" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.deliver" "/etc/apparmor.d/disable/usr.lib.dovecot.deliver" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.director" "/etc/apparmor.d/disable/usr.lib.dovecot.director" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.smbldap-useradd" "/etc/apparmor.d/disable/usr.sbin.smbldap-useradd" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.pop3-login" "/etc/apparmor.d/disable/usr.lib.dovecot.pop3-login" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.imap-login" "/etc/apparmor.d/disable/usr.lib.dovecot.imap-login" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.replicator" "/etc/apparmor.d/disable/usr.lib.dovecot.replicator" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.ssl-params" "/etc/apparmor.d/disable/usr.lib.dovecot.ssl-params" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.managesieve" "/etc/apparmor.d/disable/usr.lib.dovecot.managesieve" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dovecot-lda" "/etc/apparmor.d/disable/usr.lib.dovecot.dovecot-lda" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dovecot-auth" "/etc/apparmor.d/disable/usr.lib.dovecot.dovecot-auth" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.script-login" "/etc/apparmor.d/disable/usr.lib.dovecot.script-login" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.doveadm-server" "/etc/apparmor.d/disable/usr.lib.dovecot.doveadm-server" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.managesieve-login" "/etc/apparmor.d/disable/usr.lib.dovecot.managesieve-login" 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.apache2.mpm-prefork.apache2" "/etc/apparmor.d/disable/usr.lib.apache2.mpm-prefork.apache2" 2> /dev/null
