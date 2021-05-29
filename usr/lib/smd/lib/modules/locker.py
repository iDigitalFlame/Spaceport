#!/usr/bin/false
# Module: Locker (User, System)
#
# Manages the system lockscreen and power inhibitors.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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

from glob import glob
from os import environ
from sched import scheduler
from time import time, sleep
from lib.structs.message import Message
from subprocess import Popen, DEVNULL, SubprocessError
from lib.util import stop, run, write, read, eval_env, boolean
from lib.constants import (
    EMPTY,
    HOOK_OK,
    HOOK_LOCK,
    HOOK_LOCKER,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_MONITOR,
    HOOK_DISPLAY,
    HOOK_STARTUP,
    HOOK_SUSPEND,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    LOCKER_TYPE_LID,
    LOCKER_PATH_LID,
    LOCKER_TYPE_KEY,
    LOCKER_TYPE_LOCK,
    MESSAGE_TYPE_PRE,
    LOCKER_EXEC_LOCK,
    LOCKER_CHECK_TIME,
    LOCKER_TYPE_BLANK,
    LOCKER_BLANK_TIME,
    LOCKER_EXEC_RESET,
    LOCKER_TYPE_NAMES,
    MESSAGE_TYPE_POST,
    LOCKER_TRIGGER_KEY,
    SCREEN_PATH_ACTIVE,
    DEFAULT_LOCKER_LID,
    LOCKER_PATH_STATUS,
    LOCKER_TRIGGER_LID,
    LOCKER_BACKOFF_TIME,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_CONFIG,
    LOCKER_TYPE_SUSPEND,
    DEFAULT_LOCKER_LOCK,
    LOCKER_TRIGGER_LOCK,
    LOCKER_EXEC_SUSPEND,
    MESSAGE_TYPE_STATUS,
    DEFAULT_LOCKER_BLANK,
    SCREEN_PATH_CONNECTED,
    DEFAULT_LOCKER_LOCKER,
    LOCKER_EXEC_HIBERNATE,
    LOCKER_PATH_WAKEALARM,
    LOCKER_TYPE_HIBERNATE,
    LOCKER_EXEC_SCREEN_ON,
    LOCKER_EXEC_SCREEN_OFF,
    LOCKER_TRIGGER_TIMEOUT,
    DEFAULT_LOCKER_SUSPEND,
    DEFAULT_LOCKER_KEY_LOCK,
    DEFAULT_LOCKER_HIBERNATE,
)

HOOKS = {
    HOOK_LOCK: "LockerClient.lock",
    HOOK_DAEMON: "LockerClient.thread",
    HOOK_LOCKER: "LockerClient.update",
    HOOK_RELOAD: "LockerClient.startup",
    HOOK_SUSPEND: "LockerClient.suspend",
    HOOK_STARTUP: "LockerClient.startup",
    HOOK_SHUTDOWN: "LockerClient.shutdown",
    HOOK_HIBERNATE: "LockerClient.hibernate",
}
HOOKS_SERVER = {
    HOOK_LOCK: "LockerServer.lock",
    HOOK_DAEMON: "LockerServer.thread",
    HOOK_LOCKER: "LockerServer.update",
    HOOK_MONITOR: "LockerServer.screen",
    HOOK_RELOAD: "LockerServer.startup",
    HOOK_STARTUP: "LockerServer.startup",
    HOOK_SUSPEND: "LockerServer.suspend",
    HOOK_HIBERNATE: "LockerServer.hibernate",
}


def _pause_notify(hide):
    run(
        ["/usr/bin/killall", "-SIGUSR1" if hide else "-SIGUSR2", "dunst"],
        ignore_errors=True,
    )


def _get_screens(server):
    active = 0
    connected = 0
    for screen in glob(SCREEN_PATH_ACTIVE):
        try:
            s = read(screen, ignore_errors=False)
        except OSError as err:
            server.error(
                f'Attempting to read the screen path "{screen}" resulted in an Exception!',
                err=err,
            )
            continue
        if len(s) > 0 and s.lower()[0] == "e":
            active += 1
        del s
    for screen in glob(SCREEN_PATH_CONNECTED):
        try:
            s = read(screen, ignore_errors=False)
        except OSError as err:
            server.error(
                f'Attempting to read the screen path "{screen}" resulted in an Exception!',
                err=err,
            )
            continue
        if len(s) > 0 and s.lower()[0] == "c":
            connected += 1
        del s
    server.debug(f"Detected {active} active and {connected} connected screens..")
    return active, connected


def time_to_str(now, value):
    if value is None:
        return "Until Reboot"
    left = round(value - now)
    if left <= 0:
        return "Until Reboot"
    if left <= 60:
        return f"{left}s"
    if left > 60:
        mins = left // 60
        seconds = left - (mins * 60)
        del left
        return f"{mins}m {seconds}s"
    return None


class _LockerLock(object):
    def __init__(self, name, seconds, server):
        self.name = name
        self.event = None
        self.expires = None
        self.server = server
        if seconds is not None:
            self.expires = round(time() + seconds)
            self.event = server.scheduler.enter(seconds, 1, self.cancel)

    def cancel(self):
        if self.event is not None:
            try:
                self.server.scheduler.cancel(self.event)
            except ValueError:
                pass
        del self.server.lockers[self.name]
        self.server.needs_update = True
        self.event = None


class LockerClient(object):
    def __init__(self):
        self.event = None
        self.lockers = list()
        self.lock_locker = None
        self.is_sleeping = False
        self.lock_process = None
        self.lock_command = None
        self.lock_on_key = False
        self.ability_lid = DEFAULT_LOCKER_LID
        self.ability_lock = DEFAULT_LOCKER_LOCK
        self.ability_blank = DEFAULT_LOCKER_BLANK
        self.ability_suspend = DEFAULT_LOCKER_SUSPEND
        self.ability_hibernate = DEFAULT_LOCKER_HIBERNATE
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def _is_locked(self):
        return self.lock_process is not None and self.lock_process.poll() is None

    def setup(self, server):
        server.debug("Loading locker defaults from config..")
        try:
            self.ability_blank = int(
                server.get_config("locker.screen_blank", DEFAULT_LOCKER_BLANK, True)
            )
        except (TypeError, ValueError) as err:
            server.error(
                'Improper value for "locker.screen_blank"! Resetting to default!',
                err=err,
            )
            self.ability_blank = server.set_config(
                "locker.screen_blank", DEFAULT_LOCKER_BLANK, True
            )
        self.lock_on_key = boolean(
            server.get_config("locker.key_lock", DEFAULT_LOCKER_KEY_LOCK, True)
        )
        self.ability_lid = boolean(
            server.get_config("locker.lid_close", DEFAULT_LOCKER_LID, True)
        )
        try:
            self.ability_lock = int(
                server.get_config("locker.lockscreen", DEFAULT_LOCKER_LOCK, True)
            )
        except (TypeError, ValueError) as err:
            server.error(
                'Improper value for "locker.lockscreen"! Resetting to default!', err=err
            )
            self.ability_lock = server.set_config(
                "locker.lockscreen", DEFAULT_LOCKER_LOCK, True
            )
        try:
            self.ability_suspend = int(
                server.get_config("locker.suspend", DEFAULT_LOCKER_SUSPEND, True)
            )
        except (TypeError, ValueError) as err:
            server.error(
                'Improper value for "locker.suspend"! Resetting to default!', err=err
            )
            self.ability_suspend = server.set_config(
                "locker.suspend", DEFAULT_LOCKER_SUSPEND, True
            )
        try:
            self.ability_hibernate = int(
                server.get_config("locker.hibernate", DEFAULT_LOCKER_HIBERNATE, True)
            )
        except (TypeError, ValueError) as err:
            server.error(
                'Improper value for "locker.hibernate"! Resetting to default!', err=err
            )
            self.ability_hibernate = server.set_config(
                "locker.hibernate", DEFAULT_LOCKER_HIBERNATE, True
            )
        try:
            self.lock_command = server.get_config(
                "locker.command", DEFAULT_LOCKER_LOCKER, True
            )
        except (TypeError, ValueError) as err:
            server.error(
                'Improper value for "locker.command"! Resetting to default!', err=err
            )
            self.lock_command = server.set_config(
                "locker.command", DEFAULT_LOCKER_LOCKER, True
            )
        if isinstance(self.lock_command, list):
            self.lock_command = self.lock_command.copy()
        else:
            if isinstance(self.lock_command, str):
                self.lock_command = self.lock_command.split(" ")
            else:
                server.error(
                    'Improper value for "locker.command"! Resetting to default!'
                )
                self.lock_command = server.set_config(
                    "locker.command", DEFAULT_LOCKER_LOCKER, True
                )
        for x in range(0, len(self.lock_command)):
            self.lock_command[x] = eval_env(self.lock_command[x])
        self._try_set_screen()
        stop(self.lock_locker)
        _pause_notify(False)
        if self.ability_lock is not None and self.ability_lock > 0:
            try:
                self.lock_locker = Popen(
                    [
                        "/usr/bin/xautolock",
                        "-secure",
                        "-detectsleep",
                        "-time",
                        str(max(self.ability_lock // 60, 1)),
                        "-locker",
                        LOCKER_EXEC_LOCK,
                    ],
                    env=environ,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error('Starting "xautolock" raised an Exception!', err=err)
                self.locker = None

    def _cancel_event(self):
        if self.event is None:
            return
        try:
            self.scheduler.cancel(self.event)
        except ValueError:
            pass
        self.event = None

    def thread(self, server):
        if not self._is_locked() and self.lock_process is not None:
            server.debug("Lock Screen was removed, resetting lock status.")
            self._set_unlock(server)
        elif self._is_locked():
            self._try_wake_event(server)
        if not self.scheduler.empty():
            self.scheduler.run(blocking=False)
        if (
            self.ability_lock is not None
            and self.ability_lock > 0
            and self.lock_locker is not None
            and self.lock_locker.poll() is not None
        ):
            server.warning("Locker watcher process has unexpectedly closed!")
            stop(self.lock_locker)
            self.lock_locker = None

    def _try_set_screen(self):
        timeout = self.ability_blank
        if timeout is None or timeout < 0:
            timeout = 0
        if LOCKER_TYPE_BLANK in self.lockers:
            timeout = 0
        if self._is_locked():
            timeout = LOCKER_BLANK_TIME
        run(["/usr/bin/xset", "s", str(timeout)], ignore_errors=True)
        run(
            ["/usr/bin/xset", "dpms", str(timeout), str(timeout), str(timeout)],
            ignore_errors=True,
        )
        del timeout

    def shutdown(self, server):
        self.lockers.clear()
        stop(self.lock_locker)
        self.lock_locker = None
        self._set_unlock(server)

    def _try_wake(self, server):
        self._cancel_event()
        self._set_lock(server, True)
        server.send(
            None, Message(header=HOOK_LOCK, payload={"trigger": LOCKER_TRIGGER_TIMEOUT})
        )
        return server.info("Lockscreen timeout was hit, triggering timeout!")

    def _set_unlock(self, server):
        if self.lock_process is not None or self._is_locked():
            stop(self.lock_process)
            server.debug("Unlocked the Lock Screen and cancled any timeouts!")
            server.send(
                None, Message(header=HOOK_LOCK, payload={"type": MESSAGE_TYPE_POST})
            )
            run(LOCKER_EXEC_SCREEN_ON, ignore_errors=True)
        self.lock_process = None
        self._cancel_event()
        self._try_set_screen()
        _pause_notify(False)

    def lock(self, server, message):
        if message.type is not None:
            return
        if message.trigger == LOCKER_TRIGGER_KEY and not self.lock_on_key:
            return server.debug('Ignoring key removal lock as "key_lock" was false.')
        self._set_lock(
            server, message.get("force", False) or message.trigger == LOCKER_TRIGGER_KEY
        )

    def _try_wake_event(self, server):
        if self.is_sleeping:
            self._cancel_event()
            return
        if self.ability_lock is None or self.ability_lock <= 0:
            return
        if self.ability_suspend is not None and self.ability_suspend > 0:
            if LOCKER_TYPE_SUSPEND in self.lockers:
                if self.event is None:
                    return
                self._cancel_event()
                return server.debug(
                    "Suspend locker was detected, canceling suspend timeout.."
                )
        elif self.ability_hibernate is not None and self.ability_hibernate > 0:
            if LOCKER_TYPE_HIBERNATE in self.lockers:
                if self.event is None:
                    return
                self._cancel_event()
                return server.debug(
                    "Hibernate locker was detected, canceling hibernate timeout.."
                )
        if self.event is not None:
            return
        timeout = self.ability_suspend
        if timeout is None or timeout <= 0:
            timeout = self.ability_hibernate
        server.debug(f'Setting lockscreen timeout event for "{timeout}" seconds.')
        self._cancel_event()
        self.event = self.scheduler.enter(
            timeout, 1, self._try_wake, argument=(server,)
        )
        server.debug(f'Set lock screen timeout for "{timeout}" seconds..')
        del timeout

    def update(self, server, message):
        if message.type != MESSAGE_TYPE_STATUS or message.lockers is None:
            return
        if isinstance(message.lockers, dict):
            self.lockers = list(message.lockers.keys())
        else:
            self.lockers = message.lockers
        self._try_set_screen()
        return server.debug("Received updated list of lockers from server!")

    def suspend(self, server, message):
        if message.type == MESSAGE_TYPE_PRE:
            server.info("Received a suspend request from the server!")
            self.is_sleeping = True
            self._set_lock(server, True)
            run([LOCKER_EXEC_RESET, "no-alert"], ignore_errors=True)
            return HOOK_OK
        self.is_sleeping = False
        run(LOCKER_EXEC_SCREEN_ON, ignore_errors=True)

    def startup(self, server, message):
        if message.header() == HOOK_RELOAD:
            self.setup(server)
        server.debug("Sending abilities and query for current lockers.")
        server.send(
            None,
            Message(
                header=HOOK_LOCKER,
                payload={
                    "type": MESSAGE_TYPE_CONFIG,
                    LOCKER_TYPE_LID: self.ability_lid,
                    LOCKER_TYPE_LOCK: self.ability_lock,
                    LOCKER_TYPE_SUSPEND: self.ability_suspend,
                    LOCKER_TYPE_HIBERNATE: self.ability_hibernate,
                },
            ),
        )
        return Message(header=HOOK_LOCKER, payload={"type": MESSAGE_TYPE_STATUS})

    def hibernate(self, server, message):
        if message.type == MESSAGE_TYPE_PRE:
            server.info("Received a hibernate request from the server!")
            self.is_sleeping = True
            self._set_lock(server, True)
            run([LOCKER_EXEC_RESET, "no-alert"], ignore_errors=True)
            return HOOK_OK
        self.is_sleeping = False
        run(LOCKER_EXEC_SCREEN_ON, ignore_errors=True)

    def _set_lock(self, server, force=False):
        if (self.ability_lock is None or self.ability_lock <= 0) and not force:
            return server.debug(
                "Client lacks the ability to lock, not setting non-force lockscreen!"
            )
        if LOCKER_TYPE_LOCK in self.lockers and not force:
            return server.debug(
                "Lockscreen Locker is present, not setting non-force lockscreen!"
            )
        if self._is_locked():
            return
        try:
            self.lock_process = Popen(
                " ".join(self.lock_command),
                shell=True,
                env=environ,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
            server.info(f'Started Lock Screen, PID "{self.lock_process.pid}".')
        except (OSError, SubprocessError) as err:
            self._set_unlock(server)
            return server.error(
                "Starting the Lock Screen raised an exception!", err=err
            )
        _pause_notify(True)
        self._try_set_screen()
        self._try_wake_event(server)
        run(LOCKER_EXEC_SCREEN_OFF, ignore_errors=True)
        server.send(None, Message(header=HOOK_LOCK, payload={"type": MESSAGE_TYPE_PRE}))


class LockerServer(object):
    def __init__(self):
        self.lockers = dict()
        self.lid_switch = None
        self.event_check = None
        self.display_active = 1
        self.event_backoff = None
        self.is_wakealarm = False
        self.needs_update = False
        self.display_connected = 1
        self.is_suspending = False
        self.is_hibernating = False
        self.ability_lid = DEFAULT_LOCKER_LID
        self.ability_lock = DEFAULT_LOCKER_LOCK
        self.ability_suspend = DEFAULT_LOCKER_SUSPEND
        self.ability_hibernate = DEFAULT_LOCKER_HIBERNATE
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def thread(self, server):
        if not self.scheduler.empty():
            self.scheduler.run(blocking=False)
        if self.needs_update:
            self._send_notify(server)
            self.needs_update = False
        self._check_lid(server)

    def screen(self, server):
        if self.event_check is not None:
            return server.debug("Not ready to check display status again...")
        self.event_check = self.scheduler.enter(
            LOCKER_CHECK_TIME, 1, self._screen_clear_check
        )
        self._screen_detect(server, False)

    def _check_lid(self, server):
        if self.lid_switch is None or self.display_active > 1:
            return
        if LOCKER_TYPE_LID in self.lockers or not self.ability_lid:
            return
        try:
            lid = self.lid_switch.read()
        except OSError as err:
            return server.error(
                f'Attempting to read the lid switch "{LOCKER_PATH_LID}" raised an Exception!',
                err=err,
            )
        try:
            self.lid_switch.seek(0)
        except OSError as err:
            return server.error(
                f'Attempting to seek the lid switch "{LOCKER_PATH_LID}" raised an Exception!',
                err=err,
            )
        if not isinstance(lid, bytes):
            return server.error("Lid switch read did not return a proper bytearray!")
        if len(lid) >= 13 and lid[12] == 111:
            del lid
            return
        del lid
        if self.event_backoff is not None:
            return server.debug(
                "Detected a lid closure, but screen backoff is in effect!"
            )
        server.debug("Detected a lid closure!")
        return self._try_suspend(server, True)

    def _screen_clear_check(self):
        try:
            self.scheduler.cancel(self.event_check)
        except ValueError:
            pass
        self.event_check = None

    def setup_server(self, server):
        write(LOCKER_PATH_STATUS, EMPTY, ignore_errors=True, perms=0o644)
        if self.lid_switch is not None:
            try:
                self.lid_switch.close()
            except OSError:
                pass
            self.lid_switch = None
        try:
            self.lid_switch = open(LOCKER_PATH_LID, "rb")
        except OSError as err:
            server.error(
                "Attempting to get a handle to the lid switch raised an Exception!",
                err=err,
            )

    def _send_notify(self, server):
        server.debug("Updating Clients on Locker status..")
        server.send(
            None,
            Message(
                header=HOOK_LOCKER,
                payload={
                    "type": MESSAGE_TYPE_STATUS,
                    "lockers": list(self.lockers.keys()),
                },
            ),
        )
        write(
            LOCKER_PATH_STATUS,
            str("\n".join(self.lockers.keys())),
            ignore_errors=True,
            perms=0o644,
        )
        message = "No lockers are enabled."
        if len(self.lockers) > 0:
            now = time()
            message = "\n".join(
                [
                    f"{LOCKER_TYPE_NAMES.get(n, n.title())} ({time_to_str(now, l.expires)})"
                    for n, l in self.lockers.items()
                ]
            )
            del now
        server.notify("Lockers Updated", message, "caffeine")
        del message

    def lock(self, server, message):
        if message.trigger is None and message.type == MESSAGE_TYPE_POST:
            if message.multicast():
                return
            return message.set_multicast()
        if message.type is not None:
            return
        if message.trigger == LOCKER_TRIGGER_LID:
            if self.event_backoff is not None:
                return server.debug("Lock attempted, but screen backoff is in effect!")
            if self.display_active > 1:
                return server.debug(
                    "Not triggering a lid close action due to connected displays.."
                )
            if LOCKER_TYPE_LID in self.lockers or not self.ability_lid:
                return server.debug("Ignoring lid close action due to lid locker!")
            return self._try_suspend(server, True)
        if message.trigger == LOCKER_TRIGGER_TIMEOUT and message.is_from_client():
            server.debug("Received a timeout message from the locker client!")
            return self._try_suspend(server)
        if (
            message.trigger != LOCKER_TRIGGER_LOCK
            and message.trigger != LOCKER_TRIGGER_KEY
        ):
            return server.warning("Received an invalid locker trigger!")
        if (self.ability_lock is None or self.ability_lock <= 0) and not message.force:
            return server.debug(
                "Ignoring non-force lock request due to client lacking lock ability."
            )
        if message.trigger == LOCKER_TRIGGER_KEY:
            if LOCKER_TYPE_KEY in self.lockers:
                return server.debug("Ignoring key lock request due to key inhibitor.")
        else:
            if LOCKER_TYPE_LOCK in self.lockers and not message.force:
                return server.debug(
                    "Ignoring non-force lock request due to lock inhibitor."
                )
        server.debug("Forwarding screen lock command..")
        return message.set_multicast()

    def _screen_clear_backoff(self):
        try:
            self.scheduler.cancel(self.event_backoff)
        except ValueError:
            pass
        self.event_backoff = None

    def update(self, server, message):
        if message.type == MESSAGE_TYPE_CONFIG:
            if LOCKER_TYPE_LID in message:
                self.ability_lid = message.lid
            if LOCKER_TYPE_LOCK in message:
                self.ability_lock = message.lock
            if LOCKER_TYPE_SUSPEND in message:
                self.ability_suspend = message.suspend
            if LOCKER_TYPE_HIBERNATE in message:
                self.ability_hibernate = message.hibernate
            return server.debug(
                f"Client capabilities were updated. ({self.ability_lid}, {self.ability_lock}, "
                f"{self.ability_suspend}, {self.ability_hibernate})"
            )
        if message.type == MESSAGE_TYPE_ACTION:
            if message.name is not None:
                return self._set_locker(
                    server,
                    message.name,
                    message.get("time", None),
                    message.get("force", False),
                )
            if isinstance(message.list, list):
                for locker in message.list:
                    if "name" not in locker:
                        continue
                    self._set_locker(
                        server,
                        locker["name"],
                        locker.get("time", None),
                        locker.get("force", False),
                    )
                return
            return server.debug("Invalid management query by client!")
        if message.type == MESSAGE_TYPE_STATUS:
            if message.locker is not None and message.locker in self.lockers:
                return {
                    "type": MESSAGE_TYPE_STATUS,
                    "enabled": message.locker in self.lockers,
                    "time": self.lockers[message.lower].expires,
                }
            return {
                "type": MESSAGE_TYPE_STATUS,
                "lockers": {
                    name: value.expires for name, value in self.lockers.items()
                },
            }

    def _set_wake_alarm(self, server):
        if self.ability_hibernate is None or self.ability_hibernate <= 0:
            return server.debug(
                "Client lacks the ability to hibernate, not setting wake alarm.."
            )
        if LOCKER_TYPE_HIBERNATE in self.lockers:
            blocker = self.lockers[LOCKER_TYPE_HIBERNATE]
            if blocker.expires is None or blocker.expires > (
                time() + self.ability_hibernate
            ):
                return server.debug(
                    "Locker blocks the ability to hibernate, not setting RTC wake alarm!"
                )
            del blocker
            server.debug(
                "Hibernate locker will expire while we are sleeping, removing it.."
            )
            self._remove_locker(server, LOCKER_TYPE_HIBERNATE)
        server.debug(
            f'Setting the RTC alarm to wake the system to hibernate in "{self.ability_hibernate}" seconds.'
        )
        try:
            write(
                LOCKER_PATH_WAKEALARM,
                str(round(time() + self.ability_hibernate)),
                ignore_errors=False,
            )
        except OSError as err:
            return server.error(
                "Attempting to set the RTC alarm raised an Exception!", err=err
            )
        self.is_wakealarm = True
        server.info(f'Hibernate wake alarm set for "{self.ability_hibernate}" seconds.')

    def startup(self, server, message):
        if message.header() == HOOK_RELOAD and not message.all:
            return
        self._screen_detect(server, True)
        if message.header() != HOOK_RELOAD:
            return
        self.setup_server(server)

    def suspend(self, server, message):
        if message.type == MESSAGE_TYPE_PRE:
            self.is_wakealarm = False
            self.is_hibernating = False
            if self.is_suspending:
                return
            server.info("Received a pre-suspend hook, preparing to suspend!")
            self.is_suspending = True
            self._set_wake_alarm(server)
        elif message.type == MESSAGE_TYPE_POST:
            if not self.is_suspending:
                return
            server.debug("Received a post-suspend hook, releasing hibernation locks!")
            self.is_suspending = False
            self.is_hibernating = False
            if self._check_wake_alarm(server):
                server.info("Wake alarm was triggered, triggering hibernation!")
                return run(LOCKER_EXEC_HIBERNATE)
        return message.set_multicast()

    def _check_wake_alarm(self, server):
        if not self.is_wakealarm:
            return False
        self.is_wakealarm = False
        if self.ability_hibernate is None or self.ability_hibernate <= 0:
            return False
        if LOCKER_TYPE_HIBERNATE in self.lockers:
            return False
        server.debug("Checking the RTC wake alarm..")
        try:
            alarm = read(LOCKER_PATH_WAKEALARM, ignore_errors=False)
        except OSError as err:
            server.error(
                "Attempting to read the RTC wake alarm file raised an Exception!",
                err=err,
            )
            return False
        if len(alarm) > 0:
            try:
                write(LOCKER_PATH_WAKEALARM, EMPTY, ignore_errors=False)
            except OSError as err:
                server.error(
                    "Attempting to reset the RTC wake alarm file raised an Exception!",
                    err=err,
                )
            return False
        return True

    def hibernate(self, server, message):
        if message.type == MESSAGE_TYPE_PRE:
            self.is_wakealarm = False
            self.is_suspending = False
            if self.is_hibernating:
                return
            server.info("Received a pre-hibernation hook, preparing to hibernate!")
            self.is_hibernating = True
        elif message.type == MESSAGE_TYPE_POST:
            self.is_wakealarm = False
            if not self.is_hibernating:
                return
            server.debug(
                "Received a post-hibernation hook, releasing hibernation locks!"
            )
            self.is_suspending = False
            self.is_hibernating = False
        return message.set_multicast()

    def _remove_locker(self, server, locker):
        lock = self.lockers.get(locker)
        if lock is not None:
            lock.cancel()
            server.debug(f'Removed Locker "{locker}"!')
        del lock

    def _try_suspend(self, server, lid=False):
        if self.event_backoff is not None:
            return server.debug("Suspend attempted, but screen backoff is in effect!")
        if self.ability_suspend is None or self.ability_suspend <= 0:
            if self.ability_hibernate is None or self.ability_hibernate <= 0:
                return server.debug(
                    "Client lacks the ability to suspend and hibernate, bailing out.."
                )
            if LOCKER_TYPE_HIBERNATE in self.lockers:
                return server.debug("Locker is inhibiting hibernate, bailing out..")
            server.debug(
                "Client lacks the ability to suspend, attempting to hibernate!"
            )
            return run(LOCKER_EXEC_HIBERNATE)
        if LOCKER_TYPE_SUSPEND in self.lockers and not lid:
            return server.debug("Locker is inhibiting suspend, bailing out..")
        return run(LOCKER_EXEC_SUSPEND)

    def _screen_detect(self, server, initial=False):
        active, connected = _get_screens(server)
        if (
            not initial
            and self.display_active == active
            and self.display_connected == connected
        ):
            return
        self.display_active = active
        self.display_connected = connected
        del active
        del connected
        self.event_backoff = self.scheduler.enter(
            LOCKER_BACKOFF_TIME, 1, self._screen_clear_backoff
        )
        message = Message(
            header=HOOK_DISPLAY,
            payload={
                "active": self.display_active,
                "connected": self.display_connected,
            },
        )
        if initial:
            server.forward(message)
        else:
            server.send(None, message)
        del message

    def _set_locker(self, server, locker, expires, force=False):
        if locker in self.lockers and not force:
            return
        seconds = None
        if expires is not None:
            try:
                seconds = int(expires)
            except ValueError:
                return server.warning(
                    f'Client attempted to add a Locker "{locker}" with an invalid expire time of "{expires}"!'
                )
            if seconds <= 0:
                return self._remove_locker(server, locker)
        if (
            locker in self.lockers
            and seconds is None
            and self.lockers[locker].expires is None
        ):
            return
        self._remove_locker(server, locker)
        if seconds is None:
            server.debug(f'Added a Locker "{locker}" with no expire timeout!')
        else:
            server.debug(
                f'Added a Locker "{locker}" with a timeout of "{seconds}" seconds!'
            )
        self.lockers[locker] = _LockerLock(locker, seconds, self)
        self.needs_update = True
