#!/usr/bin/false
# Module: Background (User)
#
# Sets and changes the User's Background.
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

from threading import Thread
from random import choice, seed
from os.path import isfile, isdir, lexists
from os import listdir, mkdir, symlink, unlink
from lib.util import hash_file, remove_file, run, eval_env
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
    command = server.get_config("background.command", None, False)
    if command is not None:
        return _command(server, command)
    del command
    size = server.get_config("background.screen_size", None)
    if size is None:
        size = run(BACKGROUND_EXEC_SIZE, shell=True, wait=True)
        if not isinstance(size, str):
            return server.error("Could not properly get the screen size!")
        server.set_config("background.screen_size", size, True)
    cache = eval_env(BACKGROUND_PATH_CACHE)
    pics = server.get_config("background.directory", DEFAULT_BACKGROUND_PATH)
    if not isinstance(pics, str) or len(pics) == 0:
        return server.warning("Background directory was not specified or empty!")
    pics = eval_env(pics)
    if not isdir(pics):
        try:
            mkdir(pics)
        except OSError as err:
            del size
            del cache
            return server.error(
                f'An exception occurred when attempting to create the user backgrounds directory "{pics}"!',
                err=err,
            )
    if not isdir(cache):
        try:
            mkdir(cache)
        except OSError as err:
            del pics
            del size
            return server.error(
                f'An exception occurred when attempting to create the user backgrounds cache directory "{cache}"!',
                err=err,
            )
    seed()
    try:
        pic = choice(listdir(pics))
    except IndexError as err:
        return server.error(
            "An exception occurred when attempting to select a user background!",
            err=err,
        )
    selected = f"{pics}/{pic}"
    del pic
    try:
        hash = hash_file(selected, ignore_errors=False)
    except OSError as err:
        return server.error(
            f'An exception occurred when attempting to create a hash for the user background "{selected}"!',
            err=err,
        )
    lock = f"{cache}/{hash}.png"
    lockscreen = server.get_config(
        "background.lockscreen", DEFAULT_BACKGROUND_LOCKSCREEN, True
    )
    del hash
    if isinstance(lockscreen, str) or len(lockscreen) == 0:
        lockscreen = eval_env(lockscreen)
        if not isfile(lock):
            BackgroundGenerator(selected, lock, size, server, lockscreen).start()
        else:
            _link(server, lockscreen, lock)
        server.debug(f"Symlink from {lock} to {lockscreen} set!")
    else:
        server.debug(
            "Background lockscreen path is not specified, skipping setting it!"
        )
    del lock
    del lockscreen
    try:
        run(["/usr/bin/feh", "--no-fehbg", "--bg-fill", selected], ignore_errors=False)
    except OSError as err:
        server.error(
            'An exception occurred when attempting to set the user background to "{selected}"!',
            err=err,
        )
    else:
        server.debug(f'Set user background and lockscreen to "{selected}".')
    del pics
    del size
    del cache
    del selected


def _command(server, command):
    if isinstance(command, list):
        command = " ".join(command)
    if not isinstance(command, str):
        server.set_config("background.command", EMPTY, True)
        return server.warning(
            "Client 'background.command' was not a valid str or list!"
        )
    try:
        run(eval_env(command), shell=True, ignore_errors=False)
    except OSError as err:
        server.error(
            f'An exception occurred when attempting to set the background using "{command}"!',
            err=err,
        )
    del command


def _link(server, link, image):
    if lexists(link):
        try:
            unlink(link)
        except OSError as err:
            server.error(
                f'An exception occurred when attempting to unlink the user backround "{image}" to "{link}"!',
                err=err,
            )
    remove_file(link)
    try:
        symlink(image, link)
    except OSError as err:
        server.error(
            f'An exception occurred when attempting to link the user backround "{image}" to "{link}"!',
            err=err,
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
                ],
                ignore_errors=False,
            )
            self.server.info(
                f'Created a user lockscreen background from "{self.pic}", saved to "{self.cache}".'
            )
        except OSError as err:
            return self.server.error(
                f'Exception occurred when attempting to convert user background "{self.pic}"!',
                err=err,
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
