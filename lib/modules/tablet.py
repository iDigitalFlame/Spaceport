#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: Tablet (System)
#
# Reports on the System's Tablet orientation status.
# Updated 10/2018

from glob import glob
from os import O_NONBLOCK
from sched import scheduler
from time import time, sleep
from lib.util import read
from lib.structs.message import Message
from fcntl import fcntl, F_GETFL, F_SETFL
from lib.constants import (
    HOOK_TABLET,
    HOOK_DAEMON,
    HOOK_HIBERNATE,
    HOOK_SHUTDOWN,
    TABLET_EVENT_FILE,
    TABLET_LID_FILE,
    TABLET_DISPLAY_GLOB,
    TABLET_STATE_CLOSED,
    TABLET_STATE_LAPTOP,
    TABLET_STATE_TABLET,
    TABLET_STATUS_GLOB,
    HOOK_RELOAD,
    HOOK_MONITOR,
    HOOK_ROTATE,
    HOOK_STARTUP,
    HOOK_NOTIFICATION,
)

HOOKS = None
HOOKS_SERVER = {
    HOOK_DAEMON: "Tablet.thread",
    HOOK_HIBERNATE: "Tablet.hooks",
    HOOK_SHUTDOWN: "Tablet.hooks",
    HOOK_RELOAD: "Tablet.setup_server",
    HOOK_MONITOR: "Tablet.hooks",
    HOOK_ROTATE: "Tablet.hooks",
    HOOK_STARTUP: "Tablet.hooks",
}


def _get_lid_state():
    status = read(TABLET_LID_FILE, ignore_errors=True)
    if status is not None:
        return "open" in status
    return False


def _get_display_info():
    displays = glob(TABLET_DISPLAY_GLOB)
    if len(displays) > 0:
        count = 0
        signature = 0
        for display in displays:
            status = read(display, ignore_errors=True)
            signature += hash(display) + hash(status)
            if status is not None and status == "enabled\n":
                count += 1
        if count == 1:
            count = 0
            displays = glob(TABLET_STATUS_GLOB)
            for display in displays:
                status = read(display, ignore_errors=True)
                if status is not None and status[0] == "c":
                    count += 1
        del displays
        return count, signature
    return 0, 0


class Tablet(object):
    def __init__(self):
        self.file = None
        self.state_count = 1
        self.state_args = None
        self.state_hash = None
        self.state = TABLET_STATE_LAPTOP
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def _clear(self):
        self.state_args = None

    def thread(self, server):
        if not self.scheduler.empty():
            self.scheduler.run(blocking=False)
        if self.file is None:
            return
        try:
            event = self.file.read(240)
            if isinstance(event, bytes):
                if len(event) >= 21:
                    previous = self.state
                    if event[20] == 1:
                        if _get_lid_state():
                            self.state = TABLET_STATE_TABLET
                        else:
                            self.state = TABLET_STATE_CLOSED
                    else:
                        self.state = TABLET_STATE_LAPTOP
                    if self.state_count <= 1:
                        server.debug(
                            'Changing lid state to "%d" from "%d".'
                            % (self.state, previous)
                        )
                        server.forward(Message(HOOK_TABLET, {"state": self.state}))
                        if (
                            self.state != TABLET_STATE_CLOSED
                            and previous != TABLET_STATE_CLOSED
                        ):
                            server.send(
                                None, Message(HOOK_TABLET, {"state": self.state})
                            )
                    else:
                        server.debug(
                            'Detected a state change, but did not update due to "%d" connected displays.'
                            % self.state_count
                        )
                del event
                del previous
        except (OSError, ValueError) as err:
            server.error(
                "Attempting to read the tablet file raised an exception!", err=err
            )

    def setup_server(self, server):
        if self.file is not None:
            try:
                self.file.close()
            except OSError as err:
                server.error(
                    "Attempting to close the tablet file raised an exception!", err=err
                )
            self.file = None
        try:
            self.file = open(TABLET_EVENT_FILE, "rb")
            flags = fcntl(self.file.fileno(), F_GETFL)
            fcntl(self.file.fileno(), F_SETFL, flags | O_NONBLOCK)
            del flags
        except OSError as err:
            self.file = None
            server.error(
                "Attempting to setup the tablet file raised an exception!", err=err
            )

    def hooks(self, server, message):
        if message.header() == HOOK_MONITOR or message.header() == HOOK_STARTUP:
            count, signature = _get_display_info()
            server.debug(
                "Updating the connected Display count (%d connected, %s Signature)."
                % (count, hex(signature))
            )
            # server.set_swap("displays", count)
            previous = self.state_count
            self.state_count = count
            if message.header() == HOOK_STARTUP:
                self.state_hash = signature
                return None
            update = False
            update_notify = False
            if message.get("args") is not None:
                state_args_gen = hash(message.get("args"))
                if self.state_args is None or self.state_args != state_args_gen:
                    self.state_args = state_args_gen
                    update_notify = True
                    update = True
                del state_args_gen
            if update or self.state_hash != signature or previous != count:
                self.state_hash = signature
                update = True
                update_notify = True
            del signature
            if update:
                if (
                    not _get_lid_state()
                    or self.state == TABLET_STATE_CLOSED
                    or count > 1
                ):
                    server.send(
                        None,
                        Message(
                            header=HOOK_TABLET,
                            payload={"state": TABLET_STATE_LAPTOP, "update": False},
                        ),
                    )
                if count > 1:
                    server.send(
                        None, Message(header=HOOK_ROTATE, payload={"state": "normal"})
                    )
                else:
                    server.send(
                        None, Message(header=HOOK_TABLET, payload={"state": self.state})
                    )
                server.forward(Message(HOOK_TABLET, {"count": count}))
                if update_notify:
                    server.send(
                        None,
                        Message(
                            header=HOOK_NOTIFICATION,
                            payload={
                                "title": "Display Status",
                                "body": "Display configuration updated.\n%d Displays connected."
                                % count,
                                "icon": "preferences-desktop-display",
                            },
                        ),
                    )
                self.scheduler.enter(5, 1, self._clear)
                message["update"] = True
                return message.set_multicast(True)
            del count
            del update
            del previous
            del update_notify
        elif message.header() == HOOK_SHUTDOWN or message.get("state") == "pre":
            server.debug("Closing out tablet device handles..")
            if self.file is not None:
                try:
                    self.file.close()
                except OSError as err:
                    server.error(
                        "Attempting to close the tablet file raised an exception!",
                        err=err,
                    )
                self.file = None
        elif message.get("state") == "post-driver":
            self.setup_server(server)
            self.state = TABLET_STATE_LAPTOP


# EOF
