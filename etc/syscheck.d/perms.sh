#!/usr/bin/bash
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Permissions Configuration.

if [ $UID -ne 0 ]; then
    printf "[!] Only root can do this!\n"
    exit 1
fi

BASE_DIR="/opt/spaceport"

# Base Permissions
chown root:root -R "$BASE_DIR"
chmod 555 -R "$BASE_DIR"
chmod 555 -R "$BASE_DIR/etc"
chmod 555 -R "$BASE_DIR/usr"

# General No Execute Permission for files
find "$BASE_DIR/" -type f -exec chmod 444 {} \; 2> /dev/null

# General Execute
chmod 555 -R "$BASE_DIR/bin"
chmod 550 -R "$BASE_DIR/etc/smd"
chmod 555 -R "$BASE_DIR/etc/ssh"
chmod 550 -R "$BASE_DIR/etc/udev"
chmod 550 -R "$BASE_DIR/etc/lightdm"
chmod 550 -R "$BASE_DIR/etc/iptables"
chmod 550 -R "$BASE_DIR/etc/security"
chmod 550 -R "$BASE_DIR/etc/sysctl.d"
chmod 555 -R "$BASE_DIR/etc/profile.d"
chmod 550 -R "$BASE_DIR/etc/sudoers.d"
chmod 555 -R "$BASE_DIR/etc/syscheck.d"
chmod 550 -R "$BASE_DIR/etc/tmpfiles.d"
chmod 550 -R "$BASE_DIR/etc/modprobe.d"
chmod 550 -R "$BASE_DIR/etc/pacman.d/hooks"
chmod 550 -R "$BASE_DIR/etc/modules-load.d"
chmod 550 -R "$BASE_DIR/etc/NetworkManager"

# Remove Execute Permissions
find "$BASE_DIR/etc/smd/" -type f -exec chmod 660 {} \; 2> /dev/null
find "$BASE_DIR/etc/udev/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/lightdm/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/iptables/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/sysctl.d/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/sysctl.d/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/security/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/tmpfiles.d/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/modprobe.d/" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/pacman.d/hooks" -type f -exec chmod 440 {} \; 2> /dev/null
find "$BASE_DIR/etc/modules-load.d/" -type f -exec chmod 440 {} \; 2> /dev/null

# Remove Everyone Read
chmod 440 /etc/ssh/* 2> /dev/null
chmod 444 /etc/ssh/*.pub 2> /dev/null
chmod 440 "$BASE_DIR/etc/locale.gen"
chmod 440 "$BASE_DIR/etc/chrony.conf"
chmod 440 "$BASE_DIR/etc/chrony.conf"
chmod 440 "$BASE_DIR/etc/vconsole.conf"
chmod 444 "$BASE_DIR/etc/ssh/ssh_config"
chmod 440 "$BASE_DIR/etc/ssh/sshd_config"
chmod 440 "$BASE_DIR/etc/mkinitcpio.conf"
chmod 440 "$BASE_DIR/etc/NetworkManager/NetworkManager.conf"

# Setup Ownership
chown root:cups -R "/etc/cups"
chown root:lightdm -R "/etc/lightdm"
chown root:lightdm -R "$BASE_DIR/etc/lightdm"
chown root:chrony "$BASE_DIR/etc/chrony.conf"

# Hydra Permissions
chmod 440 "$BASE_DIR/usr/lib/smd/assets/nginx.conf"
chmod 550 -R "/usr/lib/smd/assets/novnc"
chmod 550 -R "/usr/lib/smd/assets/websockify"
chown kvm:root "$BASE_DIR/usr/lib/smd/assets/nginx.conf"
chown kvm:root -R "/usr/lib/smd/assets/novnc"
chown kvm:root -R "/usr/lib/smd/assets/websockify"
find "/usr/lib/smd/assets/novnc/" -type f -exec chmod 440 {} \;
find "/usr/lib/smd/assets/websockify/" -type f -exec chmod 440 {} \;
chmod 550 "/usr/lib/smd/assets/websockify/run"

# SMD Permissions
chmod 555 -R "$BASE_DIR/usr/lib/smd"
chmod 550 -R "$BASE_DIR/usr/lib/smd/sbin"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-video"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-daemon"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-startup"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-hibernate-pre"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-hibernate-post"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-power-attached"
chmod 550 "$BASE_DIR/usr/lib/smd/libexec/smd-power-detached"
find "$BASE_DIR/usr/lib/smd/lib/" -type f -exec chmod 444 {} \;

# Remove Drun Permissions
chmod 400 /usr/share/applications/exo-* 2> /dev/null
chmod 400 /usr/share/applications/gcr-* 2> /dev/null
chmod 400 /usr/share/applications/wine* 2> /dev/null
chmod 400 /usr/share/applications/gtk3-* 2> /dev/null
chmod 400 /usr/share/applications/zenmap* 2> /dev/null
chmod 400 /usr/share/applications/geoclue-* 2> /dev/null
chmod 400 /usr/share/applications/feh.desktop
chmod 400 /usr/share/applications/cups.desktop
chmod 400 /usr/share/applications/bssh.desktop
chmod 400 /usr/share/applications/bvnc.desktop
chmod 400 /usr/share/applications/xdvi.desktop
chmod 400 /usr/share/applications/qv4l2.desktop
chmod 400 /usr/share/applications/fluid.desktop
chmod 400 /usr/share/applications/sudoku.desktop
chmod 400 /usr/share/applications/blocks.desktop
chmod 400 /usr/share/applications/arduino.desktop
chmod 400 /usr/share/applications/compton.desktop
chmod 400 /usr/share/applications/qvidcap.desktop
chmod 400 /usr/share/applications/firefox.desktop
chmod 400 /usr/share/applications/trojita.desktop
chmod 400 /usr/share/applications/checkers.desktop
chmod 400 /usr/share/applications/gtk-lshw.desktop
chmod 400 /usr/share/applications/hdspconf.desktop
chmod 400 /usr/share/applications/chromium.desktop
chmod 400 /usr/share/applications/echomixer.desktop
chmod 400 /usr/share/applications/hdspmixer.desktop
chmod 400 /usr/share/applications/cmake-gui.desktop
chmod 400 /usr/share/applications/vncviewer.desktop
chmod 400 /usr/share/applications/nextcloud.desktop
chmod 400 /usr/share/applications/lxshortcut.desktop
chmod 400 /usr/share/applications/hwmixvolume.desktop
chmod 400 /usr/share/applications/hdajackretask.desktop
chmod 400 /usr/share/applications/envy24control.desktop
chmod 400 /usr/share/applications/teensy-loader.desktop 2> /dev/null
chmod 400 /usr/share/applications/org.kde.falkon.desktop
chmod 400 /usr/share/applications/avahi-discover.desktop
chmod 400 /usr/share/applications/libfm-pref-apps.desktop
chmod 400 /usr/share/applications/libinput-gestures.desktop
chmod 400 /usr/share/applications/pcmanfm-desktop-pref.desktop
chmod 400 /usr/share/applications/org.gnome.FileRoller.desktop
chmod 400 /usr/share/applications/libreoffice-startcenter.desktop
chmod 400 /usr/share/applications/xfce4-terminal-settings.desktop
