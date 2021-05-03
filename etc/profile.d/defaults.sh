#!/usr/bin/bash
# System Management Daemon - Spaceport
# iDigitalFlame
#
# User Profile Defaults Script.

umask 027

export PIP_USER=yes
export PYTHONUSERBASE="$HOME/.local/lib/python"

if [ -d "$HOME/.local/bin" ]; then
    PATH=$PATH:$HOME/.local/bin
fi

if [ ! -d "$PYTHONUSERBASE/bin" ]; then
    mkdir -p "$PYTHONUSERBASE/bin"
fi

PATH=/usr/local/bin:$PATH:$PYTHONUSERBASE/bin
export PATH

if [ ! -d "/tmp/.cache/$USER" ]; then
    mkdir "/tmp/.cache/$USER"
fi

if [ -d "$HOME/.surf" ]; then
    rm -rf "$HOME/.surf/cache" 2> /dev/null
    mkdir "/tmp/.cache/$USER/surf" 2> /dev/null
    ln -s "/tmp/.cache/$USER/surf" "$HOME/.surf/cache"
fi
