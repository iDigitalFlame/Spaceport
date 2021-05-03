#!/usr/bin/false
# Module: Rotate (User, System)
#
# Manages the system orientation and position.
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
from os import O_NONBLOCK
from os.path import exists
from lib.structs.message import Message
from fcntl import fcntl, F_GETFL, F_SETFL
from lib.util import read, run, write, boolean
from lib.constants import (
    EMPTY,
    HOOK_ROTATE,
    ROTATE_LEFT,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_DISPLAY,
    ROTATE_RIGHT,
    ROTATE_NORMAL,
    HOOK_SHUTDOWN,
    HOOK_BACKGROUND,
    ROTATE_INVERTED,
    ROTATE_THRESHOLD,
    HOOK_NOTIFICATION,
    ROTATE_PATH_GYROS,
    ROTATE_ITHRESHOLD,
    ROTATE_PATH_STATUS,
    ROTATE_PATH_BUTTON,
    ROTATE_CORD_STATES,
    ROTATE_STATE_NAMES,
    ROTATE_EXEC_DEVICES,
    MESSAGE_TYPE_CONFIG,
    MESSAGE_TYPE_STATUS,
    ROTATE_DEVICE_NAMES,
)

HOOKS_SERVER = {
    HOOK_DAEMON: "RotateServer.thread",
    HOOK_ROTATE: "RotateServer.update",
    HOOK_RELOAD: "RotateServer.reload",
    HOOK_DISPLAY: "RotateServer.monitor",
    HOOK_SHUTDOWN: "RotateServer.reload",
}
HOOKS = {
    HOOK_ROTATE: "RotateClient.rotate",
    HOOK_RELOAD: "RotateClient.reload",
}


class RotateClient(object):
    def __init__(self):
        self.inputs = list()

    def setup(self, server):
        try:
            devices = run(ROTATE_EXEC_DEVICES, wait=True, ignore_errors=False)
        except OSError as err:
            return server.error(
                'Reading devices list from "xinput" raised an exception!', err=err
            )
        if not isinstance(devices, str):
            del devices
            return
        for device in devices.split("\n"):
            name = device.lower()
            if "pen" in name:
                continue
            for touch in ROTATE_DEVICE_NAMES:
                if touch not in name:
                    continue
                if device in self.inputs:
                    self.inputs.remove(device)
                    self.inputs.append(f"pointer:{device}")
                    break
                self.inputs.append(device)
                server.debug(f'Added touch device "{device}" for rotate input.')
                break
            del name
        del devices

    def reload(self, server):
        self.inputs.clear()
        self.setup(server)

    def rotate(self, server, message):
        if message.position is None:
            return
        state = ROTATE_STATE_NAMES.get(message.position)
        if state is None:
            return
        server.debug(f'Rotating screen to "{state}"..')
        try:
            run(["/usr/bin/xrandr", "-o", state], ignore_errors=False)
        except OSError as err:
            return server.error(
                "Attempting to rotate the screen raised an exception!", err=err
            )
        matrix = ROTATE_CORD_STATES.get(message.position)
        if matrix is None:
            return
        devices = [
            "/usr/bin/xinput",
            "set-prop",
            EMPTY,
            "Coordinate Transformation Matrix",
        ] + matrix
        server.debug("Setting input devices matrix..")
        for device in self.inputs:
            devices[2] = device
            try:
                run(devices, ignore_errors=False)
            except OSError as err:
                server.error(
                    f'Attempting to rotate the input device "{device}" raised an exception!',
                    err=err,
                )
        del devices
        server.forward(Message(header=HOOK_BACKGROUND))


class RotateServer(object):
    def __init__(self):
        self.x = None
        self.y = None
        self.tries = 5
        self.scale = 0.0
        self.lock = False
        self.sensor = None
        self.button = None
        self.display_count = 1
        self.current = ROTATE_NORMAL

    def thread(self, server):
        if self.sensor is None or self.x is None or self.y is None:
            if self.tries > 0:
                self.setup_server(server)
            return
        self._check_button(server)
        if self.lock or self.display_count > 1:
            return
        try:
            x = float(self.x.read()) * self.scale
            y = float(self.y.read()) * self.scale
        except (OSError, ValueError) as err:
            return server.error(
                "Attempting to read rotation states raised an exception!", err=err
            )
        try:
            self.x.seek(0)
            self.y.seek(0)
        except OSError as err:
            return server.error(
                "Attempting to reset rotation state handles raised an exception!",
                err=err,
            )
        rotate = self._get_state(x, y)
        del x
        del y
        if rotate is None or rotate == self.current:
            return
        server.debug(f'Changing rotation state to "{rotate}"!')
        server.send(None, Message(HOOK_ROTATE, {"position": rotate}))
        self.current = rotate
        del rotate

    def _get_state(self, x, y):
        if x >= ROTATE_THRESHOLD and self.current != ROTATE_LEFT:
            return ROTATE_LEFT
        if y >= ROTATE_THRESHOLD and self.current != ROTATE_INVERTED:
            return ROTATE_INVERTED
        if x <= ROTATE_ITHRESHOLD and self.current != ROTATE_RIGHT:
            return ROTATE_RIGHT
        if y <= ROTATE_ITHRESHOLD and self.current != ROTATE_NORMAL:
            return ROTATE_NORMAL
        return None

    def monitor(self, _, message):
        active = message.get("active", 1)
        if self.display_count == active:
            return
        self.display_count = active
        del active

    def setup_server(self, server):
        self.lock = server.get_config("rotate", False, True)
        server.debug("Detecting gyro sensor devices..")
        write(
            ROTATE_PATH_STATUS, str(self.lock).lower(), ignore_errors=True, perms=0o644
        )
        for device in glob(ROTATE_PATH_GYROS):
            try:
                name = read(f"{device}/name", ignore_errors=False)
            except OSError as err:
                server.error(f'Error reading gyro sensor "{device}"!', err=err)
                continue
            if isinstance(name, str) and "accel" in name:
                self.sensor = device
                break
        if self.sensor is None:
            self.tries = self.tries - 1
            write(ROTATE_PATH_STATUS, "invalid", ignore_errors=True, perms=0o644)
            if self.tries <= 0:
                return server.error(
                    "Could not find any compatible gyro sensors after 5 attempts, bailing out!"
                )
            return server.warning(
                f"Could not find any compatible gyro sensors! Attempt {5 - self.tries}."
            )
        server.debug(f'Found gyro sensor at "{self.sensor}", attempting to read..')
        try:
            self.scale = float(
                read(f"{self.sensor}/in_accel_scale", ignore_errors=False)
            )
        except (ValueError, OSError) as err:
            self.sensor = None
            return server.error(
                "Attempting to read gyro scale raised an exception!", err=err
            )
        try:
            self.x = open(f"{self.sensor}/in_accel_x_raw", "r")
            self.y = open(f"{self.sensor}/in_accel_y_raw", "r")
        except OSError as err:
            self.sensor = None
            write(ROTATE_PATH_STATUS, "invalid", ignore_errors=True, perms=0o644)
            return server.error(
                "Attempting to read handles into Gyro devices raised an exception!",
                err=err,
            )
        server.debug("Gyro sensor setup complete!")
        if exists(ROTATE_PATH_BUTTON):
            server.debug(
                f'Found rotate button "{ROTATE_PATH_BUTTON}", attempting to grab handle..'
            )
            try:
                self.button = open(ROTATE_PATH_BUTTON, "rb")
                flags = fcntl(self.button.fileno(), F_GETFL)
                fcntl(self.button.fileno(), F_SETFL, flags | O_NONBLOCK)
                del flags
            except OSError as err:
                server.error(
                    f'An exception occurred when attempting to read the button file "{ROTATE_PATH_BUTTON}"!',
                    err=err,
                )
            else:
                server.debug(f'Added rotate button "{ROTATE_PATH_BUTTON}" handle!')

    def _check_button(self, server):
        if self.button is None:
            return
        try:
            data = self.button.read(144)
        except OSError as err:
            return server.error("Could not read the button event file!", err=err)
        if isinstance(data, bytes) and len(data) > 20 and data[20] == 200:
            server.debug("Button press detected, switching lock!")
            self._set_lock(server, not self.lock)
        del data

    def _set_lock(self, server, lock):
        self.lock = lock
        server.debug(f'Set screen rotation lock status to "{self.lock}".')
        server.set_config("rotate", lock, True)
        write(
            ROTATE_PATH_STATUS, str(self.lock).lower(), ignore_errors=True, perms=0o644
        )
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Rotation Lock Status",
                    "body": f'Rotation lock was {"Enabled" if self.lock else "Disabled"}.',
                    "icon": "mintBackup",
                },
            ),
        )

    def update(self, server, message):
        if message.type == MESSAGE_TYPE_STATUS:
            return {"lock": self.lock}
        if message.type != MESSAGE_TYPE_CONFIG:
            return server.debug("Received an invalid rotate message type!")
        if message.toggle is not None:
            self._set_lock(server, not self.lock)
        elif message.lock is not None:
            self._set_lock(server, boolean(message.lock))

    def reload(self, server, message):
        self.tries = 0
        if self.x is not None:
            try:
                self.x.close()
            except OSError as err:
                server.error(
                    "An error occurred attempting to close the gyro X handle!", err=err
                )
        if self.y is not None:
            try:
                self.y.close()
            except OSError as err:
                server.error(
                    "An error occurred attempting to close the gyro Y handle!", err=err
                )
        self.sensor = None
        if self.button is not None:
            try:
                self.x.close()
            except OSError as err:
                server.error(
                    f'An error occurred attempting to close the handle to "{ROTATE_PATH_BUTTON}"!',
                    err=err,
                )
        if message.header() == HOOK_RELOAD:
            self.tries = 5
            self.setup_server(server)
