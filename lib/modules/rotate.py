#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: Rotate (User, System)
#
# Manages the system orientation and position.
# Updated 10/2018

from glob import glob
from os.path import join
from lib.util import read, run, write
from lib.structs.message import Message
from lib.modules.background import set_background
from lib.constants import (
    HOOK_ROTATE,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_NOTIFICATION,
    HOOK_TABLET,
    ROTATION_CORD_STATES,
    ROTATION_LOCK_STATUS,
    ROTATION_THREASHOLD,
    ROTATION_THREASHOLD_NEG,
    ROTATION_DEVICES,
    ROTATION_GYROS,
    EMPTY,
    TABLET_STATE_CLOSED,
    TABLET_STATE_LAPTOP,
)

HOOKS = {HOOK_ROTATE: "RotateClient.rotate", HOOK_RELOAD: "RotateClient.setup"}
HOOKS_SERVER = {
    HOOK_TABLET: "RotateServer.thread",
    HOOK_DAEMON: "RotateServer.thread",
    HOOK_HIBERNATE: "RotateServer.hooks",
    HOOK_SHUTDOWN: "RotateServer.hooks",
    HOOK_ROTATE: "RotateServer.hooks",
    HOOK_RELOAD: "RotateServer.setup_server",
}


class RotateClient(object):
    def __init__(self):
        self.inputs = list()

    def setup(self, server):
        self.inputs.clear()
        try:
            devices = run(ROTATION_DEVICES, wait=2, ignore_errors=False)
        except OSError as err:
            server.error('Reading from "xinput" raised an exception!', err=err)
        else:
            if isinstance(devices, str):
                device_list = devices.split("\n")
                for device in device_list:
                    name = device.lower()
                    if ("touchscreen" in name or "wacom" in name) and "pen" not in name:
                        self.inputs.append(device)
                        server.debug('Added device "%s" for rotate input.' % name)
                    del name
                del devices
                del device_list

    def rotate(self, server, message):
        if message.header() == HOOK_ROTATE and "state" in message:
            server.debug('Rotating screen to "%s"..' % message["state"])
            try:
                run(["/usr/bin/xrandr", "-o", message["state"]], ignore_errors=False)
            except OSError as err:
                server.error(
                    "Attempting to rotate the screen raised an exception!", err=err
                )
            gyros = [
                "/usr/bin/xinput",
                "set-prop",
                EMPTY,
                "Coordinate Transformation Matrix",
            ]
            if message.get("state") in ROTATION_CORD_STATES:
                gyros += ROTATION_CORD_STATES[message["state"]]
            for device in self.inputs:
                gyros[2] = device
                try:
                    run(gyros, ignore_errors=False)
                except OSError as err:
                    server.error(
                        'Attempting to rotate the input device "%s" raised an exception!'
                        % device,
                        err=err,
                    )
            del gyros
            set_background(server)


class RotateServer(object):
    def __init__(self):
        self.count = 1
        self.gyro = None
        self.scale = 0.0
        self.lock = False
        self.state = None
        self.closed = False
        self.handle_x = None
        self.handle_y = None

    def thread(self, server):
        if self.lock or self.count > 1 and not self.closed:
            return
        if self.gyro is None and (self.handle_y is None or self.handle_x is None):
            self.setup_server(server)
            if self.gyro is None:
                return
        if self.handle_x is not None and self.handle_y is not None:
            try:
                current_x = float(self.handle_x.read()) * self.scale
                current_y = float(self.handle_y.read()) * self.scale
            except (OSError, ValueError) as err:
                server.error(
                    "Attempting to read rotation states raised an exception!", err=err
                )
            else:
                try:
                    self.handle_x.seek(0)
                    self.handle_y.seek(0)
                except (OSError, ValueError) as err:
                    server.error(
                        "Attempting to reset rotation state handles raised an exception!",
                        err=err,
                    )
                state = None
                if current_x >= ROTATION_THREASHOLD and self.state != "left":
                    state = "left"
                elif current_y >= ROTATION_THREASHOLD and self.state != "inverted":
                    state = "inverted"
                elif current_x <= ROTATION_THREASHOLD_NEG and self.state != "right":
                    state = "right"
                elif current_y <= ROTATION_THREASHOLD_NEG and self.state != "normal":
                    state = "normal"
                if (
                    state is not None
                    and self.state != state
                    # and server.swap("displays", 1) <= 1
                    # and not server.swap("closed", False)
                ):
                    self.state = state
                    server.debug('Changing rotation state to "%s".' % self.state)
                    server.send(None, Message(HOOK_ROTATE, {"state": state}))
                    del state
            finally:
                del current_x
                del current_y

    def setup_server(self, server):
        server.debug("Setting up Gyro devices..")
        self.lock = server.config("rotate_lock", True)
        write(ROTATION_LOCK_STATUS, int(self.lock), ignore_errors=True)
        if self.handle_x is not None:
            try:
                self.handle_x.close()
            except (AttributeError, OSError) as err:
                server.error(
                    "Attempting to close Gyro device handle raised an exception!",
                    err=err,
                )
        if self.handle_y is not None:
            try:
                self.handle_y.close()
            except (AttributeError, OSError) as err:
                server.error(
                    "Attempting to close Gyro device handle raised an exception!",
                    err=err,
                )
        self.gyro = None
        for device in glob(ROTATION_GYROS):
            try:
                name = read(join(device, "name"), ignore_errors=False)
            except OSError as err:
                server.error("Could read Gyro device!", err=err)
            else:
                if isinstance(name, str) and "accel" in name:
                    self.gyro = device
                    break
        if self.gyro is None:
            server.error("Could not find an available Gyro device!")
        else:
            server.debug('Found Gyro device "%s".' % self.gyro)
            try:
                self.scale = float(
                    read(join(self.gyro, "in_accel_scale"), ignore_errors=False)
                )
            except (ValueError, OSError) as err:
                server.error(
                    "Attempting to read Gyro scale raised an exception!", err=err
                )
                self.gyro = None
            else:
                try:
                    self.handle_x = open(join(self.gyro, "in_accel_x_raw"), "r")
                    self.handle_y = open(join(self.gyro, "in_accel_y_raw"), "r")
                except OSError as err:
                    server.error(
                        "Attempting to read handles into Gyro devices raised an exception!",
                        err=err,
                    )
                    self.gyro = None

    def hooks(self, server, message):
        if message.header() == HOOK_TABLET:
            if message.get("count"):
                self.count = message.get("count")
            else:
                self.closed = (
                    message.get("state", TABLET_STATE_LAPTOP) == TABLET_STATE_CLOSED
                )
        elif message.header() == HOOK_ROTATE:
            if message.get("query"):
                return {"lock": self.lock}
            else:
                if message.get("toggle"):
                    self.lock = server.set("rotate_lock", not self.lock)
                else:
                    self.lock = server.set("rotate_lock", message.get("lock", False))
                write(ROTATION_LOCK_STATUS, int(self.lock), ignore_errors=True)
                server.debug('Set screen rotation lock status to "%s".' % self.lock)
                server.send(
                    None,
                    Message(
                        header=HOOK_NOTIFICATION,
                        payload={
                            "title": "Rotation Lock Status",
                            "body": "Rotation lock was %s."
                            % ("Enabled" if self.lock else "Disabled"),
                            "icon": "mintBackup",
                        },
                    ),
                )
        elif message.header() == HOOK_SHUTDOWN or message.header() == HOOK_HIBERNATE:
            if "post" not in message.get("state", EMPTY):
                server.debug("Closing out Gyro device handles..")
                if self.handle_x is not None:
                    try:
                        self.handle_x.close()
                    except OSError as err:
                        server.error(
                            "Attempting to close Gyro device handle raised an exception!",
                            err=err,
                        )
                if self.handle_y is not None:
                    try:
                        self.handle_y.close()
                    except OSError as err:
                        server.error(
                            "Attempting to close Gyro device handle raised an exception!",
                            err=err,
                        )
                self.handle_x = None
                self.handle_y = None
            elif message.get("state") == "post-driver":
                self.setup_server(server)


# EOF
