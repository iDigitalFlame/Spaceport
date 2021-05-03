#!/usr/bin/bash

if [ $UID -eq 0 ]; then
    HISTSIZE=500
    HISTFILESIZE=0
    HISTFILE=/dev/null
fi
