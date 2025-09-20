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
## Themes Configuration
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

if ! [ -d "/usr/share/icons/DarkSky" ]; then
    dash "/usr/share/themes/DarkSky/build-icons.sh"
fi
if ! [ -d "/usr/share/icons/MoonlightSky" ]; then
    dash "/usr/share/themes/MoonlightSky/build-icons.sh"
fi

find "/usr/share/icons" -xdev -xtype l -delete
find "/usr/share/themes" -xdev -xtype l -delete
find "/usr/share/icons/DarkSky" -xdev -type f -name .directory -delete
find "/usr/share/themes/DarkSky" -xdev -type f -name .directory -delete
find "/usr/share/icons/MoonlightSky" -xdev -type f -name .directory -delete
find "/usr/share/themes/MoonlightSky" -xdev -type f -name .directory -delete

# Application Icon Links
linkcheck "/usr/share/icons/hicolor/scalable/apps/qtws.svg"                           "/usr/share/icons/kora/apps/scalable/youtube-music.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/spicy.svg"                          "/usr/share/icons/kora/apps/scalable/variety.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/codium.svg"                         "/usr/share/icons/kora/apps/scalable/vscodium.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/xfreerdp.svg"                       "/usr/share/icons/kora/apps/scalable/preferences-system-windows-actions.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/wlfreerdp.svg"                      "/usr/share/icons/kora/apps/scalable/preferences-system-windows-actions.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/pavucontrol-qt.svg"                 "/usr/share/icons/kora/apps/scalable/kmix.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/ultimaker-cura.svg"                 "/usr/share/icons/kora/apps/scalable/cura-icon.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/UltiMaker-Cura.svg"                 "/usr/share/icons/kora/apps/scalable/cura-icon.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/blueman-manager.svg"                "/usr/share/icons/kora/apps/scalable/bluetooth.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/codium-url-handler.svg"             "/usr/share/icons/kora/apps/scalable/vscodium.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/gtk-dialog-warning.svg"             "/usr/share/icons/kora/apps/scalable/firewall-config.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/mcpelauncher-client.svg"            "/usr/share/icons/kora/apps/scalable/mcpelauncher-ui-qt.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/com.obsproject.studio.svg"          "/usr/share/icons/kora/apps/scalable/obs.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/org.keepassxc.keepassxc.svg"        "/usr/share/icons/kora/apps/scalable/keepass.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/io.mrarm.mcpelauncher-ui-qt.svg"    "/usr/share/icons/kora/apps/scalable/mcpelauncher-ui-qt.svg"
linkcheck "/usr/share/icons/hicolor/scalable/apps/org.gnome.seahorse.application.svg" "/usr/share/icons/kora/apps/scalable/seahorse.svg"
