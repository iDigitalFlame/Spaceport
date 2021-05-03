#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Module: Session (User)
#
# Manages the User's startup and session processes.

from os import environ
from os.path import join
from lib.util import stop
from sched import scheduler
from time import time, sleep
from lib.modules.background import set_background
from subprocess import Popen, DEVNULL, SubprocessError
from lib.constants import (
    HOOK_SHUTDOWN,
    DIRECTORY_LIBEXEC,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_TABLET,
    HOOK_POWER,
    HOOK_ROTATE,
    HOOK_MONITOR,
    SESSION_DEFAULT_LOCK,
    SESSION_DEFAULT_BACKGROUND,
    EMPTY,
    SESSION_NETWORK,
    SESSION_COMPOSER,
    SESSION_PROFILES,
    HOOK_HIBERNATE,
    HOOK_LOCK,
    TABLET_STATE_TABLET,
    TABLET_STATE_LAPTOP,
    TABLET_STATE_CLOSED,
)

HOOKS = {
    HOOK_SHUTDOWN: "Session.hook",
    HOOK_DAEMON: "Session.thread",
    HOOK_RELOAD: "Session.hook",
    HOOK_TABLET: "Session.profile",
    HOOK_POWER: "Session.profile",
    HOOK_ROTATE: "Session.profile",
    HOOK_MONITOR: "Session.profile",
    HOOK_HIBERNATE: "Session.profile",
    HOOK_LOCK: "Session.profile",
}
SERVER_HOOKS = None


class Session(object):
    def __init__(self):
        self.locker = None
        self.composer = None
        self.profiles = dict()
        self.processes = list()
        self.background_time = 0
        self.background_event = None
        self.profile_processes = None
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def setup(self, server):
        try:
            self.background_time = int(
                server.config("background_time", SESSION_DEFAULT_BACKGROUND)
            )
        except ValueError:
            self.background_time = server.set(
                "background_time", SESSION_DEFAULT_BACKGROUND
            )
        if self.background_event is not None:
            try:
                self.scheduler.cancel(self.background_event)
            except ValueError:
                pass
            self.background_event = None
        try:
            lock_time = int(server.config("timeout_lock", SESSION_DEFAULT_LOCK))
        except ValueError:
            lock_time = server.set("timeout_lock", SESSION_DEFAULT_LOCK)
        try:
            self.locker = Popen(
                [
                    "/usr/bin/xautolock",
                    "-secure",
                    "-detectsleep",
                    "-time",
                    str(lock_time // 60),
                    "-locker",
                    join(DIRECTORY_LIBEXEC, "smd-locker"),
                ],
                env=environ,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        except (OSError, SubprocessError) as err:
            server.error('Starting "xautolock" raised an Exception!', err=err)
            self.locker = None
        del lock_time
        composer = server.config("composer", SESSION_COMPOSER)
        if not isinstance(composer, list) and not isinstance(composer, str):
            composer = server.set("composer", SESSION_COMPOSER)
        elif isinstance(composer, str):
            composer = composer.split(" ")
        try:
            self.composer = Popen(composer, stderr=DEVNULL, stdout=DEVNULL)
        except (OSError, SubprocessError, ValueError) as err:
            server.error(
                'Starting the composer "%s" raised an Exception!' % " ".join(composer),
                err=err,
            )
            self.composer = None
        del composer
        startup = server.config("startup", SESSION_NETWORK)
        if isinstance(startup, list) and len(startup) > 0:
            for process in startup:
                try:
                    self.processes.append(
                        Popen(process.split(" "), stdout=DEVNULL, stderr=DEVNULL)
                    )
                except (OSError, SubprocessError, ValueError) as err:
                    server.warning(
                        'Launching startup process "%s" raised an Exception!' % process,
                        err=err,
                    )
        del startup
        self.profiles = server.config("profiles", SESSION_PROFILES)
        if not isinstance(self.profiles, dict):
            server.set("profiles", SESSION_PROFILES)
            self.profiles = None

    def thread(self, server):
        if self.scheduler.empty() and self.background_time > 0:
            self.background_event = self.scheduler.enter(
                self.background_time, 1, set_background, argument=(server,)
            )
        self.scheduler.run(blocking=False)
        if len(self.processes) > 0:
            for process in list(self.processes):
                if process is not None and process.poll() is not None:
                    stop(process)
                    self.processes.remove(process)
                    del process
        if self.profile_processes is not None and len(self.profile_processes) > 0:
            for process in list(self.profile_processes):
                if process is not None and process.poll() is not None:
                    stop(process)
                    self.profile_processes.remove(process)
                    del process

    def hook(self, server, message):
        try:
            stop(self.locker)
            del self.locker
        except AttributeError:
            pass
        try:
            stop(self.composer)
            del self.composer
        except AttributeError:
            pass
        if len(self.processes) > 0:
            for process in self.processes:
                stop(process)
                del process
        self.processes.clear()
        if self.profile_processes is not None and len(self.profile_processes) > 0:
            for process in self.profile_processes:
                stop(process)
                del process
            self.profile_processes = None
        if message.header() == HOOK_RELOAD:
            self.setup(server)

    def profile(self, server, message):
        profile_name = None
        if message.header() == HOOK_POWER and message.get("type") == "power":
            if message.get("status") == "attached":
                profile_name = "power-ac"
            else:
                profile_name = "power-battery"
        elif message.header() == HOOK_HIBERNATE:
            if "pre" in message.get("state", EMPTY):
                profile_name = "sleep-pre"
            elif "post" in message.get("state", EMPTY):
                profile_name = "sleep-post"
        elif message.header() == HOOK_LOCK:
            if "post" in message.get("state", EMPTY):
                profile_name = "lock-post"
            else:
                profile_name = "lock-pre"
        elif (
            message.header() == HOOK_TABLET
            and message.get("state", TABLET_STATE_LAPTOP) > TABLET_STATE_CLOSED
        ):
            if message.get("state", TABLET_STATE_LAPTOP) == TABLET_STATE_TABLET:
                profile_name = "mode-tablet"
            else:
                profile_name = "mode-laptop"
        elif message.header() == HOOK_ROTATE:
            profile_name = "rotate"
        elif message.header() == HOOK_MONITOR:
            profile_name = "display"
        if profile_name is not None and profile_name in self.profiles:
            if self.profile_processes is not None and len(self.profile_processes) > 0:
                for process in self.profile_processes:
                    stop(process)
                    del process
            self.profile_processes = None
            profile_list = self.profiles[profile_name]
            if isinstance(profile_list, list) and len(profile_list) > 0:
                server.debug(
                    'Running profile commands for profile type "%s".' % profile_name
                )
                self.profile_processes = list()
                for profile_command in profile_list:
                    try:
                        self.profile_processes.append(
                            Popen(
                                profile_command.split(" "),
                                stderr=DEVNULL,
                                stdout=DEVNULL,
                            )
                        )
                    except (OSError, SubprocessError, ValueError) as err:
                        server.warning(
                            'Starting process "%s" raised an exception!', err=err
                        )
            del profile_list
            del profile_name
