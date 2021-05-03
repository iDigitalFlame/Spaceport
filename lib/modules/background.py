#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: Background (User)
#
# Sets and changes the User's Background.
# Updated 10/2018

from random import choice
from threading import Thread
from os.path import isfile, isdir, join
from os import environ, listdir, mkdir, symlink
from lib.util import hash_file, remove_file, run
from lib.constants import (
    HOOK_MONITOR,
    HOOK_ROTATE,
    HOOK_STARTUP,
    HOOK_BACKGROUND,
    DIRECTORY_LIBEXEC,
    BACKGROUND_STANDARD,
    BACKGROUND_DIRECTORY_DEFAULT,
    BACKGROUND_SIZE,
    BACKGROUND_DIRECTORY_CACHE,
    BACKGROUND_LOCKSCREEN,
)

HOOKS = {
    HOOK_ROTATE: "set_background",
    HOOK_MONITOR: "set_background",
    HOOK_STARTUP: "set_background",
    HOOK_BACKGROUND: "set_background",
}
HOOKS_SERVER = None


def _set_background(server):
    server.debug("Setting User Background..")
    if "backgrounds" not in server:
        _set_background_standard(server)
        return
    size = server.config("background_size", None)
    if size is None:
        size = run(BACKGROUND_SIZE, shell=True, wait=2)
        if not isinstance(size, str):
            server.error("An exception occured when attempting to get the screen size!")
            return
        else:
            server.set("background_size", size)
    cache = join(environ["HOME"], BACKGROUND_DIRECTORY_CACHE)
    pics = server.config(
        "backgrounds", BACKGROUND_DIRECTORY_DEFAULT.replace("{home}", environ["HOME"])
    )
    if not isdir(pics):
        try:
            mkdir(pics)
        except OSError as err:
            server.error(
                'An exception occured when attempting to create the user backgrounds directory "%s"!'
                % pics,
                err=err,
            )
            del pics
            del size
            del cache
            return
    if not isdir(cache):
        try:
            mkdir(cache)
        except OSError as err:
            server.error(
                'An exception occured when attempting to create the user backgrounds cache directory "%s"!'
                % cache,
                err=err,
            )
            del pics
            del size
            del cache
            return
    try:
        pic = choice(listdir(pics))
    except IndexError as err:
        server.error(
            "An exception occured when attempting to select a user background!", err=err
        )
    else:
        selected = join(pics, pic)
        try:
            hash = hash_file(selected, ignore_errors=False)
        except OSError as err:
            server.error(
                'An exception occured when attempting to create a hash for the user background "%s"!'
                % selected,
                err=err,
            )
        else:
            lock = join(cache, "%s.png" % hash)
            del hash
            if not isfile(lock):
                BackgroundGenerator(selected, lock, size, server).start()
            else:
                _set_link(server, lock)
            del lock
            try:
                run(
                    ["/usr/bin/feh", "--no-fehbg", "--bg-fill", selected],
                    ignore_errors=False,
                )
            except OSError as err:
                server.error(
                    'An exception occured when attempting to set the user background to "%s"!'
                    % selected,
                    err=err,
                )
            else:
                server.debug('Set user background and lockscreen to "%s".' % selected)
        finally:
            del selected
    finally:
        del pics
        del size
        del cache


def _set_link(server, image):
    link = join(environ["HOME"], BACKGROUND_LOCKSCREEN)
    remove_file(link)
    try:
        symlink(image, link)
    except OSError as err:
        server.error(
            'An exception occured when attempting to link the user backround "%s" to "%s"!'
            % (image, link),
            err=err,
        )
    finally:
        del link


def _set_background_standard(server):
    command = server.config("background", BACKGROUND_STANDARD)
    if isinstance(command, str):
        command = command.split(" ")
    if isinstance(command, list):
        try:
            run(" ".join(command), shell=True, ignore_errors=False)
        except OSError as err:
            server.error(
                'An exception occured when attempting to set the background using "%s"!'
                % " ".join(command),
                err=err,
            )
    else:
        del server["background"]
    del command


def set_background(server, message=None):
    _set_background(server)


class BackgroundGenerator(Thread):
    def __init__(self, pic, pic_cache, pic_size, pic_server):
        Thread.__init__(self)
        self.pic = pic
        self.size = pic_size
        self.cache = pic_cache
        self.server = pic_server

    def run(self):
        if isfile(self.cache):
            return
        try:
            run(
                [
                    join(DIRECTORY_LIBEXEC, "smd-covert-picture"),
                    self.size,
                    self.pic,
                    self.cache,
                ],
                ignore_errors=False,
            )
            self.server.debug(
                'Created a user background from "%s", saved to "%s".'
                % (self.pic, self.cache)
            )
        except OSError as err:
            self.server.error(
                'Exception occured when attempting to convert user background "%s"!'
                % self.pic,
                err=err,
            )
        else:
            _set_link(self.server, self.cache)
        del self.pic
        del self.size
        del self.cache
        del self.server


# EOF
