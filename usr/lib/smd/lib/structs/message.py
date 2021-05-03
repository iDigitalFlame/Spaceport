#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Message class is a subclass of the "Storage" class that is designed specifically
# to be passed between client and server in binary format quickly.
# While using the Storage class to be internally flexable, the Message class also focuses
# on the ability to be written directly to a stream and read quickly.

from traceback import format_exc
from struct import unpack_from, pack
from lib.structs.storage import Storage
from json import loads, dumps, JSONDecodeError
from lib.constants import SOCKET_MESSAGE_INTEGER_SIZE
from socket import socket, AF_UNIX, SOCK_STREAM, timeout as socket_timeout


def send_exception(header, err):
    return Message(
        header=header,
        payload={
            "result": "Received an exception when attempting to process request!",
            "error": str(err),
            "trace": format_exc(limit=3),
        },
    )


def send_message(
    socket_path, header, wait=None, timeout=0, payload=None, ignore_errors=False
):
    payload_data = None
    if payload is not None:
        if isinstance(payload, dict):
            payload_data = payload
        elif isinstance(payload, str):
            try:
                payload_data = loads(payload)
            except JSONDecodeError as err:
                raise OSError(
                    'Paramater "payload" must be properly JSON formatted! (%s)'
                    % str(err)
                )
        else:
            raise OSError('Paramater "payload" must be a Python dict or JSON string!')
    try:
        server = socket(AF_UNIX, SOCK_STREAM)
        server.connect(socket_path)
        server.setblocking(1)
    except OSError as err:
        if not ignore_errors:
            raise err
        return None
    else:
        message = Message(header=header)
        if isinstance(payload_data, dict):
            message.update(payload_data)
            del payload_data
        try:
            message.send(server)
            if wait is not None:
                if isinstance(timeout, int) and timeout > 0:
                    server.settimeout(timeout)
                if (isinstance(wait, list) or isinstance(wait, tuple)) and len(
                    wait
                ) >= 2:
                    wait_header = str(wait[0])
                    wait_keyword = str(wait[1])
                else:
                    wait_header = str(wait)
                    wait_keyword = None
                try:
                    while True:
                        try:
                            response = Message(stream=server)
                            if response.header() == wait_header:
                                if wait_keyword is None:
                                    return response
                                elif wait_keyword in response:
                                    return response
                            server.setblocking(1)
                        except BlockingIOError:
                            pass
                except (KeyboardInterrupt, socket_timeout) as err:
                    raise err
                finally:
                    del wait_header
                    del wait_keyword
            return None
        except OSError as err:
            if not ignore_errors:
                raise err
            return None
        finally:
            del message
    finally:
        server.close()
    return None


class Message(Storage):
    def __init__(self, header=None, payload=None, stream=None):
        if not isinstance(stream, socket) and (
            not isinstance(header, str) or len(header) == 0
        ):
            raise OSError('Paramater "header" must be a non-empty Python str!')
        self._header = header
        self._multicast = False
        if payload is not None and not isinstance(payload, dict):
            raise OSError('Paramater "payload" must be a Python dict!')
        elif isinstance(payload, dict):
            self.update(payload)
        if isinstance(stream, socket):
            self.recv(stream)

    def header(self):
        return self._header

    def __str__(self):
        return "%s: %s" % (self._header, super().__str__())

    def multicast(self):
        return self._multicast

    def get_header(self):
        return self._header

    def recv(self, stream):
        if not isinstance(stream, socket):
            raise OSError('Parameter "stream" must be a Python socket!')
        size_bytes = stream.recv(SOCKET_MESSAGE_INTEGER_SIZE)
        if not isinstance(size_bytes, bytes) or len(size_bytes) == 0:
            raise OSError(1000, None)
        if (
            not isinstance(size_bytes, bytes)
            or len(size_bytes) != SOCKET_MESSAGE_INTEGER_SIZE
        ):
            raise OSError(
                "Attempting to read a Message returned an incorrect header length!"
            )
        header_size = unpack_from("I", size_bytes)[0]
        if not isinstance(header_size, int) or header_size <= 0:
            raise OSError(
                "Attempting to read a Message returned an incorrect header length!"
            )
        header_bytes = stream.recv(header_size)
        if not isinstance(header_bytes, bytes) or len(header_bytes) != header_size:
            raise OSError(
                'Attempting to read a Message returned an incorrect header "%s"!'
                % str(header_bytes)
            )
        try:
            self._header = header_bytes.decode("UTF-8")
        except UnicodeDecodeError as err:
            raise OSError(
                'Attempting to read a Message returned an incorrect encoded header "%s"! (%s)'
                % (str(header_bytes), str(err))
            )
        finally:
            del header_size
            del header_bytes
        size_bytes = stream.recv(SOCKET_MESSAGE_INTEGER_SIZE)
        if (
            not isinstance(size_bytes, bytes)
            or len(size_bytes) != SOCKET_MESSAGE_INTEGER_SIZE
        ):
            raise OSError(
                "Attempting to read a Message returned an incorrect payload length!"
            )
        payload_size = unpack_from("I", size_bytes)[0]
        if not isinstance(payload_size, int) or payload_size < 0:
            raise OSError(
                "Attempting to read a Message returned an incorrect payload length!"
            )
        if payload_size > 0:
            payload_bytes = stream.recv(payload_size)
            if (
                not isinstance(payload_bytes, bytes)
                or len(payload_bytes) != payload_size
            ):
                raise OSError(
                    "Attempting to read a Message returned an incorrect payload!"
                )
            try:
                payload = loads(payload_bytes.decode("UTF-8"))
                if isinstance(payload, dict):
                    self.update(payload)
                else:
                    raise OSError(
                        "Attempting to read a Message payload returned a non-dict object!"
                    )
                del payload
            except (UnicodeDecodeError, JSONDecodeError) as err:
                raise OSError(
                    "Attempting to read a Message payload raised an exception! (%s)"
                    % str(err)
                )
            del payload_bytes
        del size_bytes
        del payload_size
        stream.setblocking(0)

    def send(self, stream):
        if not isinstance(self._header, str) or len(self._header) == 0:
            raise OSError("Message is missing a proper header!")
        if not isinstance(stream, socket):
            raise OSError('Parameter "stream" must be a Python socket!')
        stream.sendall(pack("I", len(self._header)))
        try:
            stream.sendall(self._header.encode("UTF-8"))
        except UnicodeEncodeError as err:
            raise OSError(
                "Received an exception attempting to encode Message header! (%s)"
                % str(err)
            )
        if super().__len__() > 0:
            try:
                payload = dumps(self)
                stream.sendall(pack("I", len(payload)))
                stream.sendall(payload.encode("UTF-8"))
                del payload
            except (UnicodeEncodeError, JSONDecodeError) as err:
                raise OSError(
                    "Received an exception attempting to encode Message payload! (%s)"
                    % str(err)
                )
        else:
            stream.sendall(pack("I", 0))

    def is_multicast(self):
        return self._multicast

    def set_header(self, header):
        self._header = header

    def set_multicast(self, multicast):
        self._multicast = multicast
        return self
