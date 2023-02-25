#!/usr/bin/dash
# Build the DarkSky icon theme

if ! [ "$USER" = "root" ]; then
    echo "Only root can do this!"
    exit 1
fi

if ! [ -d "/usr/share/icons/kora" ]; then
    echo '"/usr/share/icons/kora" does not exist!'
    exit 1
fi
if ! [ -d "/usr/share/icons/Flatery-Dark" ]; then
    echo '"/usr/share/icons/Flatery-Dark" does not exist!'
    exit 1
fi
if ! [ -d "/usr/share/icons/Vimix-cursors" ]; then
    echo '"/usr/share/icons/Vimix-cursors" does not exist!'
    exit 1
fi

THEME_DIR="/usr/share/icons/DarkSky"
if [ -e "$THEME_DIR" ]; then
    rm -rf "$THEME_DIR"
fi

if ! cp -R "/usr/share/icons/Flatery-Dark" "$THEME_DIR"; then
    exit 0
fi

rm -rf "${THEME_DIR}/apps" 2> /dev/null
rm -f "${THEME_DIR}/index.theme" 2> /dev/null
rm -f "${THEME_DIR}/icon-theme.cache" 2> /dev/null
find "${THEME_DIR}/actions" -type l -name "go-*" -delete 2> /dev/null
find "${THEME_DIR}/actions" -type f -name "go-*" -delete 2> /dev/null

ln -s "/usr/share/icons/kora/apps" "${THEME_DIR}/apps" 2> /dev/null
ln -s "/usr/share/icons/Vimix-cursors/cursors" "${THEME_DIR}/cursors" 2> /dev/null
ln -s "/usr/share/themes/DarkSky/icons.theme" "${THEME_DIR}/index.theme" 2> /dev/null

for icon in $(find "/usr/share/icons/kora/actions" -type f -name "go-*" -ls | awk '{print $11}'); do
    for d in "${THEME_DIR}"/actions/*; do
        if [ -d "${THEME_DIR}/actions/${d}" ]; then
            ln -s "$icon" "${THEME_DIR}/actions/${d}/" 2> /dev/null
        fi
    done
done

chown root:root -R "$THEME_DIR"
find "$THEME_DIR" -type d -exec chmod 0755 {} \;
find "$THEME_DIR" -type f -exec chmod 0644 {} \;
exit 0
