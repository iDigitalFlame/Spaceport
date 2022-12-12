#!/usr/bin/dash
# Permissions Configuration
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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
    printf "[!] Only root can do this!\n"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Base Permissions
chmod u-s -R "$BASE_DIR"
chmod g-s -R "$BASE_DIR"
chown root:root -R "$BASE_DIR"
chmod 0555 -R "$BASE_DIR"
chmod 0555 -R "${BASE_DIR}/etc"
chmod 0555 -R "${BASE_DIR}/usr"
chmod 0555 -R "${BASE_DIR}/etc/chromium"
chmod 0555 -R "/etc/chromium"

# General No Execute Permission for files
find "${BASE_DIR}/" -type f -exec chmod 444 {} \; 2> /dev/null

# Remove non-root permissions on copied files
find "/" -xdev -group firewall-web -exec sh -c 'chgrp -h root {}' \;

# General Execute
chmod 0550 -R "/etc/smd"
chmod 0555 -R "${BASE_DIR}/bin"
chmod 0555 -R "${BASE_DIR}/etc/ssh"
chmod 0555 -R "${BASE_DIR}/etc/udev"
chmod 0550 -R "${BASE_DIR}/etc/squid"
chmod 0550 -R "${BASE_DIR}/etc/iptables"
chmod 0550 -R "${BASE_DIR}/etc/security"
chmod 0550 -R "${BASE_DIR}/etc/sysctl.d"
chmod 0555 -R "${BASE_DIR}/var/cache/smd"
chmod 0555 -R "${BASE_DIR}/etc/profile.d"
chmod 0550 -R "${BASE_DIR}/etc/sudoers.d"
chmod 0555 -R "${BASE_DIR}/etc/syscheck.d"
chmod 0550 -R "${BASE_DIR}/etc/tmpfiles.d"
chmod 0550 -R "${BASE_DIR}/etc/modprobe.d"
chmod 0550 -R "${BASE_DIR}/etc/pacman.d/hooks"
chmod 0550 -R "${BASE_DIR}/etc/modules-load.d"
chmod 0550 -R "${BASE_DIR}/etc/NetworkManager"

# Remove Execute Permissions
find "${BASE_DIR}/etc/smd/" -type f -exec chmod 0660 {} \; 2> /dev/null
find "${BASE_DIR}/etc/udev/" -type f -exec chmod 0444 {} \; 2> /dev/null
find "${BASE_DIR}/etc/iptables/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/sysctl.d/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/sysctl.d/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/security/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/tmpfiles.d/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/modprobe.d/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/pacman.d/hooks/" -type f -exec chmod 0440 {} \; 2> /dev/null
find "${BASE_DIR}/etc/modules-load.d/" -type f -exec chmod 0440 {} \; 2> /dev/null

# Remove Everyone Read
chmod 0440 /etc/ssh/* 2> /dev/null
chmod 0444 /etc/ssh/*.pub 2> /dev/null
chmod 0440 "${BASE_DIR}/etc/locale.gen"
chmod 0440 "${BASE_DIR}/etc/vconsole.conf"
chmod 0444 "${BASE_DIR}/etc/ssh/ssh_config"
chmod 0440 "${BASE_DIR}/etc/ssh/sshd_config"
chmod 0440 "${BASE_DIR}/etc/mkinitcpio.conf"
chmod 0440 "${BASE_DIR}/etc/NetworkManager/NetworkManager.conf"

# Setup Ownership
chown root:cups -R "/etc/cups"
chown root:proxy -R "/etc/squid"
chown root:root "/usr/share/applications/mimeinfo.cache"

# Group Helper Permissions
chown root:root "${BASE_DIR}/bin/gh"
chmod 4755 "${BASE_DIR}/bin/gh"

# Theme Permissions
chown root:root -R "/usr/share/icons/DarkSky" 2> /dev/null
chown root:root -R "/usr/share/themes/DarkSky" 2> /dev/null
chmod 0755 -R "/usr/share/icons/DarkSky" 2> /dev/null
chmod 0755 -R "/usr/share/themes/DarkSky" 2> /dev/null
find "/usr/share/icons/DarkSky" -type f -exec chmod 0644 {} \; 2> /dev/null
find "/usr/share/themes/DarkSky" -type f -exec chmod 0644 {} \; 2> /dev/null

# SMD Permissions
chmod 0640 /var/cache/smd/*.json
chmod 0555 -R "${BASE_DIR}/usr/lib/smd"
chmod 0555 -R "${BASE_DIR}/usr/lib/smd/bin"
chmod 0550 -R "${BASE_DIR}/usr/lib/smd/sbin"
chmod 0644 "${BASE_DIR}/var/cache/smd/constants.json"
chmod 0555 "${BASE_DIR}/usr/lib/smd/libexec/smd-video"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-daemon"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-key-eject"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-power-low"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-suspend-pre"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-suspend-post"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-hibernate-pre"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-hibernate-post"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-power-attached"
chmod 0550 "${BASE_DIR}/usr/lib/smd/libexec/smd-power-detached"
find "${BASE_DIR}/usr/lib/smd/lib/" -type f -exec chmod 0444 {} \;

# Hydra Permissions
chown kvm:root "/usr/lib/smd/static/nginx.conf"
chown kvm:root "${BASE_DIR}/usr/lib/smd/static/nginx.conf"
chmod 0440 "${BASE_DIR}/usr/lib/smd/static/nginx.conf"
chmod 0440 "/usr/lib/smd/static/nginx.conf"

# Secureboot Key Permissons
chown root:root -R "/opt/secureboot"
chmod 0500 -R "/opt/secureboot"
chmod 0400 /opt/secureboot/*

# Backup Key Permissions
chown root:root /etc/smd/*.key
chown root:root /etc/smd/*.ssh
chown root:root "/var/cache/smd/backup"
chmod 0400 /etc/smd/*.key
chmod 0400 /etc/smd/*.ssh
chmod 0750 "/var/cache/smd/backup"

# Remove Drun Permissions
chmod 0400 /usr/share/applications/exo-* 2> /dev/null
chmod 0400 /usr/share/applications/gcr-* 2> /dev/null
chmod 0400 /usr/share/applications/wine* 2> /dev/null
chmod 0400 /usr/share/applications/*qt4* 2> /dev/null
chmod 0400 /usr/share/applications/gtk3-* 2> /dev/null
chmod 0400 /usr/share/applications/zenmap* 2> /dev/null
chmod 0400 /usr/share/applications/geoclue-* 2> /dev/null
chmod 0400 /usr/share/applications/*scangear* 2> /dev/null
chmod 0400 /usr/share/applications/*autostart* 2> /dev/null
chmod 0400 /usr/share/applications/feh.desktop 2> /dev/null
chmod 0400 /usr/share/applications/cups.desktop 2> /dev/null
chmod 0400 /usr/share/applications/bssh.desktop 2> /dev/null
chmod 0400 /usr/share/applications/bvnc.desktop 2> /dev/null
chmod 0400 /usr/share/applications/xdvi.desktop 2> /dev/null
chmod 0400 /usr/share/applications/htop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/rofi.desktop 2> /dev/null
chmod 0400 /usr/share/applications/kitty.desktop 2> /dev/null
chmod 0400 /usr/share/applications/qv4l2.desktop 2> /dev/null
chmod 0400 /usr/share/applications/fluid.desktop 2> /dev/null
chmod 0400 /usr/share/applications/slack.desktop 2> /dev/null
chmod 0400 /usr/share/applications/picom.desktop 2> /dev/null
chmod 0400 /usr/share/applications/sudoku.desktop 2> /dev/null
chmod 0400 /usr/share/applications/blocks.desktop 2> /dev/null
chmod 0400 /usr/share/applications/lstopo.desktop 2> /dev/null
chmod 0400 /usr/share/applications/codium.desktop 2> /dev/null
chmod 0400 /usr/share/applications/arduino.desktop 2> /dev/null
chmod 0400 /usr/share/applications/onboard.desktop 2> /dev/null
chmod 0400 /usr/share/applications/qvidcap.desktop 2> /dev/null
chmod 0400 /usr/share/applications/firefox.desktop 2> /dev/null
chmod 0400 /usr/share/applications/VSCodium.desktop 2> /dev/null
chmod 0400 /usr/share/applications/checkers.desktop 2> /dev/null
chmod 0400 /usr/share/applications/gtk-lshw.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hdspconf.desktop 2> /dev/null
chmod 0400 /usr/share/applications/chromium.desktop 2> /dev/null
chmod 0400 /usr/share/applications/geisview.desktop 2> /dev/null
chmod 0400 /usr/share/applications/ticktick.desktop 2> /dev/null
chmod 0400 /usr/share/applications/librewolf.desktop 2> /dev/null
chmod 0400 /usr/share/applications/ristretto.desktop 2> /dev/null
chmod 0400 /usr/share/applications/echomixer.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hdspmixer.desktop 2> /dev/null
chmod 0400 /usr/share/applications/notesnook.desktop 2> /dev/null
chmod 0400 /usr/share/applications/cmake-gui.desktop 2> /dev/null
chmod 0400 /usr/share/applications/vncviewer.desktop 2> /dev/null
chmod 0400 /usr/share/applications/nextcloud.desktop 2> /dev/null
chmod 0400 /usr/share/applications/galculator.desktop 2> /dev/null
chmod 0400 /usr/share/applications/lxshortcut.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hwmixvolume.desktop 2> /dev/null
chmod 0400 /usr/share/applications/xfce4-about.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hdajackretask.desktop 2> /dev/null
chmod 0400 /usr/share/applications/envy24control.desktop 2> /dev/null
chmod 0400 /usr/share/applications/teensy-loader.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.kde.falkon.desktop 2> /dev/null
chmod 0400 /usr/share/applications/avahi-discover.desktop 2> /dev/null
chmod 0400 /usr/share/applications/evernote-client.desktop 2> /dev/null
chmod 0400 /usr/share/applications/telegramdesktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/libfm-pref-apps.desktop 2> /dev/null
chmod 0400 /usr/share/applications/thunar-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/onboard-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/libinput-gestures.desktop 2> /dev/null
chmod 0400 /usr/share/applications/thunar-bulk-rename.desktop 2> /dev/null
chmod 0400 /usr/share/applications/rofi-theme-selector.desktop 2> /dev/null
chmod 0400 /usr/share/applications/pcmanfm-desktop-pref.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.gnome.FileRoller.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.telegram.desktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/youtube-music-desktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/betterdiscord-installer.desktop 2> /dev/null
chmod 0400 /usr/share/applications/xfce4-terminal-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.keepassxc.KeePassXC.desktop 2> /dev/null
