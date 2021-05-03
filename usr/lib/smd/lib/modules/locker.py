#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Module: Locker (User, System)
#
# Manages the system lockscreen and power inhibitors.

from os import environ
from os.path import join
from sched import scheduler
from time import time, sleep
from lib.util import stop, run, write
from lib.structs.message import Message
from subprocess import Popen, DEVNULL, SubprocessError
from lib.constants import (
    HOOK_POWER,
    HOOK_HIBERNATE,
    HOOK_SHUTDOWN,
    HOOK_DAEMON,
    HOOK_LOCK,
    HOOK_TABLET,
    HOOK_STARTUP,
    HOOK_RELOAD,
    HOOK_BACKGROUND,
    HOOK_NOTIFICATION,
    DIRECTORY_LIBEXEC,
    LOCKER_LOCK_BLANK_DEFAULT,
    LOCKER_LOCK_DEFAULT,
    LOCKER_SCREEN_ON,
    LOCKER_SCREEN_OFF,
    LOCKER_EXEC_HIBERNATE,
    LOCKER_BLANK_DEFAULT,
    LOCKER_SLEEP_DEFAULT,
    LOCKER_QUERY,
    LOCKER_STATUS_FILE,
    LOCKER_NAMES,
    LOCKER_BLANK,
    LOCKER_LID,
    LOCKER_HIBERNATE,
    LOCKER_LOCK_SCREEN,
    TABLET_STATE_CLOSED,
    TABLET_STATE_LAPTOP,
    TABLET_STATE_TABLET,
)

HOOKS = {
    HOOK_POWER: "LockerClient.hook",
    HOOK_DAEMON: "LockerClient.thread",
    HOOK_LOCK: "LockerClient.hook",
    HOOK_HIBERNATE: "LockerClient.hook",
    HOOK_SHUTDOWN: "LockerClient.hook",
    HOOK_STARTUP: "LockerClient.hook",
    HOOK_RELOAD: "LockerClient.setup",
}
HOOKS_SERVER = {
    HOOK_POWER: "LockerServer.hook",
    HOOK_DAEMON: "LockerServer.thread",
    HOOK_LOCK: "LockerServer.hook",
    HOOK_TABLET: "LockerServer.hook",
    HOOK_HIBERNATE: "LockerServer.hook",
    HOOK_BACKGROUND: "LockerServer.hook",
    HOOK_RELOAD: "LockerServer.hook",
}


def time_to_str(now, value):
    if value is None:
        return "Until Reboot"
    left = round(value - now)
    if left <= 0:
        return "Until Reboot"
    if left <= 60:
        return "%ds" % left
    if left > 60:
        mins = left // 60
        seconds = left - (mins * 60)
        del left
        return "%dm %ds" % (mins, seconds)
    return None


def _set_blank(seconds=None):
    if seconds is None:
        seconds = 0
    run(["/usr/bin/xset", "s", str(seconds)])
    run(["/usr/bin/xset", "dpms", str(seconds), str(seconds), str(seconds)])


def _set_notifications(hide=True):
    run(["/usr/bin/killall", "-SIGUSR1" if hide else "-SIGUSR2", "dunst"])


class LockerClient(object):
    def __init__(self):
        self.lock_blank = 5
        self.lockers = list()
        self.timeout_sleep = 60
        self.timeout_blank = 60
        self.sleep_event = None
        self.lock_process = None
        self.lock_command = None
        self.sleep_started = False
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def setup(self, server):
        try:
            self.timeout_blank = int(
                server.config("timeout_blank", LOCKER_BLANK_DEFAULT)
            )
        except ValueError:
            self.timeout_blank = server.set("timeout_blank", LOCKER_BLANK_DEFAULT)
        try:
            self.timeout_sleep = int(
                server.config("timeout_sleep", LOCKER_SLEEP_DEFAULT)
            )
        except ValueError:
            self.timeout_sleep = server.set("timeout_sleep", LOCKER_SLEEP_DEFAULT)

        try:
            self.lock_blank = int(
                server.config("lockscreen_blank", LOCKER_LOCK_BLANK_DEFAULT)
            )
        except ValueError:
            self.lock_blank = server.set("lockscreen_blank", LOCKER_LOCK_BLANK_DEFAULT)
        self.lock_command = server.config("locker", LOCKER_LOCK_DEFAULT)
        if not isinstance(self.lock_command, list):
            if isinstance(self.lock_command, str):
                self.lock_command = self.lock_command.split(" ")
            else:
                self.lock_command = server.set("locker", LOCKER_LOCK_DEFAULT)
        if not self._lock_running():
            _set_blank(self.timeout_blank)
            _set_notifications(False)
        else:
            _set_blank(self.lock_blank)
            _set_notifications(True)

    def _lock_running(self):
        return self.lock_process is not None and self.lock_process.poll() is None

    def thread(self, server):
        if not self._lock_running() and self.lock_process is not None:
            server.debug("Lock Screen was removed, resetting lock status.")
            self._unlock(server)
        elif self._lock_running():
            if LOCKER_HIBERNATE in self.lockers and self.sleep_event is not None:
                try:
                    self.scheduler.cancel(self.sleep_event)
                except ValueError:
                    pass
                self.sleep_event = None
                server.debug("Canceled any Hibernate timeouts due to Lockers.")
            elif LOCKER_HIBERNATE not in self.lockers and self.sleep_event is None:
                self.sleep_event = self.scheduler.enter(
                    self.timeout_sleep, 1, self._sleep, argument=(server,)
                )
                server.debug(
                    'Set Hibernate timeout for "%d" seconds due to Lockers.'
                    % self.timeout_sleep
                )
        if not self.scheduler.empty():
            self.scheduler.run(blocking=False)

    def _sleep(self, server):
        if self.sleep_event is not None:
            try:
                self.scheduler.cancel(self.sleep_event)
            except ValueError:
                pass
            self.sleep_event = None
        if self.sleep_started:
            self._lock(server, True)
        else:
            if LOCKER_HIBERNATE in self.lockers:
                server.warning(
                    "Invalid attempt to Hibernate the system while a locker is in place!"
                )
            elif not self.sleep_started:
                self.sleep_started = True
                self._lock(server, True)
                server.info("Triggering System Hibernation..")
                server.send(
                    None, Message(header=HOOK_LOCK, payload={LOCKER_HIBERNATE: True})
                )

    def _unlock(self, server):
        if self._lock_running():
            stop(self.lock_process)
            del self.lock_process
        self.lock_process = None
        self.sleep_started = False
        _set_notifications(False)
        if LOCKER_BLANK in self.lockers:
            _set_blank(None)
        else:
            _set_blank(self.timeout_blank)
        if self.sleep_event is not None:
            try:
                self.scheduler.cancel(self.sleep_event)
            except ValueError:
                pass
            self.sleep_event = None
        server.debug("Unlocked the Lock Screen and cancled any Hibernate timeouts.")
        server.send(None, Message(header=HOOK_LOCK, payload={"state": "post"}))

    def _lock(self, server, force):
        if LOCKER_LOCK_SCREEN in self.lockers and not force:
            return
        if self._lock_running():
            return
        else:
            try:
                self.lock_process = Popen(
                    " ".join(self.lock_command),
                    shell=True,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    env=environ,
                )
                server.info('Started Lock Screen, PID "%d".' % self.lock_process.pid)
            except (OSError, SubprocessError) as err:
                server.error("Starting the Lock Screen raised an exception!", err=err)
                self._unlock(server)
                return
        run(LOCKER_SCREEN_OFF)
        _set_notifications(True)
        _set_blank(self.lock_blank)
        server.send(None, Message(header=HOOK_LOCK, payload={"state": "pre"}))
        if not self.sleep_started:
            if LOCKER_HIBERNATE not in self.lockers:
                if self.sleep_event is None:
                    self.sleep_event = self.scheduler.enter(
                        self.timeout_sleep, 1, self._sleep, argument=(server,)
                    )
                    server.debug(
                        'Set Hibernate timeout for "%d" seconds.' % self.timeout_sleep
                    )
            elif self.sleep_event is not None:
                try:
                    self.scheduler.cancel(self.sleep_event)
                except ValueError:
                    pass
                self.sleep_event = None
                server.debug("Canceled Hibernate timeout.")
        elif self.sleep_event is not None:
            try:
                self.scheduler.cancel(self.sleep_event)
            except ValueError:
                pass
            self.sleep_event = None
            server.debug(
                "Canceled Hibernate timeout, as we are attempting to Hibernate."
            )

    def hook(self, server, message):
        if message.header() == HOOK_LOCK and message.get("state") is None:
            if LOCKER_LOCK_SCREEN not in self.lockers or message.get("force", False):
                self._lock(server, message.get("force", False))
        elif message.header() == HOOK_POWER and "lockers" in message:
            self.lockers = message["lockers"]
            if LOCKER_BLANK in self.lockers:
                _set_blank(None)
            else:
                _set_blank(self.timeout_blank)
            server.debug("Updating Lockers from server.")
        elif message.header() == HOOK_HIBERNATE:
            if message.get("state") == "pre":
                if not self.sleep_started:
                    run(
                        join(DIRECTORY_LIBEXEC, "smd-reset-display"), ignore_errors=True
                    )
                self.sleep_started = True
                self._sleep(server)
            elif message.get("state") == "post":
                self.sleep_started = False
                if self.sleep_event is not None:
                    try:
                        self.scheduler.cancel(self.sleep_event)
                    except ValueError:
                        pass
                    self.sleep_event = None
                self._lock(server, True)
                run(LOCKER_SCREEN_ON)
        elif message.header() == HOOK_STARTUP:
            return Message(header=HOOK_POWER, payload=LOCKER_QUERY)


class LockerServer(object):
    def __init__(self):
        self.sleep = False
        self.closed = False
        self.update = False
        self.lockers = dict()
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)
        write(LOCKER_STATUS_FILE, "", ignore_errors=True)

    def thread(self, server):
        if not self.scheduler.empty():
            self.scheduler.run(blocking=False)
        if self.update:
            server.debug("Updating Clients on Locker status..")
            server.send(
                None,
                Message(
                    header=HOOK_POWER, payload={"lockers": list(self.lockers.keys())}
                ),
            )
            self.update = False
            write(
                LOCKER_STATUS_FILE,
                str("\n".join(self.lockers.keys())),
                ignore_errors=True,
            )
            if LOCKER_LID not in self.lockers and self.closed:
                server.forward(Message(HOOK_TABLET, {"state": TABLET_STATE_CLOSED}))
            if len(self.lockers) == 0:
                message = "No lockers are enabled."
            else:
                now = time()
                message = "\n".join(
                    [
                        "%s (%s)"
                        % (LOCKER_NAMES.get(n, n.title()), time_to_str(now, l[1]))
                        for n, l in self.lockers.items()
                    ]
                )
                del now
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Lockers Updated",
                        "body": message,
                        "icon": "caffeine",
                    },
                ),
            )
            del message

    def _update(self, locker):
        if locker in self.lockers:
            del self.lockers[locker]
            self.update = True

    def hook(self, server, message):
        if message.header() == HOOK_LOCK:
            if LOCKER_HIBERNATE in message:
                server.info("Attempting to Hibernate the system.. (Reason: Locker)")
                try:
                    run(LOCKER_EXEC_HIBERNATE, wait=True, ignore_errors=False)
                except OSError as err:
                    server.error(
                        "Attempting to Hibernate the system raised an exception!",
                        err=err,
                    )
            elif (
                LOCKER_LOCK_SCREEN not in self.lockers
                or message.get("force")
                or message.get("state")
            ):
                return message.set_multicast(True)
        elif (
            message.header() == HOOK_TABLET
            and message.get("state", TABLET_STATE_TABLET) <= TABLET_STATE_LAPTOP
            and not message.get("count")
        ):
            self.closed = (
                message.get("state", TABLET_STATE_LAPTOP) == TABLET_STATE_CLOSED
            )
            if "lid" not in self.lockers and self.closed:
                server.info("Attempting to Hibernate the system.. (Reason: Lid)")
                try:
                    run(LOCKER_EXEC_HIBERNATE, wait=True, ignore_errors=False)
                except OSError as err:
                    server.error(
                        "Attempting to Hibernate the system raised an exception!",
                        err=err,
                    )
            elif self.closed:
                return Message(HOOK_LOCK, {"force": True})
        elif (
            message.header() == HOOK_HIBERNATE
            or message.header() == HOOK_BACKGROUND
            or message.header() == HOOK_RELOAD
            or (message.header() == HOOK_POWER and message.get("type") == "power")
        ):
            if message.header() == HOOK_HIBERNATE:
                self.sleep = not ("post" in message.get("state"))
            if (
                message.header() == HOOK_POWER
                and message.get("type") != "power"
                and not self.sleep
            ):
                return None
            return message.set_multicast(True)
        elif message.header() == HOOK_POWER and message.get("type") == "locker":
            if message.get("action") == "query":
                if "locker" in message:
                    return {"enabled": message["locker"] in self.lockers}
                return {
                    "lockers": {name: value[1] for name, value in self.lockers.items()}
                }
            if message.get("action") == "get":
                return {"lockers": list(self.lockers.keys())}
            if message.get("action") == "set":
                if isinstance(message.get("list"), list):
                    for locker in message["list"]:
                        if isinstance(locker, dict) and "name" in locker:
                            self._add(
                                server,
                                locker["name"],
                                locker.get("expire", None),
                                locker.get("force", False),
                            )
                elif "name" in message:
                    self._add(
                        server,
                        message["name"],
                        message.get("expire", None),
                        message.get("force", False),
                    )

    def _remove(self, server, locker):
        if locker in self.lockers:
            if self.lockers[locker][0] is not None:
                try:
                    self.scheduler.cancel(self.lockers[locker][0])
                except ValueError:
                    pass
            del self.lockers[locker]
            server.debug('Removed Locker "%s"!' % locker)
            self.update = True

    def _add(self, server, locker, timeout, force):
        if locker in self.lockers and not force:
            return False
        self._remove(server, locker)
        if timeout is not None:
            try:
                seconds = int(timeout)
            except ValueError:
                server.warning(
                    'Client attempted to add a Locker "%s" with an invalid expire time of "%s"!'
                    % (locker, timeout)
                )
                return False
            if seconds == 0:
                del seconds
                return True
            elif seconds < 0:
                self.lockers[locker] = (None, None)
                server.debug('Added a Locker "%s" with no expire timeout!' % locker)
            else:
                self.lockers[locker] = (
                    self.scheduler.enter(seconds, 1, self._update, argument=(locker,)),
                    round(time() + seconds),
                )
                server.debug(
                    'Added a Locker "%s" with a timeout of "%d" seconds!'
                    % (locker, seconds)
                )
            del seconds
        else:
            self.lockers[locker] = (None, None)
            server.debug('Added a Locker "%s" with no expire timeout!' % locker)
        self.update = True
        return True
