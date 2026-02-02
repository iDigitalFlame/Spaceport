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
## AppArmor Links Configuration
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

if ! [ "$USER" = "root" ]; then
    echo "Error: root is required!"
    exit 1
fi

ln -sT "/etc/apparmor.d/rpm"                                 "/etc/apparmor.d/disable/rpm"                                  2> /dev/null
ln -sT "/etc/apparmor.d/tup"                                 "/etc/apparmor.d/disable/tup"                                  2> /dev/null
ln -sT "/etc/apparmor.d/cam"                                 "/etc/apparmor.d/disable/cam"                                  2> /dev/null
ln -sT "/etc/apparmor.d/code"                                "/etc/apparmor.d/disable/code"                                 2> /dev/null
ln -sT "/etc/apparmor.d/opam"                                "/etc/apparmor.d/disable/opam"                                 2> /dev/null
ln -sT "/etc/apparmor.d/wike"                                "/etc/apparmor.d/disable/wike"                                 2> /dev/null
ln -sT "/etc/apparmor.d/crun"                                "/etc/apparmor.d/disable/crun"                                 2> /dev/null
ln -sT "/etc/apparmor.d/runc"                                "/etc/apparmor.d/disable/runc"                                 2> /dev/null
ln -sT "/etc/apparmor.d/qcam"                                "/etc/apparmor.d/disable/qcam"                                 2> /dev/null
ln -sT "/etc/apparmor.d/scide"                               "/etc/apparmor.d/disable/scide"                                2> /dev/null
ln -sT "/etc/apparmor.d/slack"                               "/etc/apparmor.d/disable/slack"                                2> /dev/null
ln -sT "/etc/apparmor.d/steam"                               "/etc/apparmor.d/disable/steam"                                2> /dev/null
ln -sT "/etc/apparmor.d/vdens"                               "/etc/apparmor.d/disable/vdens"                                2> /dev/null
ln -sT "/etc/apparmor.d/vpnns"                               "/etc/apparmor.d/disable/vpnns"                                2> /dev/null
ln -sT "/etc/apparmor.d/wpcom"                               "/etc/apparmor.d/disable/wpcom"                                2> /dev/null
ln -sT "/etc/apparmor.d/opera"                               "/etc/apparmor.d/disable/opera"                                2> /dev/null
ln -sT "/etc/apparmor.d/geary"                               "/etc/apparmor.d/disable/geary"                                2> /dev/null
ln -sT "/etc/apparmor.d/loupe"                               "/etc/apparmor.d/disable/loupe"                                2> /dev/null
ln -sT "/etc/apparmor.d/brave"                               "/etc/apparmor.d/disable/brave"                                2> /dev/null
ln -sT "/etc/apparmor.d/chrome"                              "/etc/apparmor.d/disable/chrome"                               2> /dev/null
ln -sT "/etc/apparmor.d/ch-run"                              "/etc/apparmor.d/disable/ch-run"                               2> /dev/null
ln -sT "/etc/apparmor.d/msedge"                              "/etc/apparmor.d/disable/msedge"                               2> /dev/null
ln -sT "/etc/apparmor.d/podman"                              "/etc/apparmor.d/disable/podman"                               2> /dev/null
ln -sT "/etc/apparmor.d/toybox"                              "/etc/apparmor.d/disable/toybox"                               2> /dev/null
ln -sT "/etc/apparmor.d/sbuild"                              "/etc/apparmor.d/disable/sbuild"                               2> /dev/null
ln -sT "/etc/apparmor.d/devhelp"                             "/etc/apparmor.d/disable/devhelp"                              2> /dev/null
ln -sT "/etc/apparmor.d/Discord"                             "/etc/apparmor.d/disable/Discord"                              2> /dev/null
ln -sT "/etc/apparmor.d/trinity"                             "/etc/apparmor.d/disable/trinity"                              2> /dev/null
ln -sT "/etc/apparmor.d/firefox"                             "/etc/apparmor.d/disable/firefox"                              2> /dev/null
ln -sT "/etc/apparmor.d/php-fpm"                             "/etc/apparmor.d/disable/php-fpm"                              2> /dev/null
ln -sT "/etc/apparmor.d/keybase"                             "/etc/apparmor.d/disable/keybase"                              2> /dev/null
ln -sT "/etc/apparmor.d/flatpak"                             "/etc/apparmor.d/disable/flatpak"                              2> /dev/null
ln -sT "/etc/apparmor.d/foliate"                             "/etc/apparmor.d/disable/foliate"                              2> /dev/null
ln -sT "/etc/apparmor.d/php-fpm"                             "/etc/apparmor.d/disable/php-fpm"                              2> /dev/null
ln -sT "/etc/apparmor.d/buildah"                             "/etc/apparmor.d/disable/buildah"                              2> /dev/null
ln -sT "/etc/apparmor.d/busybox"                             "/etc/apparmor.d/disable/busybox"                              2> /dev/null
ln -sT "/etc/apparmor.d/pageedit"                            "/etc/apparmor.d/disable/pageedit"                             2> /dev/null
ln -sT "/etc/apparmor.d/bin.ping"                            "/etc/apparmor.d/disable/bin.ping"                             2> /dev/null
ln -sT "/etc/apparmor.d/lxc-stop"                            "/etc/apparmor.d/disable/lxc-stop"                             2> /dev/null
ln -sT "/etc/apparmor.d/chromium"                            "/etc/apparmor.d/disable/chromium"                             2> /dev/null
ln -sT "/etc/apparmor.d/obsidian"                            "/etc/apparmor.d/disable/obsidian"                             2> /dev/null
ln -sT "/etc/apparmor.d/polypane"                            "/etc/apparmor.d/disable/polypane"                             2> /dev/null
ln -sT "/etc/apparmor.d/rssguard"                            "/etc/apparmor.d/disable/rssguard"                             2> /dev/null
ln -sT "/etc/apparmor.d/epiphany"                            "/etc/apparmor.d/disable/epiphany"                             2> /dev/null
ln -sT "/etc/apparmor.d/nautilus"                            "/etc/apparmor.d/disable/nautilus"                             2> /dev/null
ln -sT "/etc/apparmor.d/virtiofsd"                           "/etc/apparmor.d/disable/virtiofsd"                            2> /dev/null
ln -sT "/etc/apparmor.d/evolution"                           "/etc/apparmor.d/disable/evolution"                            2> /dev/null
ln -sT "/etc/apparmor.d/qmapshack"                           "/etc/apparmor.d/disable/qmapshack"                            2> /dev/null
ln -sT "/etc/apparmor.d/notepadqq"                           "/etc/apparmor.d/disable/notepadqq"                            2> /dev/null
ln -sT "/etc/apparmor.d/stress-ng"                           "/etc/apparmor.d/disable/stress-ng"                            2> /dev/null
ln -sT "/etc/apparmor.d/surfshark"                           "/etc/apparmor.d/disable/surfshark"                            2> /dev/null
ln -sT "/etc/apparmor.d/1password"                           "/etc/apparmor.d/disable/1password"                            2> /dev/null
ln -sT "/etc/apparmor.d/kchmviewer"                          "/etc/apparmor.d/disable/kchmviewer"                           2> /dev/null
ln -sT "/etc/apparmor.d/samba-bgqd"                          "/etc/apparmor.d/disable/samba-bgqd"                           2> /dev/null
ln -sT "/etc/apparmor.d/mmdebstrap"                          "/etc/apparmor.d/disable/mmdebstrap"                           2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd"                          "/etc/apparmor.d/disable/samba-rpcd"                           2> /dev/null
ln -sT "/etc/apparmor.d/lxc-attach"                          "/etc/apparmor.d/disable/lxc-attach"                           2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-apt"                          "/etc/apparmor.d/disable/sbuild-apt"                           2> /dev/null
ln -sT "/etc/apparmor.d/uwsgi-core"                          "/etc/apparmor.d/disable/uwsgi-core"                           2> /dev/null
ln -sT "/etc/apparmor.d/goldendict"                          "/etc/apparmor.d/disable/goldendict"                           2> /dev/null
ln -sT "/etc/apparmor.d/ipa_verify"                          "/etc/apparmor.d/disable/ipa_verify"                           2> /dev/null
ln -sT "/etc/apparmor.d/lxc-create"                          "/etc/apparmor.d/disable/lxc-create"                           2> /dev/null
ln -sT "/etc/apparmor.d/ch-checkns"                          "/etc/apparmor.d/disable/ch-checkns"                           2> /dev/null
ln -sT "/etc/apparmor.d/sbin.klogd"                          "/etc/apparmor.d/disable/sbin.klogd"                           2> /dev/null
ln -sT "/etc/apparmor.d/unix-chkpwd"                         "/etc/apparmor.d/disable/unix-chkpwd"                          2> /dev/null
ln -sT "/etc/apparmor.d/lxc-execute"                         "/etc/apparmor.d/disable/lxc-execute"                          2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-hold"                         "/etc/apparmor.d/disable/sbuild-hold"                          2> /dev/null
ln -sT "/etc/apparmor.d/slirp4netns"                         "/etc/apparmor.d/disable/slirp4netns"                          2> /dev/null
ln -sT "/etc/apparmor.d/rootlesskit"                         "/etc/apparmor.d/disable/rootlesskit"                          2> /dev/null
ln -sT "/etc/apparmor.d/qutebrowser"                         "/etc/apparmor.d/disable/qutebrowser"                          2> /dev/null
ln -sT "/etc/apparmor.d/plasmashell"                         "/etc/apparmor.d/disable/plasmashell"                          2> /dev/null
ln -sT "/etc/apparmor.d/libcamerify"                         "/etc/apparmor.d/disable/libcamerify"                          2> /dev/null
ln -sT "/etc/apparmor.d/lxc-destroy"                         "/etc/apparmor.d/disable/lxc-destroy"                          2> /dev/null
ln -sT "/etc/apparmor.d/lxc-unshare"                         "/etc/apparmor.d/disable/lxc-unshare"                          2> /dev/null
ln -sT "/etc/apparmor.d/vivaldi-bin"                         "/etc/apparmor.d/disable/vivaldi-bin"                          2> /dev/null
ln -sT "/etc/apparmor.d/thunderbird"                         "/etc/apparmor.d/disable/thunderbird"                          2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-abort"                        "/etc/apparmor.d/disable/sbuild-abort"                         2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-clean"                        "/etc/apparmor.d/disable/sbuild-clean"                         2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-shell"                        "/etc/apparmor.d/disable/sbuild-shell"                         2> /dev/null
ln -sT "/etc/apparmor.d/transmission"                        "/etc/apparmor.d/disable/transmission"                         2> /dev/null
ln -sT "/etc/apparmor.d/sbin.syslogd"                        "/etc/apparmor.d/disable/sbin.syslogd"                         2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-unhold"                       "/etc/apparmor.d/disable/sbuild-unhold"                        2> /dev/null
ln -sT "/etc/apparmor.d/lc-compliance"                       "/etc/apparmor.d/disable/lc-compliance"                        2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.nmbd"                       "/etc/apparmor.d/disable/usr.sbin.nmbd"                        2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.nscd"                       "/etc/apparmor.d/disable/usr.sbin.nscd"                        2> /dev/null
ln -sT "/etc/apparmor.d/balena-etcher"                       "/etc/apparmor.d/disable/balena-etcher"                        2> /dev/null
ln -sT "/etc/apparmor.d/samba-dcerpcd"                       "/etc/apparmor.d/disable/samba-dcerpcd"                        2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.ntpd"                       "/etc/apparmor.d/disable/usr.sbin.ntpd"                        2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.smbd"                       "/etc/apparmor.d/disable/usr.sbin.smbd"                        2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-update"                       "/etc/apparmor.d/disable/sbuild-update"                        2> /dev/null
ln -sT "/etc/apparmor.d/userbindmount"                       "/etc/apparmor.d/disable/userbindmount"                        2> /dev/null
ln -sT "/etc/apparmor.d/linux-sandbox"                       "/etc/apparmor.d/disable/linux-sandbox"                        2> /dev/null
ln -sT "/etc/apparmor.d/signal-desktop"                      "/etc/apparmor.d/disable/signal-desktop"                       2> /dev/null
ln -sT "/etc/apparmor.d/privacybrowser"                      "/etc/apparmor.d/disable/privacybrowser"                       2> /dev/null
ln -sT "/etc/apparmor.d/github-desktop"                      "/etc/apparmor.d/disable/github-desktop"                       2> /dev/null
ln -sT "/etc/apparmor.d/sbin.syslog-ng"                      "/etc/apparmor.d/disable/sbin.syslog-ng"                       2> /dev/null
ln -sT "/etc/apparmor.d/lxc-usernsexec"                      "/etc/apparmor.d/disable/lxc-usernsexec"                       2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.mdnsd"                      "/etc/apparmor.d/disable/usr.sbin.mdnsd"                       2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-upgrade"                      "/etc/apparmor.d/disable/sbuild-upgrade"                       2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-adduser"                      "/etc/apparmor.d/disable/sbuild-adduser"                       2> /dev/null
ln -sT "/etc/apparmor.d/nvidia_modprobe"                     "/etc/apparmor.d/disable/nvidia_modprobe"                      2> /dev/null
ln -sT "/etc/apparmor.d/MongoDB_Compass"                     "/etc/apparmor.d/disable/MongoDB_Compass"                      2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.identd"                     "/etc/apparmor.d/disable/usr.sbin.identd"                      2> /dev/null
ln -sT "/etc/apparmor.d/nvidia_modprobe"                     "/etc/apparmor.d/disable/nvidia_modprobe"                      2> /dev/null
ln -sT "/etc/apparmor.d/element-desktop"                     "/etc/apparmor.d/disable/element-desktop"                      2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.dnsmasq"                    "/etc/apparmor.d/disable/usr.sbin.dnsmasq"                     2> /dev/null
ln -sT "/etc/apparmor.d/systemd-coredump"                    "/etc/apparmor.d/disable/systemd-coredump"                     2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.dovecot"                    "/etc/apparmor.d/disable/usr.sbin.dovecot"                     2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.apache2"                    "/etc/apparmor.d/disable/usr.sbin.apache2"                     2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.winbindd"                   "/etc/apparmor.d/disable/usr.sbin.winbindd"                    2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd-classic"                  "/etc/apparmor.d/disable/samba-rpcd-classic"                   2> /dev/null
ln -sT "/etc/apparmor.d/samba-rpcd-spoolss"                  "/etc/apparmor.d/disable/samba-rpcd-spoolss"                   2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-distupgrade"                  "/etc/apparmor.d/disable/sbuild-distupgrade"                   2> /dev/null
ln -sT "/etc/apparmor.d/QtWebEngineProcess"                  "/etc/apparmor.d/disable/QtWebEngineProcess"                   2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.log"                 "/etc/apparmor.d/disable/usr.lib.dovecot.log"                  2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-createchroot"                 "/etc/apparmor.d/disable/sbuild-createchroot"                  2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-checkpackages"                "/etc/apparmor.d/disable/sbuild-checkpackages"                 2> /dev/null
ln -sT "/etc/apparmor.d/sbuild-destroychroot"                "/etc/apparmor.d/disable/sbuild-destroychroot"                 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dict"                "/etc/apparmor.d/disable/usr.lib.dovecot.dict"                 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.auth"                "/etc/apparmor.d/disable/usr.lib.dovecot.auth"                 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.imap"                "/etc/apparmor.d/disable/usr.lib.dovecot.imap"                 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.lmtp"                "/etc/apparmor.d/disable/usr.lib.dovecot.lmtp"                 2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.pop3"                "/etc/apparmor.d/disable/usr.lib.dovecot.pop3"                 2> /dev/null
ln -sT "/etc/apparmor.d/tuxedo-control-center"               "/etc/apparmor.d/disable/tuxedo-control-center"                2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.avahi-daemon"               "/etc/apparmor.d/disable/usr.sbin.avahi-daemon"                2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.stats"               "/etc/apparmor.d/disable/usr.lib.dovecot.stats"                2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.anvil"               "/etc/apparmor.d/disable/usr.lib.dovecot.anvil"                2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.config"              "/etc/apparmor.d/disable/usr.lib.dovecot.config"               2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.deliver"             "/etc/apparmor.d/disable/usr.lib.dovecot.deliver"              2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.director"            "/etc/apparmor.d/disable/usr.lib.dovecot.director"             2> /dev/null
ln -sT "/etc/apparmor.d/usr.sbin.smbldap-useradd"            "/etc/apparmor.d/disable/usr.sbin.smbldap-useradd"             2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.pop3-login"          "/etc/apparmor.d/disable/usr.lib.dovecot.pop3-login"           2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.imap-login"          "/etc/apparmor.d/disable/usr.lib.dovecot.imap-login"           2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.replicator"          "/etc/apparmor.d/disable/usr.lib.dovecot.replicator"           2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.ssl-params"          "/etc/apparmor.d/disable/usr.lib.dovecot.ssl-params"           2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.managesieve"         "/etc/apparmor.d/disable/usr.lib.dovecot.managesieve"          2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dovecot-lda"         "/etc/apparmor.d/disable/usr.lib.dovecot.dovecot-lda"          2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.dovecot-auth"        "/etc/apparmor.d/disable/usr.lib.dovecot.dovecot-auth"         2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.script-login"        "/etc/apparmor.d/disable/usr.lib.dovecot.script-login"         2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.doveadm-server"      "/etc/apparmor.d/disable/usr.lib.dovecot.doveadm-server"       2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.dovecot.managesieve-login"   "/etc/apparmor.d/disable/usr.lib.dovecot.managesieve-login"    2> /dev/null
ln -sT "/etc/apparmor.d/usr.lib.apache2.mpm-prefork.apache2" "/etc/apparmor.d/disable/usr.lib.apache2.mpm-prefork.apache2"  2> /dev/null

chown -hR root:root "/etc/apparmor.d"
chown -hR root:root "/var/cache/apparmor"

chmod 0500 "/etc/apparmor.d"
chmod 0500 "/var/cache/apparmor"

find "/etc/apparmor.d" -xdev -type d -exec chmod 0500 {} \;
find "/etc/apparmor.d" -xdev -type f -exec chmod 0400 {} \;
