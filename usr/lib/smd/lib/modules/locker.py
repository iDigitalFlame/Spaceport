#!/usr/bin/false
################################
### iDigitalFlame  2016-2024 ###
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
# Copyright (C) 2016 - 2024 iDigitalFlame
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

# Module: System/LockerServer, User/LockerClient
#   Manages multiple types of inhibitors and controls power actions based on
#   user configuration. User and Server modules sync with eachother to enable
#   the Server to enforce rules.

from glob import glob
from time import time
from json import dumps
from os import O_NONBLOCK
from lib.sway import swaymsg
from lib.structs import Message, as_error
from signal import SIGCONT, SIGSTOP, SIGUSR1
from lib.util.file import read, write, expand
from lib.util.exec import stop, nulexec, split
from fcntl import ioctl, fcntl, F_GETFL, F_SETFL
from lib.util import boolean, num, nes, cancel_nul, seconds, time_to_str
from lib.constants import (
    EMPTY,
    HOOK_OK,
    NEWLINE,
    MSG_PRE,
    MSG_POST,
    HOOK_LOCK,
    HOOK_POWER,
    MSG_CONFIG,
    MSG_ACTION,
    MSG_STATUS,
    MSG_UPDATE,
    HOOK_LOCKER,
    HOOK_DAEMON,
    HOOK_RELOAD,
    TRIGGER_KEY,
    TRIGGER_LOCK,
    HOOK_MONITOR,
    HOOK_STARTUP,
    HOOK_SUSPEND,
    TRIGGER_BLANK,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    LOCKER_TYPE_LID,
    TRIGGER_TIMEOUT,
    LOCKER_TYPE_KEY,
    LOCKER_TYPE_LOCK,
    LOCKER_TYPE_BLANK,
    LOCKER_TIME_BLANK,
    LOCKER_TIME_BACKOFF,
    LOCKER_TYPE_SUSPEND,
    LOCKER_TYPE_HIBERNATE,
)
from lib.constants.config import (
    LOCKER_PATH_DIR,
    LOCKER_EXEC_LOCK,
    LOCKER_TYPE_NAMES,
    LOCKER_PATH_STATUS,
    LOCKER_EXEC_DND_ON,
    LOCKER_EXEC_SUSPEND,
    DISPLAY_PATH_ACTIVE,
    LOCKER_PATH_BATTERY,
    LOCKER_EXEC_DND_OFF,
    DISPLAY_PATH_DEFAULT,
    LOCKER_PATH_WAKEALARM,
    LOCKER_EXEC_HIBERNATE,
    DISPLAY_PATH_CONNECTED,
)
from lib.constants.defaults import (
    DEFAULT_LOCKER_LID,
    DEFAULT_LOCKER_LOCK,
    DEFAULT_LOCKER_BLANK,
    DEFAULT_LOCKER_LOCKER,
    DEFAULT_LOCKER_SUSPEND,
    DEFAULT_LOCKER_KEY_LOCK,
    DEFAULT_LOCKER_HIBERNATE,
)


HOOKS = {
    HOOK_LOCK: "LockerClient.trigger",
    HOOK_POWER: "LockerClient.update",
    HOOK_DAEMON: "LockerClient.thread",
    HOOK_LOCKER: "LockerClient.update",
    HOOK_RELOAD: "LockerClient.startup",
    HOOK_SUSPEND: "LockerClient.sleep",
    HOOK_STARTUP: "LockerClient.startup",
    HOOK_SHUTDOWN: "LockerClient.shutdown",
    HOOK_HIBERNATE: "LockerClient.sleep",
}
HOOKS_SERVER = {
    HOOK_LOCK: "LockerServer.trigger",
    HOOK_POWER: "LockerServer.screen",
    HOOK_DAEMON: "LockerServer.thread",
    HOOK_LOCKER: "LockerServer.update",
    HOOK_RELOAD: "LockerServer.reload",
    HOOK_MONITOR: "LockerServer.screen",
    HOOK_SUSPEND: "LockerServer.suspend",
    HOOK_SHUTDOWN: "LockerServer.shutdown",
    HOOK_HIBERNATE: "LockerServer.hibernate",
}


def _on_power():
    s = None
    try:
        s = read(LOCKER_PATH_BATTERY, binary=True)
    except OSError:
        return False
    else:
        return s is not None and len(s) > 0 and s[0] == 0x31
    finally:
        del s


def _find_lid_switch(server):
    for i in glob("/dev/input/event*"):
        try:
            with open(i, "r") as f:
                b = bytearray(256)
                # 0x80FF4506 - EVIOCGNAME
                n = ioctl(f, 0x80FF4506, b)
        except OSError as err:
            server.error(f'[m/locker]: Cannot read the event "{i}"!', err)
            continue
        try:
            s = b[:n].decode("UTF-8")
            del b, n
            if s.startswith("Lid Switch"):
                server.debug(f'[m/locker]: Found the Lid Switch event at "{i}"!')
                return i
            del s
        except UnicodeDecodeError as err:
            server.error(f'[m/locker]: Cannot read the event "{i}" name!', err)
            continue
    return None


def _connected_displays(server):
    g = glob(DISPLAY_PATH_CONNECTED)
    for i in g:
        # NOTE(dij): Force detection of monitors first to see if any are
        #            connected but the kernel didn't enable them correctly.
        write(i, "detect", errors=False)
    c = 0
    for i in g:
        try:
            with open(i, "rb") as f:
                v = f.read(1)
        except OSError as err:
            server.error(f'[m/locker]: Cannot read from the display path "{i}"!', err)
            continue
        if len(v) > 0 and v[0] == 0x63:
            c += 1
        del v
    del g
    server.debug(f"[m/locker]: Detected {c} connected display(s)..")
    if c <= 1:
        return False
    del c
    a = 0
    for i in glob(DISPLAY_PATH_ACTIVE):
        try:
            with open(i, "rb") as f:
                v = f.read(1)
        except OSError as err:
            server.error(f'[m/locker]: Cannot read from the display path "{i}"!', err)
            continue
        if len(v) > 0 and v[0] == 0x65:
            a += 1
        del v
    server.debug(f"[m/locker]: Detected {a} active display(s)..")
    # NOTE(dij): We check to see if only one display is enabled and being used.
    #            sometimes we can have 0 active displays, which we should assume
    #            that we're using DPMS/DisplayTimeout to turn off the displays.
    #
    #            In that case we trust the connected displays number since there's
    #            not a super reliable way to detect single screen/multi-head setups.
    if a != 1:
        return True
    del a
    # NOTE(dij): Check the default Display if it's active and being used.
    g = glob(DISPLAY_PATH_DEFAULT)
    if len(g) != 1:
        return True
    try:
        with open(g[0], "rb") as f:
            v = f.read(1)
    except OSError as err:
        server.error(
            f'[m/locker]: Cannot read from the default display path "{g[0]}"!', err
        )
    else:
        return len(v) > 0 and v[0] == 0x65
    finally:
        del g
    return True


def _notify_control(server, enable):
    try:
        nulexec(LOCKER_EXEC_DND_ON if enable else LOCKER_EXEC_DND_OFF, wait=True)
    except OSError as err:
        server.error(
            f"[m/locker]: Cannot {'enable' if enable else 'disable'} notifications!",
            err,
        )


class Locker(object):
    __slots__ = ("name", "event", "expire")

    def __init__(self, server, manager, name, expire):
        self.name = name
        if isinstance(expire, int) and expire > 0:
            self.expire = expire + seconds()
            self.event = server.task(
                expire, manager._locker_close, (server, self), priority=5
            )
        else:
            self.event, self.expire = None, None


class Ability(object):
    __slots__ = ("lid", "key", "lock", "blank", "suspend", "hibernate")

    def __init__(self, lid, key, blank, lock, sus, hib):
        self.lid = lid
        self.key = key
        self.lock = lock
        self.blank = blank
        self.suspend = sus
        self.hibernate = hib

    @classmethod
    def defalts(cls):
        return cls(
            DEFAULT_LOCKER_LID,
            DEFAULT_LOCKER_KEY_LOCK,
            DEFAULT_LOCKER_BLANK,
            DEFAULT_LOCKER_LOCK,
            DEFAULT_LOCKER_SUSPEND,
            DEFAULT_LOCKER_HIBERNATE,
        )

    def to_dict(self):
        return {
            "lid": self.lid,
            "key": self.key,
            "lock": self.lock,
            "blank": self.blank,
            "suspend": self.suspend,
            "hibernate": self.hibernate,
        }

    def __str__(self):
        return dumps(
            {
                "lid": self.lid,
                "key": self.key,
                "lock": self.lock,
                "blank": self.blank,
                "suspend": self.suspend,
                "hibernate": self.hibernate,
            },
            sort_keys=True,
        )

    def can_lock(self):
        return isinstance(self.lock, int) and self.lock > 0

    def can_blank(self):
        return isinstance(self.blank, int) and self.blank > 0

    def can_suspend(self):
        return isinstance(self.suspend, int) and self.suspend > 0

    def can_hibernate(self):
        return isinstance(self.hibernate, int) and self.hibernate > 0

    def from_dict(self, data):
        self.lid = boolean(data.get("lid", DEFAULT_LOCKER_LID))
        self.key = boolean(data.get("key", DEFAULT_LOCKER_KEY_LOCK))
        try:
            self.lock = num(data.get("lock", DEFAULT_LOCKER_LOCK), False)
        except ValueError:
            self.lock = DEFAULT_LOCKER_LOCK
        try:
            self.blank = num(data.get("blank", DEFAULT_LOCKER_BLANK), False)
        except ValueError:
            self.blank = DEFAULT_LOCKER_BLANK
        try:
            self.suspend = num(data.get("suspend", DEFAULT_LOCKER_SUSPEND), False)
        except ValueError:
            self.suspend = DEFAULT_LOCKER_SUSPEND
        try:
            self.hibernate = num(data.get("hibernate", DEFAULT_LOCKER_HIBERNATE), False)
        except ValueError:
            self.hibernate = DEFAULT_LOCKER_HIBERNATE

    @classmethod
    def load(cls, server, name):
        try:
            blank = num(
                server.get(f"locker.{name}.blank", DEFAULT_LOCKER_BLANK),
                False,
            )
        except ValueError:
            server.warning(
                f'[m/locker]: Config value "locker.{name}.blank" is invalid (must be a positive number), '
                "using the default value!"
            )
            blank = DEFAULT_LOCKER_BLANK
        try:
            lock = num(
                server.get(f"locker.{name}.lockscreen", DEFAULT_LOCKER_LOCK), False
            )
        except ValueError:
            server.warning(
                f'[m/locker]: Config value "locker.{name}.lockscreen" is invalid (must be a positive number), '
                "using the default value!"
            )
            lock = DEFAULT_LOCKER_LOCK
        try:
            sus = num(
                server.get(f"locker.{name}.suspend", DEFAULT_LOCKER_SUSPEND), False
            )
        except ValueError:
            server.warning(
                f'[m/locker]: Config value "locker.{name}.suspend" is invalid (must be a positive number), '
                "using the default value!"
            )
            sus = DEFAULT_LOCKER_SUSPEND
        try:
            hib = num(
                server.get(f"locker.{name}.hibernate", DEFAULT_LOCKER_HIBERNATE),
                False,
            )
        except ValueError:
            server.warning(
                f'[m/locker]: Config value "locker.{name}.hibernate" is invalid (must be a positive number), '
                "using the default value!"
            )
            hib = DEFAULT_LOCKER_HIBERNATE
        return cls(
            boolean(server.get(f"locker.{name}.lid", DEFAULT_LOCKER_LID, True)),
            boolean(server.get(f"locker.{name}.key", DEFAULT_LOCKER_KEY_LOCK, True)),
            blank,
            lock,
            sus,
            hib,
        )


class LockerClient(object):
    __slots__ = (
        "_cmd",
        "_dpms",
        "_idle",
        "_lockdir",
        "_battery",
        "_sleeper",
        "_lockers",
        "_ability",
        "_backoff",
        "_sleeping",
        "_lockscreen",
        "_ability_ac",
        "_backoff_blank",
        "_ability_battery",
    )

    def __init__(self):
        self._cmd = list()
        self._dpms = None
        self._idle = None
        self._lockdir = None
        self._battery = False
        self._sleeper = None
        self._lockers = list()
        self._ability = Ability.defalts()
        self._backoff = None
        self._sleeping = False
        self._lockscreen = None
        self._ability_ac = Ability.defalts()
        self._backoff_blank = None
        self._ability_battery = Ability.defalts()

    def _locked(self):
        return self._lockscreen is not None and self._lockscreen.poll() is None

    def setup(self, server):
        self._ability_ac = Ability.load(server, "power")
        server.debug(f"[m/locker]: Loaded AC Abilities: {self._ability_ac}.")
        self._ability_battery = Ability.load(server, "battery")
        server.debug(f"[m/locker]: Loaded Battery Abilities: {self._ability_battery}.")
        if _on_power():
            self._ability, self._battery = self._ability_ac, False
            server.debug(f"[m/locker]: Using AC Abilities: {self._ability}.")
        else:
            self._ability, self._battery = self._ability_battery, True
            server.debug(f"[m/locker]: Using Battery Abilities: {self._ability}.")
        self._cmd = split(
            server.get("locker.lock_command", DEFAULT_LOCKER_LOCKER), True
        )
        if self._cmd is None:
            server.warning(
                '[m/locker]: Config value "locker.lock_command" is invalid (must be a non-empty string or list), '
                "using the default value!"
            )
            self._cmd = DEFAULT_LOCKER_LOCKER
        self._backoff_blank = cancel_nul(server, self._backoff_blank)
        self._idle_init(server)
        self._lockdir = expand(LOCKER_PATH_DIR)

    def _wake_backoff(self):
        # NOTE(dij): Clear the backoff, this happens if something slowed or stopped
        #            the suspend/hibernate process.
        self._backoff = None

    def _blank_backoff(self):
        self._backoff_blank = None

    def thread(self, server):
        if self._locked():
            self._wake_check(server)
        elif self._lockscreen is not None and self._lockscreen.poll() is not None:
            server.debug("[m/locker]: Lockscreen was removed, resetting lock status..")
            self._lock_unlock(server)
        if self._idle is None or self._idle.poll() is None:
            return
        server.warning(
            "[m/locker]: Idle process has unexpectedly closed, a reload is recommended!"
        )
        stop(self._idle)
        self._idle = None

    def shutdown(self, server):
        # NOTE(dij): If we're locked and we receive a shutdown, orphan the
        #            Lockscreen. It'll get killed if we're exiting a session
        #            but will stay up to prevent SMD from unlocking the device.
        self._lock_unlock(server, False)
        stop(self._idle)
        self._idle = None
        self._cmd.clear()
        self._lockers.clear()

    def _idle_init(self, server):
        x = list()
        if self._ability.can_blank():
            x += [
                "timeout",
                f"{self._ability.blank}",
                f"{LOCKER_EXEC_LOCK} blank",
                "resume",
                'swaymsg "output * power on"',
            ]
        if self._ability.can_lock():
            x += ["timeout", f"{self._ability.lock}", f"{LOCKER_EXEC_LOCK}"]
        if len(x) == 0:
            # NOTE(dij): Stop idle without restarting it.
            v = self._idle
            self._idle = None
            stop(v)
            del v
            return
        a = ["/usr/bin/swayidle", "-C", "/dev/null", "-w"] + x
        del x
        # NOTE(dij): Prevent the thread from registering this as the locker quiting
        #            randomally.
        v = self._idle
        self._idle = None
        if v is not None:
            server.debug("[m/locker]: Reloading idle process..")
            stop(v)
        del v
        try:
            self._idle = nulexec(a)
        except OSError as err:
            server.error('[m/locker]: Cannot start "swayidle"!', err)
        finally:
            del a

    def _wake_check(self, server):
        if self._sleeping:
            if self._sleeper is not None:
                self._sleeper = cancel_nul(server, self._sleeper)
            return
        if self._backoff is not None:
            return
        if not self._ability.can_lock():
            return server.debug(
                "[m/locker]: Client lacks the Lock ability, not doing a wake check."
            )
        if self._ability.can_suspend():
            if LOCKER_TYPE_SUSPEND in self._lockers:
                if self._sleeper is None:
                    return
                self._sleeper = cancel_nul(server, self._sleeper)
                return server.debug(
                    "[m/locker]: Suspend Locker was detected, canceling Suspend timeout."
                )
        elif self._ability.can_hibernate():
            if LOCKER_TYPE_HIBERNATE in self._lockers:
                if self._sleeper is None:
                    return
                self._sleeper = cancel_nul(server, self._sleeper)
                return server.debug(
                    "[m/locker]: Hibernate Locker was detected, canceling Hibernate timeout."
                )
        if self._sleeper is not None:
            return
        if self._ability.can_suspend():
            t = self._ability.suspend
        else:
            t = self._ability.hibernate
        server.debug(f'[m/locker]: Setting Lockscreen timeout event for "{t}" seconds.')
        self._sleeper = server.task(t, self._wake_attempt, (server,), priority=5)
        del t

    def _wake_attempt(self, server):
        self._sleeper = cancel_nul(server, self._sleeper)
        self._lock(server, True)
        server.info("[m/locker]: Lockscreen timeout was hit, triggering Suspend!")
        server.send(None, Message(HOOK_LOCK, {"trigger": TRIGGER_TIMEOUT}))
        if self._backoff is not None:
            server.cancel(self._backoff)
        # NOTE(dij): Add a small ~5s backoff event to prevent setting another
        #            wake event while the device is processing the timeout trigger.
        self._backoff = server.task(
            LOCKER_TIME_BACKOFF, self._wake_backoff, priority=10
        )

    def sleep(self, server, message):
        if message.type == MSG_PRE:
            server.info(
                f"[m/locker]: Received a {'Suspend' if message.header() == HOOK_SUSPEND else 'Hibernate'} request!"
            )
            self._sleeper, self._sleeping = cancel_nul(server, self._sleeper), True
            self._backoff = cancel_nul(server, self._backoff)
            self._lock(server, True)
            return HOOK_OK
        # NOTE(dij); Backoff is stopped here just incase the event falls through.
        self._sleeping, self._backoff = False, cancel_nul(server, self._backoff)
        if not self._locked():
            self._lock(server, True)
        else:
            self._wake_check(server)
        try:
            swaymsg(0, "output * power on")
        except OSError as err:
            server.error("[m/locker]: Cannot power on the Displays!", err)
        # NOTE(dij): Check power source after suspend/resume.
        if _on_power():
            if not self._battery:
                return
            self._ability, self._battery = self._ability_ac, False
            server.debug(f"[m/locker]: Switching to AC Abilities: {self._ability}.")
        else:
            if self._battery:
                return
            self._ability, self._battery = self._ability_battery, True
            server.debug(
                f"[m/locker]: Switching to Battery Abilities: {self._ability}."
            )
        self._idle_init(server)
        server.debug("[m/locker]: Updating the Server with the new Abilities.")
        return Message(
            HOOK_LOCKER, {"type": MSG_CONFIG, "abilities": self._ability.to_dict()}
        )

    def update(self, server, message):
        if message.header() == HOOK_POWER:
            if message.type == MSG_PRE:  # Power Detached
                if self._battery:
                    return
                self._ability, self._battery = self._ability_battery, True
                server.debug(
                    f"[m/locker]: Switching to Battery Abilities: {self._ability}."
                )
            elif message.type == MSG_POST:  # Power Attached
                if not self._battery:
                    return
                self._ability, self._battery = self._ability_ac, False
                server.debug(f"[m/locker]: Switching to AC Abilities: {self._ability}.")
            else:
                return
            self._idle_init(server)
            server.debug("[m/locker]: Updating the Server with the new Abilities.")
            return Message(
                HOOK_LOCKER, {"type": MSG_CONFIG, "abilities": self._ability.to_dict()}
            )
        if message.type != MSG_STATUS or message.lockers is None:
            return
        if isinstance(message.lockers, dict):
            self._lockers = list(message.lockers.keys())
        else:
            self._lockers = message.lockers
        server.debug(
            f"[m/locker]: Received an updated list of Lockers! ({self._lockers})"
        )

    def trigger(self, server, message):
        if message.type is not None:
            return
        if message.trigger == TRIGGER_BLANK:
            if not self._ability.can_blank():
                return server.debug(
                    "[m/locker]: Ignoring Blank request as we lack the Blank ability."
                )
            if LOCKER_TYPE_BLANK in self._lockers:
                return server.debug(
                    "[m/locker]: Ignoring Blank request due to Blank Locker!"
                )
            if self._backoff_blank is not None:
                return server.debug(
                    "[m/locker]: Ignoring Blank request due to Lockscreen backoff!"
                )
            try:
                swaymsg(0, "output * power off")
            except OSError as err:
                server.error("[m/locker]: Cannot power off the Displays!", err)
            return
        # NOTE(dij): Handeling of the Key Locker is handled at the Server level.
        if message.trigger == TRIGGER_KEY and not self._ability.key:
            return server.debug(
                "[m/locker]: Ignoring Key request as we lack the Key ability."
            )
        self._lock(server, message.force or message.trigger == TRIGGER_KEY)

    def startup(self, server, message):
        if message.header() == HOOK_RELOAD:
            if self._locked():
                return server.warning(
                    "[m/locker]: Not reloading Locker config as we're currently locked!"
                )
            stop(self._idle)
            self._idle = None
            self._cmd.clear()
            self._lockers.clear()
            self.setup(server)
        _notify_control(server, False)
        server.debug("[m/locker]: Sending Abilities and quering for current Lockers..")
        return Message(
            HOOK_LOCKER, {"type": MSG_UPDATE, "abilities": self._ability.to_dict()}
        )

    def _lock(self, server, force=False):
        if self._locked():
            return
        if not self._ability.can_lock() and not force:
            return server.info(
                "[m/locker]: Ignoring non-force Lockscreen request as we lack the Lockscreen ability!"
            )
        if LOCKER_TYPE_LOCK in self._lockers and not force:
            return server.debug(
                "[m/locker]: Ignoring non-force Lockscreen request due to Lockscreen Locker!"
            )
        try:
            self._lockscreen = nulexec(self._cmd, cwd=self._lockdir)
        except OSError as err:
            self._lock_unlock(server)
            return server.error("[m/locker]: Cannot start the Lockscreen process!", err)
        server.info(
            f'[m/locker]: Started the Lockscreen with PID "{self._lockscreen.pid}".'
        )
        _notify_control(server, True)
        self._lock_dpms(server, True)
        self._wake_check(server)
        self._backoff_blank = cancel_nul(server, self._backoff_blank)
        server.send(None, Message(HOOK_LOCK, {"type": MSG_PRE}))

    def _lock_dpms(self, server, enable):
        if enable:
            try:
                if self._idle is not None and self._idle.poll() is None:
                    self._idle.send_signal(SIGSTOP)
            except OSError as err:
                server.error("[m/locker]: Cannot pause the idle process!", err)
            stop(self._dpms)
            try:
                self._dpms = nulexec(
                    [
                        "/usr/bin/swayidle",
                        "-C",
                        "/dev/null",
                        "-w",
                        "timeout",
                        f"{LOCKER_TIME_BLANK}",
                        'swaymsg "output * power off"',
                        "resume",
                        'swaymsg "output * power on"',
                    ]
                )
            except OSError as err:
                return server.error(
                    "[m/locker]: Cannot start the Lockscreen idle process!", err
                )
            return server.debug("[m/locker]: Enabled DPMS and started idle processes.")
        if self._dpms is None:
            return
        stop(self._dpms)
        self._dpms = None
        try:
            if self._idle is not None and self._idle.poll() is None:
                self._idle.send_signal(SIGCONT)
        except OSError as err:
            return server.error("[m/locker]: Cannot resume the idle process!", err)
        try:
            swaymsg(0, "output * power on")
        except OSError as err:
            server.error("[m/locker]: Cannot power on the Displays!", err)
        server.debug("[m/locker]: Disabled DPMS and stopped idle processes.")

    def _lock_unlock(self, server, unlock=True):
        if self._lockscreen is not None:
            if unlock:
                try:
                    # NOTE(dij): Send SIGUSR1 to swaylock as SIGINT/SIGTERM does
                    #            not close the lockscreen.
                    self._lockscreen.send_signal(SIGUSR1)
                except OSError:
                    pass
                stop(self._lockscreen)
                server.debug(
                    "[m/locker]: Unlocked the Lockscreen and canceled any timeouts!"
                )
                server.send(None, Message(HOOK_LOCK, {"type": MSG_POST}))
            self._lock_dpms(server, False)
        self._sleeper, self._lockscreen = cancel_nul(server, self._sleeper), None
        self._backoff = cancel_nul(server, self._backoff)
        self._backoff_blank = server.task(LOCKER_TIME_BACKOFF, self._blank_backoff)
        if unlock:
            _notify_control(server, False)


class LockerServer(object):
    __slots__ = (
        "_lid",
        "_update",
        "_ability",
        "_backoff",
        "_lockers",
        "_lid_path",
        "_displays",
        "_wake_alarm",
        "_suspending",
        "_hibernating",
    )

    def __init__(self):
        self._lid = None
        self._update = False
        self._ability = Ability.defalts()
        self._backoff = None
        self._lockers = dict()
        self._displays = False
        self._lid_path = None
        self._wake_alarm = False
        self._suspending = False
        self._hibernating = False

    def _backoff_clear(self):
        self._backoff = None

    def thread(self, server):
        self._notify(server)
        self._lid_check(server)

    def _notify(self, server):
        if not self._update:
            return
        server.debug("[m/locker]: Updating clients on Locker status..")
        server.broadcast(
            Message(
                HOOK_LOCKER, {"type": MSG_STATUS, "lockers": list(self._lockers.keys())}
            ),
        )
        write(
            LOCKER_PATH_STATUS,
            NEWLINE.join(self._lockers.keys()),
            perms=0o0644,
            errors=False,
        )
        if len(self._lockers) > 0:
            v = time()
            m = NEWLINE.join(
                [
                    f"{LOCKER_TYPE_NAMES.get(n, n.title())} ({time_to_str(l.expire, v)})"
                    for n, l in self._lockers.items()
                ]
            )
            del v
        else:
            m = "No lockers are enabled."
        server.notify("Lockers Updated", m, "caffeine")
        del m
        self._update = False

    def shutdown(self, server):
        if self._lid is None:
            return
        server.debug("[m/locker]: Closing the Lid switch file.")
        try:
            self._lid.close()
        except OSError:
            pass
        self._lid = None

    def _wake_set(self, server):
        if not self._ability.can_hibernate():
            return server.info(
                "[m/locker]: Ignoring wake alarm request as the client lacks the Hibernate ability."
            )
        b = self._lockers.get(LOCKER_TYPE_HIBERNATE)
        if b is not None:
            if b.expire is None or b.expire > (seconds() + self._ability.hibernate):
                return server.debug(
                    "[m/locker]: Ignoring wake alarm request due to Hibernate Locker!"
                )
            server.debug(
                "[m/locker]: Removing a Hibernate Locker that will expire while sleeping."
            )
            self._locker_remove(server, LOCKER_TYPE_HIBERNATE, False)
        del b
        server.debug(
            f'[m/locker]: Setting the RTC alarm "{LOCKER_PATH_WAKEALARM}" to wake the system to '
            f'Hibernate in "{self._ability.hibernate}" seconds.'
        )
        try:
            write(LOCKER_PATH_WAKEALARM, f"{seconds() + self._ability.hibernate}")
        except OSError as err:
            if err.errno == 0x10:
                try:
                    # NOTE(dij): Fix a bug where sometimes the RTC isn't cleared
                    #            properly.
                    write(LOCKER_PATH_WAKEALARM, "0")
                    write(
                        LOCKER_PATH_WAKEALARM,
                        f"{round(time()) + self._ability.hibernate}",
                    )
                except OSError as err:
                    return server.error("[m/locker]: Cannot set the wake alarm!", err)
            else:
                return server.error("[m/locker]: Cannot set the wake alarm!", err)
        self._wake_alarm = True
        server.info(
            f'[m/locker]: Hibernate wake alarm set for "{self._ability.hibernate}" seconds.'
        )

    def _lid_check(self, server):
        if (
            self._backoff is not None
            or self._lid is None
            or self._suspending
            or self._hibernating
            or not self._ability.lid
            or LOCKER_TYPE_LID in self._lockers
        ):
            return
        # NOTE(dij): We're async reading the Lid switch, as it outputs a 48b data
        #            segment on state change. If nothing happens, this returns None.
        try:
            v = self._lid.read(48)
        except OSError as err:
            return server.error(
                f'[m/locker]: Cannot read the Lid switch "{self._lid_path}"!', err
            )
        # NOTE(dij): Like all evdev events, the state flag is on the 20th byte.
        if isinstance(v, bytes) and len(v) > 20:
            # and v[20] == 1:
            # We're going to fire on any lid opens and closes so we can turn on
            # the Display if needed.
            server.debug(
                f'[m/locker]: Detected a Lid {"close" if v[20] == 1 else "open"} event!'
            )
            if v[20] == 1 and self._backoff is not None:
                # NOTE(dij): Prevent any display disconnections from being
                #            taken as Lid closure events. Give grace time first.
                #
                #            We check this state up top, but we should check it
                #            here before updating to prevent any race conditions.
                return server.debug(
                    "[m/locker]: Ignoring Lid closure as the screen backoff is in effect."
                )
            # NOTE(dij): Update the clients about a potential Display change.
            self.screen(server, None, v[20] == 0)
            if (
                v[20] == 1
                and not self._displays
                and not self._suspending
                and not self._hibernating
            ):
                server.debug(
                    "[m/locker]: Attempting to trigger Suspend via Lid closure!"
                )
                self._suspend(server, True)
        del v

    def _wake_check(self, server):
        if not self._wake_alarm:
            return False
        self._wake_alarm = False
        if not self._ability.can_hibernate() or LOCKER_TYPE_HIBERNATE in self._lockers:
            return False
        server.debug(f'[m/locker]: Checking the wake alarm "{LOCKER_PATH_WAKEALARM}"..')
        try:
            a = read(LOCKER_PATH_WAKEALARM)
        except OSError as err:
            return server.error("[m/locker]: Cannot read the wake alarm!", err)
        if len(a) > 0:
            try:
                write(LOCKER_PATH_WAKEALARM, "0")
            except OSError as err:
                server.error("[m/locker]: Cannot reset the wake alarm!", err)
            return False
        del a
        return True

    def setup_server(self, server):
        write(LOCKER_PATH_STATUS, EMPTY, perms=0o0644, errors=False)
        self._lid_path, self._lid = _find_lid_switch(server), None
        if not nes(self._lid_path):
            server.error(
                "[m/locker]: Cannot find a Lid Switch, Lid events will not function!"
            )
            return self.screen(server, None)
        try:
            self._lid = open(self._lid_path, "rb")
        except OSError as err:
            server.error(
                f'[m/locker]: Cannot open the Lid switch "{self._lid_path}"!',
                err,
            )
        try:
            f = fcntl(self._lid.fileno(), F_GETFL)
            fcntl(self._lid.fileno(), F_SETFL, f | O_NONBLOCK)
            del f
        except OSError as err:
            try:
                self._lid.close()
            except OSError:
                pass
            finally:
                self._lid = None
            server.error(
                f'[m/locker]: Cannot configure the Lid switch "{self._lid_path}"!',
                err,
            )
        self.screen(server, None)

    def update(self, server, message):
        if message.type == MSG_UPDATE or message.type == MSG_CONFIG:
            if message.abilities is None:
                return
            self._ability.from_dict(message.abilities)
            server.debug(
                f"[m/locker]: Updated client capabilities. {self._ability.to_dict()}"
            )
            if message.type == MSG_CONFIG:
                return
        if message.type == MSG_UPDATE or message.type == MSG_STATUS:
            if isinstance(message.locker, str) and message.locker in self._lockers:
                return {"type": MSG_STATUS, "time": self._lockers[message.lower].expire}
            return {
                "type": MSG_STATUS,
                "lockers": {n: v.expire for n, v in self._lockers.items()},
            }
        if message.type != MSG_ACTION:
            return
        if nes(message.name):
            try:
                return self._locker_add(
                    server, message.name, message.time, message.force
                )
            except ValueError as err:
                return as_error(f"Invaid Locker syntax for {message.name}: {err}")
        if not isinstance(message.list, list):
            return as_error("Invaid Locker structure")
        for i in message.list:
            if "name" not in i:
                continue
            try:
                self._locker_add(server, i["name"], i.get("time"), i.get("force"))
            except ValueError as err:
                return as_error(f'Invaid Locker syntax for {i["name"]}: {err}')

    def reload(self, server, message):
        if not message.all:
            return
        for i in self._lockers.values():
            self._locker_close(server, i, False, False)
        self._lockers.clear()
        self._update = False
        self.shutdown(server)
        self.setup_server(server)

    def trigger(self, server, message):
        if message.trigger is None and message.type is not None:
            if message.is_multicast():
                return
            return message.multicast()
        if message.type is not None:
            return
        if message.trigger == TRIGGER_BLANK:
            if not self._ability.can_blank():
                return server.info(
                    "[m/locker]: Ignoring Blank request as the client lacks the Blank ability."
                )
            if LOCKER_TYPE_BLANK in self._lockers:
                return server.debug(
                    "[m/locker]: Ignoring Blank request due to Blank Locker!"
                )
            return message.multicast()
        if message.trigger == TRIGGER_TIMEOUT:
            server.debug("[m/locker]: Received a Lockscreen timeout request!")
            return self._suspend(server)
        if message.trigger == TRIGGER_KEY:
            if message.uid() != 0:
                return server.warning(
                    "[m/locker]: Ignoring a Key request from a non-root user."
                )
            if not self._ability.key:
                return server.debug(
                    "[m/locker]: Ignoring Key request as the client lacks the Key ability."
                )
            if LOCKER_TYPE_KEY in self._lockers:
                return server.debug(
                    "[m/locker]: Ignoring Key request due to Key Locker!"
                )
        elif message.trigger == TRIGGER_LOCK:
            if not self._ability.can_lock():
                return server.info(
                    "[m/locker]: Ignoring non-force Lockscreen request as the client lacks the Lockscreen ability."
                )
            if LOCKER_TYPE_LOCK in self._lockers and not message.force:
                return server.debug(
                    "[m/locker]: Ignoring non-force Lockscreen request due to Lockscreen Locker!"
                )
        else:
            return as_error("invalid trigger type")
        server.debug("[m/locker]: Forwarding Lockscreen request..")
        return message.multicast()

    def suspend(self, server, message):
        if message.uid() != 0:
            return server.warning(
                "[m/locker]: Ignoring a Suspend request from a non-root user."
            )
        if message.type == MSG_PRE:
            self._wake_alarm, self._hibernating = False, False
            if self._suspending:
                return
            server.info(
                "[m/locker]: Pre-Suspend request received, preparing to Suspend!"
            )
            self._suspending = True
            self._wake_set(server)
        elif message.type == MSG_POST:
            if not self._suspending:
                return
            server.debug(
                "[m/locker]: Post-Suspend request received, releasing Hibernation locks!"
            )
            self._suspending, self._hibernating = False, False
            if self._wake_check(server):
                server.info(
                    "[m/locker]: Wake alarm was triggered, starting Hibernation!"
                )
                try:
                    nulexec(LOCKER_EXEC_HIBERNATE, wait=True)
                except OSError as err:
                    server.error("[m/locker]: Hibernation command failed!", err)
                return
            # NOTE(dij): Prevent cascading suspends and wait a little for to check
            #            again.
            server.cancel(self._backoff)
            self._backoff = server.task(LOCKER_TIME_BACKOFF, self._backoff_clear)
            self.screen(server, None)
        return message.multicast()

    def hibernate(self, server, message):
        if message.uid() != 0:
            return server.warning(
                "[m/locker]: Ignoring a Hibernate request from a non-root user."
            )
        if message.type == MSG_PRE:
            self._wake_alarm, self._suspending = False, False
            if self._hibernating:
                return
            server.info(
                "[m/locker]: Pre-Hibernation request received, preparing to Hibernate!"
            )
            self._hibernating = True
        elif message.type == MSG_POST:
            self._wake_alarm = False
            if not self._hibernating:
                return
            server.debug(
                "[m/locker]: Post-Hibernation request received, releasing Hibernation locks!"
            )
            self._suspending, self._hibernating = False, False
            # NOTE(dij): Prevent cascading suspends and wait a little for to check
            #            again.
            server.cancel(self._backoff)
            self._backoff = server.task(LOCKER_TIME_BACKOFF, self._backoff_clear)
            self.screen(server, None)
        return message.multicast()

    def _suspend(self, server, is_lid=False):
        if self._backoff is not None:
            # NOTE(dij): Same as the Lid closure event, prevent suspending when
            #            disconnecting docks or external monitors.
            return server.debug(
                "[m/locker]: Ignoring Suspend request as the screen backoff is in effect!"
            )
        if not self._ability.can_suspend():
            if not self._ability.can_hibernate():
                return server.debug(
                    "[m/locker]: Ignoring Suspend request as the client lacks the Suspend and Hibernate abilities."
                )
            server.info(
                "[m/locker]: Changing Suspend request to Hibernate as the client lacks the Suspend ability."
            )
            if LOCKER_TYPE_HIBERNATE in self._lockers:
                return server.debug(
                    "[m/locker]: Ignoring Hibernate request due to Hibernate Locker!"
                )
            try:
                nulexec(LOCKER_EXEC_HIBERNATE, wait=True)
            except OSError as err:
                server.error("[m/locker]: Hibernation command failed!", err)
            return
        if LOCKER_TYPE_SUSPEND in self._lockers and not is_lid:
            return server.debug(
                "[m/locker]: Ignoring Suspend request due to Suspend Locker!"
            )
        try:
            nulexec(LOCKER_EXEC_SUSPEND, wait=True)
        except OSError as err:
            server.error("[m/locker]: Suspend command failed!", err)

    def screen(self, server, message, close=True):
        if message is not None and message.uid() != 0:
            return server.warning(
                "[m/locker]: Ignoring a Screen request from a non-root user."
            )
        if self._backoff is not None:
            # NOTE(dij): We use a backoff period to prevent back-n-forth switches
            #            triggered by multiple udev events.
            #            Currently it's at 5sec which should be good enough to be
            #            stable.
            return server.debug(
                "[m/locker]: Waiting longer to check the Display status."
            )
        if close:
            self._backoff = server.task(LOCKER_TIME_BACKOFF, self._backoff_clear)
        # NOTE(dij): We only care if we have more than one active display or a
        #            single active display that isn't the builtin display.
        self._displays = _connected_displays(server)
        if message is None:
            return server.broadcast(Message(HOOK_MONITOR))
        if message.header() == HOOK_POWER:
            return
        return message.multicast()

    def _locker_remove(self, server, name, notify=True):
        x = self._lockers.pop(name, None)
        if x is not None:
            self._locker_close(server, x, notify, False)
        del x

    def _locker_add(self, server, name, expires, force=False):
        if name not in LOCKER_TYPE_NAMES:
            raise ValueError("invalid locker name")
        if name in self._lockers and not force:
            return
        if expires is None:
            e = None
        else:
            try:
                e = num(expires)
            except ValueError:
                raise ValueError("invalid expire time")
            if e <= 0:
                return self._locker_remove(server, name)
        x = self._lockers.get(name)
        # NOTE(dij): We shouldn't remove Lockers that match the one we want to set.
        if x is not None and e == x.expire:
            return
        if x is not None:
            self._locker_remove(server, name, False)
        del x
        if e is None:
            server.debug(f'[m/locker]: Added a Locker "{name}" with no expire timeout.')
        else:
            server.debug(
                f'[m/locker]: Added a Locker "{name}" with a timeout of "{e}" seconds.'
            )
        self._lockers[name] = Locker(server, self, name, e)
        self._update = True
        del e

    def _locker_close(self, server, locker, notify=True, remove=True):
        if remove:
            self._lockers.pop(locker.name, None)
        server.debug(f'[m/locker]: Removed Locker "{locker.name}"!')
        locker.event, locker.expire = cancel_nul(server, locker.event), None
        if not notify:
            return
        self._update = True
