#!/usr/bin/dash

if [ "$USER" = "root" ]; then
    HISTSIZE=500
    HISTFILESIZE=0
    HISTFILE=/dev/null
fi
