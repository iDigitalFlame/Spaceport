#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Utils Python file is used to help assist with simple repeatable functions that
# may be used across the System Management Daemon. Functions here are basic functions
# for file writing, reading and other simple operations.

from hashlib import md5
from sys import stderr, exit
from os import remove, makedirs
from traceback import format_exc
from os.path import isfile, dirname, exists
from json import loads, dumps, JSONDecodeError
from subprocess import (
    Popen,
    DEVNULL,
    SubprocessError,
    PIPE,
    check_call,
    CalledProcessError,
)


def boolean(bool_value):
    if isinstance(bool_value, str):
        value = bool_value.lower().strip()
        return value == "1" or value == "true" or value == "on"
    if isinstance(bool_value, bool):
        return bool_value
    if isinstance(bool_value, int):
        return bool_value == 1
    return False


def stop(process_object):
    if not isinstance(process_object, Popen):
        return
    try:
        process_object.terminate()
    except (OSError, SubprocessError):
        pass
    try:
        process_object.kill()
    except (OSError, SubprocessError):
        pass


def remove_file(file_path):
    if not isinstance(file_path, str) or not isfile(file_path):
        return
    try:
        remove(file_path)
    except OSError:
        pass


def print_error(message, error, quit=True):
    print(message, file=stderr)
    if error is not None:
        print(format_exc(limit=3), file=stderr)
    if quit:
        exit(1)


def read_json(file_path, ignore_errors=True):
    data = read(file_path, ignore_errors, False)
    if not isinstance(data, str):
        if not ignore_errors:
            raise OSError('Reading file "%s" did not return string data!' % file_path)
    if len(data) == 0:
        return None
    try:
        json_data = loads(data)
    except JSONDecodeError as err:
        if not ignore_errors:
            raise OSError(err)
        return None
    else:
        return json_data
    finally:
        del data
    return None


def read(file_path, ignore_errors=True, binary=False):
    if not isinstance(file_path, str):
        if not ignore_errors:
            raise OSError('Parameter "file_path" must be a Python str!')
        return None
    if not isfile(file_path):
        if not ignore_errors:
            raise OSError('The path "%s" is not a file!' % file_path)
        return None
    try:
        handle = open(file_path, "rb" if binary else "r")
    except OSError as err:
        if not ignore_errors:
            raise err
        return None
    else:
        try:
            data = handle.read()
        except OSError as err:
            if not ignore_errors:
                raise err
            return None
        else:
            return data
        finally:
            handle.close()
            del handle
    return None


def hash_file(file_path, block=4096, ignore_errors=True):
    if not isinstance(file_path, str):
        if not ignore_errors:
            raise OSError('Parameter "file_path" must be a Python str!')
        return None
    if not isfile(file_path):
        if not ignore_errors:
            raise OSError('The path "%s" is not a file!' % file_path)
        return None
    generator = md5()
    try:
        with open(file_path, "rb") as handle:
            while True:
                buffer = handle.read(block)
                if not buffer:
                    break
                generator.update(buffer)
    except OSError as err:
        if not ignore_errors:
            raise err
        return None
    else:
        return generator.hexdigest()
    return None


def run(command, shell=False, wait=None, ignore_errors=True):
    if shell:
        if isinstance(command, list):
            process = " ".join(command)
        else:
            process = command
    else:
        if not isinstance(command, list):
            if not isinstance(command, str):
                process = str(command).split(" ")
            else:
                process = command.split(" ")
        else:
            process = command
    if (
        isinstance(wait, int)
        or isinstance(wait, float)
        or (isinstance(wait, bool) and wait)
    ):
        try:
            proc = Popen(process, shell=shell, stdout=PIPE, stderr=PIPE)
        except (OSError, SubprocessError, ValueError) as err:
            if not ignore_errors:
                if isinstance(err, OSError):
                    raise err
                raise OSError(err)
            return None
        else:
            try:
                proc.wait(None if isinstance(wait, bool) else wait)
            except (OSError, SubprocessError) as err:
                if not ignore_errors:
                    if isinstance(err, OSError):
                        raise err
                    raise OSError(err)
                return None
            else:
                output = []
                bytes_stdout = proc.stdout.read()
                bytes_stderr = proc.stderr.read()
                try:
                    if isinstance(bytes_stdout, bytes) and len(bytes_stdout) > 0:
                        if bytes_stdout[len(bytes_stdout) - 1] == 10:
                            bytes_stdout = bytes_stdout[: len(bytes_stdout) - 1]
                        output.append(bytes_stdout.decode("UTF-8"))
                    if isinstance(bytes_stderr, bytes) and len(bytes_stderr) > 0:
                        if bytes_stderr[len(bytes_stderr) - 1] == 10:
                            bytes_stderr = bytes_stderr[: len(bytes_stderr) - 1]
                        output.append(bytes_stderr.decode("UTF-8"))
                except UnicodeDecodeError as err:
                    if not ignore_errors:
                        raise OSError(err)
                    return None
                else:
                    return "".join(output)
            finally:
                stop(proc)
                del proc
                del output
        finally:
            del process
        return None
    try:
        check_call(process, shell=shell, stdout=DEVNULL, stderr=DEVNULL)
    except CalledProcessError as err:
        if not ignore_errors:
            raise OSError(err)
        return False
    except (OSError, SubprocessError, ValueError) as err:
        if not ignore_errors:
            if isinstance(err, OSError):
                raise err
            raise OSError(err)
        return False
    finally:
        del process
    return True


def write(file_path, data, ignore_errors=True, binary=False, append=False):
    if not isinstance(file_path, str):
        if not ignore_errors:
            raise OSError('Parameter "file_path" must be a Python str!')
        return False
    file_dir = dirname(file_path)
    if not exists(file_dir):
        try:
            makedirs(file_dir, exist_ok=True)
        except OSError as err:
            if not ignore_errors:
                raise err
            return False
    del file_dir
    try:
        handle = open(
            file_path,
            ("ab" if binary else "a") if append else ("wb" if binary else "w"),
        )
    except OSError as err:
        if not ignore_errors:
            raise err
        return False
    else:
        try:
            if data is None:
                handle.write(bytes() if binary else str())
            if isinstance(data, str):
                if binary:
                    handle.write(data.encode("UTF-8"))
                else:
                    handle.write(data)
            else:
                data_string = str(data)
                if binary:
                    handle.write(data_string.encode("UTF-8"))
                else:
                    handle.write(data_string)
                del data_string
            handle.flush()
            return True
        except (OSError, UnicodeEncodeError) as err:
            if not ignore_errors:
                raise err
            return False
        finally:
            handle.close()
            del handle
    return False


def write_json(file_path, obj, indent=0, sort=False, ignore_errors=True):
    if obj is None:
        if not ignore_errors:
            raise OSError('Paramater "obj" cannot be None!')
        return False
    try:
        data = dumps(obj, indent=indent, sort_keys=sort)
    except (TypeError, JSONDecodeError, OverflowError) as err:
        if not ignore_errors:
            raise OSError(err)
        return False
    else:
        try:
            return write(file_path, data, ignore_errors, False)
        except OSError as err:
            if not ignore_errors:
                raise err
            return False
        del data
    return False
