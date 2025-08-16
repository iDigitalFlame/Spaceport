#!/usr/bin/dash
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
## Base Permissions Configuration
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

if ! [ "$USER" = "root" ]; then
    echo "Error: root is required!"
    exit 1
fi

BASE_DIR="/opt/spaceport"

_chmod() {
    if [ $# -lt 2 ]; then
        return 0
    fi
    chmod -h $1 "$2"
    chmod -h $1 "${BASE_DIR}$2"
    if [ $# -eq 3 ]; then
        chmod -h $3 "$2/"*            2> /dev/null
        chmod -h $3 "${BASE_DIR}$2/"* 2> /dev/null
    fi
}

# Setup Base Permissions
## Remove SUID/SGID
## Owned by root:root / 0555
chown -hR root:root "${BASE_DIR}"
chmod -hR "=0555"   "${BASE_DIR}"

# Change /boot Permissions
chmod -h  0500      "/boot"
chmod -h  0500      "/boot/loader"
chmod -h  0500      "/boot/esp"                        2> /dev/null
find "/boot" -xdev         -exec chown root:root {} \; 2> /dev/null
find "/boot" -xdev -type f -exec chmod 0400 {} \;,     2> /dev/null

# Permission Fixes
## Starting 0444 Permission
find "${BASE_DIR}/" -xdev -type f -exec chmod -h 0444 {} \;
## Group Fixes
find "/" -xdev -group firewall-web -exec chgrp -h root {} \;

## Update Targets with root:root / 0555
for i in $(find "${BASE_DIR}/" -xdev -type d -not -path "${BASE_DIR}/" -print); do
    chown -h root:root "${i#$BASE_DIR}"
    chmod -h 0555      "${i#$BASE_DIR}"
done

# Remove "Everyone" Permissions
## Directories / Sub-files
_chmod 0550 "/etc/audit"
_chmod 0550 "/etc/initcpio"
_chmod 0550 "/etc/initcpio/post"     0550
_chmod 0550 "/etc/kernel"            0440
_chmod 0550 "/etc/logrotate.d"       0440
_chmod 0550 "/etc/mkinitcpio.d"      0440
_chmod 0550 "/etc/modprobe.d"        0440
_chmod 0550 "/etc/modules-load.d"    0440
_chmod 0550 "/etc/pacman.d/hooks"    0440
_chmod 0550 "/etc/security/limits.d" 0440
_chmod 0550 "/etc/polkit-1"
_chmod 0550 "/etc/polkit-1/rules.d"
_chmod 0550 "/etc/squid"             0440
_chmod 0500 "/etc/sudoers.d"         0400
_chmod 0500 "/etc/sysctl.d"          0400
_chmod 0550 "/etc/tmpfiles.d"        0440
_chmod 0550 "/etc/udev/rules.d"      0440
_chmod 0550 "/usr/lib/smd/sbin"      0550
_chmod 0550 "/etc/modprobe.d"        0440
_chmod 0550 "/etc/udev/rules.d"      0440
_chmod 0550 "/etc/modules-load.d"    0440
_chmod 0550 "/etc/NetworkManager"
_chmod 0550 "/etc/pacman.d/hooks"    0440

## Files
chmod -h 0444 "/etc/ssh/"*.pub
chmod -h 0440 "${BASE_DIR}/etc/locale.gen"
chmod -h 0440 "${BASE_DIR}/etc/libaudit.conf"
chmod -h 0440 "${BASE_DIR}/etc/nftables.conf"
chmod -h 0440 "${BASE_DIR}/etc/vconsole.conf"
chmod -h 0440 "${BASE_DIR}/etc/logrotate.conf"
chmod -h 0440 "${BASE_DIR}/etc/ssh/sshd_config"
chmod -h 0440 "${BASE_DIR}/etc/mkinitcpio.conf"
chmod -h 0440 "${BASE_DIR}/etc/ssh/sshd_config"
chmod -h 0440 "${BASE_DIR}/etc/polkit-1/rules.d/spaceport.rules"
chmod -h 0440 "${BASE_DIR}/etc/NetworkManager/NetworkManager.conf"

## Might Not Exist
chmod -h 0550 "/usr/local/share/polkit-1"         2> /dev/null
chmod -h 0550 "/usr/local/share/polkit-1/rules.d" 2> /dev/null
chmod -h 0444 "/var/cache/librewolf.cfg.bak"      2> /dev/null

# Recursive Execute
chmod -hR 0555 "${BASE_DIR}/bin"
chmod -hR 0555 "/etc/profile.d"
chmod -hR 0555 "${BASE_DIR}/etc/profile.d"
chmod -hR 0555 "/etc/syscheck.d"
chmod -hR 0555 "${BASE_DIR}/etc/syscheck.d"
chmod -hR 0555 "/usr/lib/smd/bin"
chmod -hR 0555 "${BASE_DIR}/usr/lib/smd/bin"

# CUPS Permissions
chmod -h 0550 "/etc/cups"
chmod -h 0770 "/etc/cups/ppd"
chmod -h 0550 "/etc/cups/ssl"
chmod -h 0440 "/etc/cups/"*.conf         2> /dev/null
chmod -h 0440 "/etc/cups/"*.conf.default 2> /dev/null

# Ownership Updates
chown -hR root:cups    "/etc/cups"
chown -hR root:cups    "${BASE_DIR}/etc/cups"
chown -hR root:proxy   "/etc/squid"
chown -hR root:proxy   "${BASE_DIR}/etc/squid"
chown -h  root:root    "/usr/share/applications/mimeinfo.cache"
chown -h  root:root    "${BASE_DIR}/usr/share/applications/mimeinfo.cache"
chown -hR root:polkitd "/etc/polkit-1"
chown -hR root:polkitd "${BASE_DIR}/etc/polkit-1"
chown -hR root:polkitd "/usr/local/share/polkit-1"

# Group Helper Permissions
chown -h root:root "/bin/ghr"
chown -h root:root "${BASE_DIR}/bin/ghr"
chmod -h 4755      "${BASE_DIR}/bin/ghr"

# SMD Permissions
chmod -h 0500  "/etc/smd"
chmod -h 0400  "/etc/smd/"*
chmod -h 0640  "/var/cache/smd/"*.json
chmod -h 0640  "/var/cache/smd/hydra"
chmod -h 0640  "/var/cache/smd/hydra/"* 2> /dev/null
chmod -hR 0555 "${BASE_DIR}/usr/lib/smd/libexec"
chmod -h 0444  "${BASE_DIR}/var/cache/smd/constants.json"
chmod -h 0555  "${BASE_DIR}/usr/lib/smd/assets/smb-backup-entries"
chmod -h 0555  "${BASE_DIR}/usr/lib/smd/assets/smb-backup-extract"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-video"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-daemon"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-usb-add"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-key-eject"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-power-low"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-usb-remove"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-suspend-pre"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-suspend-post"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-hibernate-pre"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-hibernate-post"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-power-attached"
chmod -h 0550  "${BASE_DIR}/usr/lib/smd/libexec/smd-power-detached"

# Secureboot Permissions
chown -hR root:root "/opt/secureboot"
chmod -hR 0500      "/opt/secureboot"
chmod -h  0400      "/opt/secureboot/"*

# Backup Cache Permissions
chown root:root "/var/cache/smd/backup" 2> /dev/null
chmod 0750      "/var/cache/smd/backup" 2> /dev/null

# AuditD Permissions
chmod -h 0440 "/etc/audit/"*           2> /dev/null
chmod -h 0550 "/etc/audit/rules.d"
chmod -h 0440 "/etc/audit/rules.d/"*   2> /dev/null
chmod -h 0550 "/etc/audit/plugins.d"
chmod -h 0440 "/etc/audit/plugins.d"/* 2> /dev/null

# AppArmor Permissions
chmod -h  0500 "/etc/apparmor.d"
chmod -hR 0500 "${BASE_DIR}/etc/apparmor.d"
find "${BASE_DIR}/etc/apparmor.d" -xdev -type f -exec chmod -h 0400 {} \;

# Fill Empty Modules

mkdir    "/usr/lib/firmware/qed"              2> /dev/null
mkdir    "/usr/lib/firmware/qlogic"           2> /dev/null
mkdir    "/usr/lib/firmware/amdgpu"           2> /dev/null
mkdir    "/usr/lib/firmware/radeon"           2> /dev/null
mkdir -p "/usr/lib/firmware/nvidia/gp100/acr" 2> /dev/null

touch "/usr/lib/firmware/qat_6xxx.bin"
touch "/usr/lib/firmware/ql2500_fw.bin"
touch "/usr/lib/firmware/aic94xx-seq.fw"
touch "/usr/lib/firmware/wd719x-risc.bin"
touch "/usr/lib/firmware/qlogic/12160.bin"
touch "/usr/lib/firmware/ast_dp501_fw.bin"
touch "/usr/lib/firmware/ct2fw-3.2.5.1.bin"
touch "/usr/lib/firmware/renesas_usb_fw.mem"
touch "/usr/lib/firmware/radeon/R520_cp.bin"
touch "/usr/lib/firmware/amdgpu/navi12_gpu_info.bin"
touch "/usr/lib/firmware/nvidia/gp100/acr/ucode_load.bin"
touch "/usr/lib/firmware/qed/qed_init_values_zipped-8.59.1.0.bin"

# Remove Drun Permissions
chmod 0400 /usr/share/applications/exo-*                                2> /dev/null
chmod 0400 /usr/share/applications/gcr-*                                2> /dev/null
chmod 0400 /usr/share/applications/wine*                                2> /dev/null
chmod 0400 /usr/share/applications/*qt4*                                2> /dev/null
chmod 0400 /usr/share/applications/gtk3-*                               2> /dev/null
chmod 0400 /usr/share/applications/zenmap*                              2> /dev/null
chmod 0400 /usr/share/applications/geoclue-*                            2> /dev/null
chmod 0400 /usr/share/applications/*scangear*                           2> /dev/null
chmod 0400 /usr/share/applications/*autostart*                          2> /dev/null
chmod 0400 /usr/share/applications/cups.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/bssh.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/bvnc.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/xdvi.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/htop.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/rofi.desktop                         2> /dev/null
chmod 0400 /usr/share/applications/kitty.desktop                        2> /dev/null
chmod 0400 /usr/share/applications/qv4l2.desktop                        2> /dev/null
chmod 0400 /usr/share/applications/xgps*.desktop                        2> /dev/null
chmod 0400 /usr/share/applications/slack.desktop                        2> /dev/null
chmod 0400 /usr/share/applications/fluid*.desktop                       2> /dev/null
chmod 0400 /usr/share/applications/sudoku.desktop                       2> /dev/null
chmod 0400 /usr/share/applications/blocks.desktop                       2> /dev/null
chmod 0400 /usr/share/applications/lstopo.desktop                       2> /dev/null
chmod 0400 /usr/share/applications/codium.desktop                       2> /dev/null
chmod 0400 /usr/share/applications/vesktop.desktop                      2> /dev/null
chmod 0400 /usr/share/applications/arduino.desktop                      2> /dev/null
chmod 0400 /usr/share/applications/qvidcap.desktop                      2> /dev/null
chmod 0400 /usr/share/applications/firefox.desktop                      2> /dev/null
chmod 0400 /usr/share/applications/cropgui.desktop                      2> /dev/null
chmod 0400 /usr/share/applications/VSCodium.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/checkers.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/gtk-lshw.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/hdspconf.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/chromium.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/geisview.desktop                     2> /dev/null
chmod 0400 /usr/share/applications/librewolf.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/ristretto.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/echomixer.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/hdspmixer.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/notesnook.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/cmake-gui.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/vncviewer.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/electron*.desktop                    2> /dev/null
chmod 0400 /usr/share/applications/lxshortcut.desktop                   2> /dev/null
chmod 0400 /usr/share/applications/hwmixvolume.desktop                  2> /dev/null
chmod 0400 /usr/share/applications/xfce4-about.desktop                  2> /dev/null
chmod 0400 /usr/share/applications/hdajackretask.desktop                2> /dev/null
chmod 0400 /usr/share/applications/envy24control.desktop                2> /dev/null
chmod 0400 /usr/share/applications/teensy-loader.desktop                2> /dev/null
chmod 0400 /usr/share/applications/org.kde.falkon.desktop               2> /dev/null
chmod 0400 /usr/share/applications/avahi-discover.desktop               2> /dev/null
chmod 0400 /usr/share/applications/codium-wayland.desktop               2> /dev/null
chmod 0400 /usr/share/applications/signal-desktop.desktop               2> /dev/null
chmod 0400 /usr/share/applications/telegramdesktop.desktop              2> /dev/null
chmod 0400 /usr/share/applications/libfm-pref-apps.desktop              2> /dev/null
chmod 0400 /usr/share/applications/thunar-settings.desktop              2> /dev/null
chmod 0400 /usr/share/applications/blueman-adapters.desktop             2> /dev/null
chmod 0400 /usr/share/applications/libinput-gestures.desktop            2> /dev/null
chmod 0400 /usr/share/applications/java-java-openjdk.desktop            2> /dev/null
chmod 0400 /usr/share/applications/vscodium-electron*.desktop           2> /dev/null
chmod 0400 /usr/share/applications/thunar-bulk-rename.desktop           2> /dev/null
chmod 0400 /usr/share/applications/codium-uri-handler.desktop           2> /dev/null
chmod 0400 /usr/share/applications/com.ultimaker.cura.desktop           2> /dev/null
chmod 0400 /usr/share/applications/*.cubocore.CorePDF.desktop           2> /dev/null
chmod 0400 /usr/share/applications/mcpelauncher-ui-qt.desktop           2> /dev/null
chmod 0400 /usr/share/applications/rofi-theme-selector.desktop          2> /dev/null
chmod 0400 /usr/share/applications/jshell-java-openjdk.desktop          2> /dev/null
chmod 0400 /usr/share/applications/pcmanfm-desktop-pref.desktop         2> /dev/null
chmod 0400 /usr/share/applications/org.gnome.FileRoller.desktop         2> /dev/null
chmod 0400 /usr/share/applications/org.telegram.desktop.desktop         2> /dev/null
chmod 0400 /usr/share/applications/cura-modern-appimage.desktop         2> /dev/null
chmod 0400 /usr/share/applications/jconsole-java-openjdk.desktop        2> /dev/null
chmod 0400 /usr/share/applications/youtube-music-desktop.desktop        2> /dev/null
chmod 0400 /usr/share/applications/xfce4-terminal-settings.desktop      2> /dev/null
chmod 0400 /usr/share/applications/org.keepassxc.KeePassXC.desktop      2> /dev/null
chmod 0400 /usr/share/applications/net.sourceforge.liferea.desktop      2> /dev/null
chmod 0400 /usr/share/applications/io.elementary.granite-7.demo.desktop 2> /dev/null
