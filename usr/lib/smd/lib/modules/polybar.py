#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Module: Polybar (User)
#
# Manages the Polybar process.

from os import environ
from lib.util import stop
from subprocess import Popen, DEVNULL, SubprocessError
from lib.constants import (
    HOOK_DAEMON,
    HOOK_TABLET,
    HOOK_SHUTDOWN,
    HOOK_MONITOR,
    HOOK_ROTATE,
    HOOK_RELOAD,
    POLYBAR_DEFAULT,
    TABLET_STATE_TABLET,
    TABLET_STATE_LAPTOP,
)

HOOKS = {
    HOOK_DAEMON: "Polybar.thread",
    HOOK_ROTATE: "Polybar.hook",
    HOOK_TABLET: "Polybar.hook",
    HOOK_MONITOR: "Polybar.hook",
    HOOK_SHUTDOWN: "Polybar.hook",
    HOOK_RELOAD: "Polybar.setup",
}
HOOKS_SERVER = None


class Polybar(object):
    def __init__(self):
        self.bar = None
        self.bars = None
        self.mode = False
        self.running = False

    def setup(self, server):
        self.bars = server.config("polybar_bars", POLYBAR_DEFAULT)
        if not isinstance(self.bars, dict):
            self.bars = server.set("polybar_bars", POLYBAR_DEFAULT)

    def thread(self, server):
        if self.bar is None or (self.bar is not None and self.bar.poll() is not None):
            self.restart(server, True)

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
            self.restart(server, False)
        elif message.header() == HOOK_ROTATE:
            self.restart(server, False)
        elif message.header() == HOOK_MONITOR:
            self.restart(server, False)
        elif message.header() == HOOK_TABLET:
            self.mode = message.get("state", TABLET_STATE_LAPTOP) == TABLET_STATE_TABLET
            self.restart(server, False)

    def restart(self, server, restart=True):
        if self.bar is not None and self.bar.poll() is None:
            stop(self.bar)
            del self.bar
        self.bar = None
        if restart:
            server.debug("Attempting to start Polybar...")
            try:
                self.bar = Popen(
                    [
                        "/usr/bin/polybar",
                        self.bars["tablet" if self.mode else "laptop"],
                        "-q",
                    ],
                    env=environ,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "Attempting to start Polybar raised an exception!", err=err
                )
