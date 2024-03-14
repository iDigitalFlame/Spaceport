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
## Base Permissions Configuration
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
    echo "Error: root is required!"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Base Permissions
chmod -R u-s "$BASE_DIR"
chmod -R g-s "$BASE_DIR"
chown -R root:root "$BASE_DIR"
chmod -R 0555 "$BASE_DIR"
chmod -R 0555 "${BASE_DIR}/etc"
chmod -R 0555 "${BASE_DIR}/usr"
chmod -R 0555 "${BASE_DIR}/etc/chromium"
chmod -R 0555 "/etc/chromium"

# General No Execute Permission for files
find "${BASE_DIR}/" -xdev -type f -exec chmod 0444 {} \;

# Remove non-root permissions on copied files
find "/" -xdev -group firewall-web -exec chgrp -h root {} \;

# General Execute
chmod -R 0500 "/etc/smd"
chmod -R 0555 "${BASE_DIR}/bin"
chmod -R 0555 "${BASE_DIR}/etc/ssh"
chmod -R 0555 "${BASE_DIR}/etc/udev"
chmod -R 0550 "${BASE_DIR}/etc/squid"
chmod -R 0550 "${BASE_DIR}/etc/security"
chmod -R 0550 "${BASE_DIR}/etc/sysctl.d"
chmod -R 0555 "${BASE_DIR}/var/cache/smd"
chmod -R 0555 "${BASE_DIR}/etc/profile.d"
chmod -R 0550 "${BASE_DIR}/etc/sudoers.d"
chmod -R 0555 "${BASE_DIR}/etc/syscheck.d"
chmod -R 0550 "${BASE_DIR}/etc/tmpfiles.d"
chmod -R 0550 "${BASE_DIR}/etc/modprobe.d"
chmod -R 0550 "${BASE_DIR}/etc/pacman.d/hooks"
chmod -R 0550 "${BASE_DIR}/etc/modules-load.d"
chmod -R 0550 "${BASE_DIR}/etc/NetworkManager"

# Remove Execute Permissions
if [ -e "/var/cache/librewolf.cfg.bak" ]; then
    chmod 0444 "/var/cache/librewolf.cfg.bak"
fi
find "${BASE_DIR}/etc/udev/" -xdev -type f -exec chmod 0444 {} \;
find "${BASE_DIR}/etc/sysctl.d/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/sysctl.d/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/security/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/tmpfiles.d/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/modprobe.d/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/pacman.d/hooks/" -xdev -type f -exec chmod 0440 {} \;
find "${BASE_DIR}/etc/modules-load.d/" -xdev -type f -exec chmod 0440 {} \;

# Remove Everyone Read
chmod 0440 /etc/ssh/*
chmod 0444 /etc/ssh/*.pub
chmod 0440 "${BASE_DIR}/etc/locale.gen"
chmod 0550 "${BASE_DIR}/etc/nftables.conf"
chmod 0440 "${BASE_DIR}/etc/vconsole.conf"
chmod 0444 "${BASE_DIR}/etc/ssh/ssh_config"
chmod 0440 "${BASE_DIR}/etc/ssh/sshd_config"
chmod 0440 "${BASE_DIR}/etc/mkinitcpio.conf"
chmod 0440 "${BASE_DIR}/etc/NetworkManager/NetworkManager.conf"

# Setup Ownership
chown root:cups "/etc/cups"
chown root:proxy "/etc/squid"
chown root:root "/usr/share/applications/mimeinfo.cache"

# Group Helper Permissions
chown root:root "${BASE_DIR}/bin/ghr"
chmod 4755 "${BASE_DIR}/bin/ghr"

# Theme Permissions
chown -R root:root "/usr/share/icons/DarkSky"
chown -R root:root "/usr/share/themes/DarkSky"
chmod -R 0755 "/usr/share/icons/DarkSky"
chmod -R 0755 "/usr/share/themes/DarkSky"
find "/usr/share/icons/DarkSky" -xdev -type f -exec chmod 0644 {} \;
find "/usr/share/themes/DarkSky" -xdev -type f -exec chmod 0644 {} \;
chown -R root:root "/usr/share/icons/MoonlightSky"
chown -R root:root "/usr/share/themes/MoonlightSky"
chmod -R 0755 "/usr/share/icons/MoonlightSky"
chmod -R 0755 "/usr/share/themes/MoonlightSky"
find "/usr/share/icons/MoonlightSky" -xdev -type f -exec chmod 0644 {} \;
find "/usr/share/themes/MoonlightSky" -xdev -type f -exec chmod 0644 {} \;

# Fix Notesnook Icons
linkcheck "/usr/share/icons/hicolor/16x16/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/16x16.png"
linkcheck "/usr/share/icons/hicolor/24x24/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/24x24.png"
linkcheck "/usr/share/icons/hicolor/32x32/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/32x32.png"
linkcheck "/usr/share/icons/hicolor/64x64/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/64x64.png"
linkcheck "/usr/share/icons/hicolor/48x48/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/48x48.png"
linkcheck "/usr/share/icons/hicolor/128x128/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/128x128.png"
linkcheck "/usr/share/icons/hicolor/256x256/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/256x256.png"
linkcheck "/usr/share/icons/hicolor/512x512/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/512x512.png"
linkcheck "/usr/share/icons/hicolor/1024x1024/apps/notesnook.png" "/opt/notesnook/resources/assets/icons/1024x1024.png"

# SMD Permissions
chmod 0640 /var/cache/smd/*.json
chmod -R 0555 "${BASE_DIR}/usr/lib/smd"
chmod -R 0555 "${BASE_DIR}/usr/lib/smd/bin"
chmod -R 0550 "${BASE_DIR}/usr/lib/smd/sbin"
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
find "${BASE_DIR}/usr/lib/smd/lib/" -xdev -type f -exec chmod 0444 {} \;

# Secureboot Key Permissons
chown -R root:root "/opt/secureboot"
chmod -R 0500 "/opt/secureboot"
chmod 0400 /opt/secureboot/*

# Secureboot Signer Permissions
chown root:root "/etc/kernel/cmdline"
chown root:root "/etc/initcpio/post/sign-image"
chmod 0400 "/etc/kernel/cmdline"
chmod 0550 "/etc/initcpio/post/sign-image"
chmod 0400 "${BASE_DIR}/etc/kernel/cmdline"
chmod 0550 "${BASE_DIR}/etc/initcpio/post/sign-image"

# Backup Key Permissions
chown root:root /etc/smd/*.key
chown root:root /etc/smd/*.ssh
chown root:root "/var/cache/smd/backup" 2> /dev/null
chmod 0400 /etc/smd/*.key
chmod 0400 /etc/smd/*.ssh
chmod 0750 "/var/cache/smd/backup" 2> /dev/null

# Don't update the MIME database, ours is fine thx.
linkcheck "/etc/pacman.d/hooks/update-desktop-database.hook" "/dev/null"

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
chmod 0400 /usr/share/applications/vesktop.desktop 2> /dev/null
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
chmod 0400 /usr/share/applications/electron*.desktop 2> /dev/null
chmod 0400 /usr/share/applications/galculator.desktop 2> /dev/null
chmod 0400 /usr/share/applications/lxshortcut.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hwmixvolume.desktop 2> /dev/null
chmod 0400 /usr/share/applications/xfce4-about.desktop 2> /dev/null
chmod 0400 /usr/share/applications/hdajackretask.desktop 2> /dev/null
chmod 0400 /usr/share/applications/envy24control.desktop 2> /dev/null
chmod 0400 /usr/share/applications/teensy-loader.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.kde.falkon.desktop 2> /dev/null
chmod 0400 /usr/share/applications/avahi-discover.desktop 2> /dev/null
chmod 0400 /usr/share/applications/codium-wayland.desktop 2> /dev/null
chmod 0400 /usr/share/applications/evernote-client.desktop 2> /dev/null
chmod 0400 /usr/share/applications/telegramdesktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/libfm-pref-apps.desktop 2> /dev/null
chmod 0400 /usr/share/applications/thunar-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/blueman-adapters.desktop 2> /dev/null
chmod 0400 /usr/share/applications/onboard-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/libinput-gestures.desktop 2> /dev/null
chmod 0400 /usr/share/applications/java-java-openjdk.desktop 2> /dev/null
chmod 0400 /usr/share/applications/thunar-bulk-rename.desktop 2> /dev/null
chmod 0400 /usr/share/applications/codium-uri-handler.desktop 2> /dev/null
chmod 0400 /usr/share/applications/com.ultimaker.cura.desktop 2> /dev/null
chmod 0400 /usr/share/applications/rofi-theme-selector.desktop 2> /dev/null
chmod 0400 /usr/share/applications/jshell-java-openjdk.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.cubocore.CorePDF.desktop 2> /dev/null
chmod 0400 /usr/share/applications/pcmanfm-desktop-pref.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.gnome.FileRoller.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.telegram.desktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/cura-modern-appimage.desktop 2> /dev/null
chmod 0400 /usr/share/applications/jconsole-java-openjdk.desktop 2> /dev/null
chmod 0400 /usr/share/applications/youtube-music-desktop.desktop 2> /dev/null
chmod 0400 /usr/share/applications/betterdiscord-installer.desktop 2> /dev/null
chmod 0400 /usr/share/applications/xfce4-terminal-settings.desktop 2> /dev/null
chmod 0400 /usr/share/applications/org.keepassxc.KeePassXC.desktop 2> /dev/null
chmod 0400 /usr/share/applications/net.sourceforge.liferea.desktop 2> /dev/null
