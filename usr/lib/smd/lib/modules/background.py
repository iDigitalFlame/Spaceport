#!/usr/bin/false
# Module: Background (User)
#
# Sets and changes the User's Background.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

from threading import Thread
from random import choice, seed
from os import listdir, mkdir, symlink, unlink
from lib.util import hash_file, remove_file, run
from os.path import isfile, isdir, lexists, expanduser, expandvars, islink
from lib.constants import (
    EMPTY,
    HOOK_ROTATE,
    HOOK_STARTUP,
    HOOK_BACKGROUND,
    DIRECTORY_LIBEXEC,
    BACKGROUND_EXEC_SIZE,
    BACKGROUND_PATH_CACHE,
    DEFAULT_BACKGROUND_PATH,
    DEFAULT_BACKGROUND_LOCKSCREEN,
)

HOOKS = {
    HOOK_ROTATE: "background",
    HOOK_STARTUP: "background",
    HOOK_BACKGROUND: "background",
}


def background(server):
    server.debug("Setting User Background..")
    c = server.get_config("background.command")
    if c is not None:
        return _command(server, c)
    del c
    s = server.get_config("background.screen_size", None)
    # NOTE(dij): We need to validate that size is a NUMxNUM value.
    #            Zero it if not. (Security/Command issue).
    if isinstance(s, str) and len(s) > 0:
        i = s.find("x")
        if i < 3:
            server.set_config("background.screen_size", "", True)
            server.warning(
                f'Validation error in "background.screen_size": "{s}", clearing it!'
            )
            s = None
        else:
            try:
                int(s[:i], 10)
                int(s[i + 1], 10)
            except ValueError:
                server.set_config("background.screen_size", "", True)
                server.warning(
                    f'Validation error in "background.screen_size": "{s}", clearing it!'
                )
                s = None
        del i
    if not isinstance(s, str) or len(s) == 0 or "x" not in s or ";" in s:
        s = run(BACKGROUND_EXEC_SIZE, shell=True, wait=True, errors=False)
        if not isinstance(s, str) or "x" not in s:
            # NOTE(dij): Let's reset it here too, it already is invalid anyway.
            server.set_config("background.screen_size", "", True)
            return server.error("Could not properly get the Screen Size!")
        server.set_config("background.screen_size", s, True)
    c = expandvars(expanduser(BACKGROUND_PATH_CACHE))
    p = server.get_config("background.directory", DEFAULT_BACKGROUND_PATH)
    if not isinstance(p, str) or len(p) == 0:
        return server.warning("Background directory was not specified or empty!")
    p = expandvars(expanduser(p))
    if not isdir(p):
        try:
            mkdir(p)
        except OSError as err:
            del s
            del c
            return server.error(f'Error creating Background directory "{p}"!', err=err)
    if not isdir(c):
        try:
            mkdir(c)
        except OSError as err:
            del s
            del p
            return server.error(
                f'Error creating Background cache directory "{c}"!', err=err
            )
    elif islink(c):
        return server.error(f'Background cache directory "{p}" cannot be a symlink!')
    seed(version=2)
    try:
        v = choice(listdir(p))
    except IndexError as err:
        return server.error("Error selecting a Background!", err=err)
    x = f"{p}/{v}"
    del v
    del p
    try:
        h = hash_file(x)
    except OSError as err:
        return server.error(f'Error hashing the Background "{x}"!', err=err)
    q = f"{c}/{h}.png"
    w = server.get_config("background.lockscreen", DEFAULT_BACKGROUND_LOCKSCREEN, True)
    del h
    if isinstance(w, str) or len(w) == 0:
        w = expandvars(expanduser(w))
        if not isfile(q):
            BackgroundGenerator(x, q, s, server, w).start()
        else:
            _link(server, w, q)
        server.debug(f'Symlink from "{q}" to "{w}" set!')
    else:
        server.debug("Background Lockscreen path is not specified, skipping it!")
    del q
    del w
    try:
        run(["/usr/bin/feh", "--no-fehbg", "--bg-fill", x])
    except OSError as err:
        server.error(f'Error setting the user Background to "{x}"!', err=err)
    else:
        server.debug(f'Set user Background and Lockscreen to "{x}".')
    del s
    del c
    del x


def _command(server, command):
    if isinstance(command, list):
        command = " ".join(command)
    if not isinstance(command, str):
        server.set_config("background.command", EMPTY, True)
        return server.warning(
            'Setting "background.command" was not a valid String or List!'
        )
    server.debug(f'Running user Background command "{command}"..')
    try:
        # NOTE(dij): We can't really protect the user here, since they
        #            supply the command to use. Technically speaking this
        #            would be a method of user-land persistance. *shrug*
        run(expandvars(expanduser(command)), shell=True)
    except OSError as err:
        server.error(f'Error setting the Background with "{command}"!', err=err)
    del command


def _link(server, link, image):
    if lexists(link):
        try:
            unlink(link)
        except OSError as err:
            server.error(
                f'Error unlinking the user Backround "{image}" to "{link}"!', err=err
            )
    remove_file(link)
    try:
        symlink(image, link)
    except OSError as err:
        server.error(
            f'Error linking the user Backround "{image}" to "{link}"!', err=err
        )


class BackgroundGenerator(Thread):
    def __init__(self, pic, pic_cache, pic_size, pic_server, lock):
        Thread.__init__(self, name="SMBBackgroundGenThread", daemon=True)
        self.pic = pic
        self.lock = lock
        self.size = pic_size
        self.cache = pic_cache
        self.server = pic_server

    def run(self):
        if isfile(self.cache):
            return
        try:
            run(
                [
                    f"{DIRECTORY_LIBEXEC}/smd-convert-picture",
                    self.size,
                    self.pic,
                    self.cache,
                ]
            )
            self.server.info(
                f'Created a user Lockscreen Background from "{self.pic}", saved to "{self.cache}".'
            )
        except OSError as err:
            return self.server.error(
                f'Error converting user Background "{self.pic}"!', err=err
            )
        _link(
            self.server,
            self.lock,
            self.cache,
        )
        del self.pic
        del self.lock
        del self.size
        del self.cache
        del self.server
