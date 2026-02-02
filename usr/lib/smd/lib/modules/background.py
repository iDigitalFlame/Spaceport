################################
### iDigitalFlame  2016-2026 ###
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
#
# Copyright (C) 2016 - 2026 iDigitalFlame
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

# Module: User/Background
#   Sets and changes the User's Background, optionally changes the Lockscreen
#   image to match the background selected.

from random import Random
from lib.sway import displays
from lib.util.exec import stop, nulexec
from os import mkdir, unlink, listdir, symlink
from lib.util import nes, num, boolean, cancel_nul
from lib.util.file import expand, hash_file, remove_file
from os.path import isdir, exists, isfile, islink, lexists, splitext
from lib.constants.config import (
    DIRECTORY_LIBEXEC,
    BACKGROUND_PATH_CACHE,
    BACKGROUND_PATH_EXTENSIONS,
)
from lib.constants import (
    HOOK_RELOAD,
    HOOK_DISPLAY,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
    HOOK_BACKGROUND,
)
from lib.constants.defaults import (
    DEFAULT_BACKGROUND_PATH,
    DEFAULT_BACKGROUND_METHOD,
    DEFAULT_BACKGROUND_SWITCH,
    DEFAULT_BACKGROUND_METHODS,
    DEFAULT_BACKGROUND_LOCKSCREEN,
)

HOOKS = {
    HOOK_RELOAD: "Background.reload",
    HOOK_DISPLAY: "Background.hook",
    HOOK_STARTUP: "Background.hook",
    HOOK_SHUTDOWN: "Background.hook",
    HOOK_BACKGROUND: "Background.hook",
}


class Background(object):
    __slots__ = (
        "_dir",
        "_src",
        "_lock",
        "_rand",
        "_proc",
        "_size",
        "_auto",
        "_handle",
        "_method",
        "_enabled",
        "_lockscreen",
    )

    def __init__(self):
        self._dir = expand(BACKGROUND_PATH_CACHE)
        self._src = None
        self._auto = None
        self._lock = False
        self._rand = Random()
        self._size = None
        self._proc = None
        self._handle = None
        self._method = None
        self._enabled = None
        self._lockscreen = None

    def setup(self, server):
        self._enabled = boolean(server.get("background.enabled", True, True))
        if not self._enabled:
            return
        try:
            self._auto = num(
                server.get("background.auto_change", DEFAULT_BACKGROUND_SWITCH, True),
                False,
            )
        except ValueError:
            server.warning(
                '[m/background]: Config value "background.auto_change" is invalid (must be a positive number), '
                "using the default value!"
            )
            self._auto = DEFAULT_BACKGROUND_SWITCH
        self._src = expand(
            server.get("background.directory", DEFAULT_BACKGROUND_PATH, True)
        )
        if not nes(self._src):
            server.warning(
                '[m/background]: Config value "background.directory" is invalid (must be a non-empty string), '
                "using the default value!"
            )
            self._src = expand(DEFAULT_BACKGROUND_PATH)
        self._lockscreen = expand(
            server.get("background.lockscreen", DEFAULT_BACKGROUND_LOCKSCREEN, True)
        )
        if self._auto > 0:
            self._handle = server.task(self._auto, self._change, (server,), priority=20)
        if not isdir(self._src):
            server.warning(
                f'[m/background]: Background source path "{self._src}" does not exist or is is not a directory!'
            )
        self._method = server.get("background.method", DEFAULT_BACKGROUND_METHOD, True)
        if not nes(self._method):
            self._method = None
        else:
            self._method = self._method.lower()
        if self._method not in DEFAULT_BACKGROUND_METHODS:
            server.warning(
                '[m/background]: Config value "background.method" is invalid (must be one of the following values '
                f"{DEFAULT_BACKGROUND_METHODS}) using the default value!"
            )
            self._method = None

    def reload(self, server):
        self._handle = cancel_nul(server, self._handle)
        self._lock, self._size = False, None
        server.debug(
            "[m/background]: Reloading and clearing cached background settings.."
        )
        self.setup(server)

    def _change(self, server):
        self._background(server)
        # Guards against a race that may happen against the Dispatcher and a
        # reload request happening at the same time.
        if self._auto == 0 or not self._enabled:
            return
        self._handle = server.task(self._auto, self._change, (server,), priority=20)

    def _background(self, server):
        if not self._enabled:
            return
        if not isdir(self._src):
            return server.error(
                f'[m/background]: Background source path "{self._src}" does not exist or is is not a directory!'
            )
        if self._size is None and not self._screen_size(server):
            return
        if self._lock:
            return server.info(
                "[m/background]: Not setting Background until the conversion Task is complete!"
            )
        # Start the Guard against changing the Background.
        self._lock = True
        p = self._select_picture(server)
        if p is None:
            self._lock = False
            return
        self._set_background(server, p)
        # NOTE(dij): Guard might be cleared here if the func returns None.
        #
        #            This is an inline if as it'll return None instead of False
        #            and we want this value to always be a bool.
        self._lock = True if self._set_lockscreen(server, p) else False

    def _screen_size(self, server):
        x, y = 0, 0
        try:
            for i in displays():
                if not i.active or i.width == 0 or i.height == 0:
                    continue
                if x is None or i.width > x:
                    x = i.width
                if y is None or i.height > y:
                    y = i.height
        except OSError as err:
            return server.error(
                "[m/background]: Cannot not get Display size details!", err
            )
        if x is None or y is None or x == 0 or y == 0:
            return server.error("[m/background]: Cannot detect any active Displays!")
        self._size = (x, y)
        server.debug(f"[m/background]: Detected a max Display size of {x}x{y}.")
        del x, y
        return True

    def _link(self, server, image):
        if not nes(self._lockscreen):
            return server.debug(
                "[m/background]: Lockscreen path is empty, skipping linking!"
            )
        if lexists(self._lockscreen):
            try:
                unlink(self._lockscreen)
            except OSError as err:
                server.error(
                    f'[m/background]: Cannot unlink the symlink path "{self._lockscreen}"!',
                    err,
                )
        if exists(self._lockscreen) and not islink(self._lockscreen):
            return server.error(
                f'[m/background]: Not removing non-symlink file "{self._lockscreen}"!'
            )
        remove_file(self._lockscreen, True)
        try:
            symlink(image, self._lockscreen)
        except OSError as err:
            server.error(
                f'[m/background]: Cannot link the Background path "{image}" to "{self._lockscreen}"!',
                err,
            )
        else:
            server.debug(
                f'[m/background]: Created a Lockscreen Background image from "{image}".'
            )
        finally:
            # Catch anything else here to ensure the lock is cleared.
            self._lock = False

    def hook(self, server, message):
        if message.header() == HOOK_DISPLAY:
            if self._size is not None:
                self._size = None
                server.debug(
                    "[m/background]: Clearing the size cache due to a Display change."
                )
        elif message.header() == HOOK_SHUTDOWN:
            if self._proc is not None:
                stop(self._proc)
            self._handle = cancel_nul(server, self._handle)
            return
        if not self._enabled:
            return
        self._background(server)

    def _select_picture(self, server):
        try:
            e = listdir(self._src)
        except OSError as err:
            return server.error(
                f'[m/background]: Cannot list the directory path "{self._src}"!',
                err,
            )
        a = list()
        for i in e:
            if len(i) < 2 or not isfile(f"{self._src}/{i}"):
                continue
            _, v = splitext(i.lower())
            if v in BACKGROUND_PATH_EXTENSIONS:
                a.append(i)
        del e
        if len(a) == 0:
            return server.error(
                f'[m/background]: No acceptable image types found in "{self._src}"!'
            )
        try:
            s = self._rand.choice(a)
        except (ValueError, IndexError) as err:
            return server.error(
                f'[m/background]: Cannot select a valid image from "{self._src}"!',
                err,
            )
        if not nes(s):
            return server.error(
                f'[m/background]: Cannot select a valid image from "{self._src}"!'
            )
        f = f"{self._src}/{s}"
        del a, s
        return f

    def _set_lockscreen(self, server, bg):
        if not nes(self._lockscreen):
            return server.debug(
                "[m/background]: Lockscreen path is empty, skipping setup!"
            )
        if not isdir(self._dir):
            try:
                mkdir(self._dir)
            except OSError as err:
                return server.error(
                    f'[m/background]: Cannot create the Background cache directory "{self._dir}"!',
                    err,
                )
        elif islink(self._dir):
            return server.error(
                f'[m/background]: Background cache path "{self._dir}" cannot be a symlink!'
            )
        # If "self._method" is the "native" method, then we don't need to convert the
        # background file, we can just directly symlink it.
        if self._method is None or self._method == "native":
            # This explicitly returns "None" so it won't lock.
            return self._link(server, bg)
        try:
            h = hash_file(bg)
        except OSError as err:
            return server.error(f'[m/background]: Cannot hash the file "{bg}"!', err)
        t = f"{self._dir}/{h}.jpg"
        del h
        if isfile(t):
            self._link(server, t)
            return server.debug(
                f'[m/background]: Created a symlink from "{t}" to "{self._lockscreen}" set!'
            )
        server.debug(
            f'[m/background]: Created a Task to convert "{bg}" to "{t}" using method "{self._method}".'
        )
        try:
            server.watch(
                nulexec(
                    [
                        f"{DIRECTORY_LIBEXEC}/smd-convert-picture",
                        self._method,
                        f"{self._size[0]}",
                        f"{self._size[1]}",
                        bg,
                        t,
                    ],
                ),
                self._link,
                (server, t),
            )
        except OSError as err:
            return server.error(
                "[m/background]: Cannot start the Background conversion Task!",
                err,
            )
        del t
        return True

    def _set_background(self, server, file):
        # Cache the process and copy the object to prevent the screen from
        # flickering too much.
        o = self._proc
        self._proc = None
        try:
            self._proc = nulexec(
                ["/usr/bin/swaybg", "--mode", "fill", "--output", "*", "--image", file]
            )
        except OSError as err:
            return server.error(
                f'[m/background]: Cannot set the user Background to "{file}"!', err
            )
        server.debug(
            f'[m/background]: Set the user Background to "{file}", PID({self._proc.pid}).'
        )
        stop(o)
        del o
