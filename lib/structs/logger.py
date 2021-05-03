#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# The Logger class is exactly as it sounds. This can create and mantain a
# logging instance to file and/or stdout.
# Updated 10/2018

from traceback import format_exc
from logging import getLogger, Formatter, StreamHandler, FileHandler


class Logger(object):
    def __init__(self, log_name, log_level="INFO", log_file=None):
        if not isinstance(log_level, str) or len(log_level) == 0:
            raise OSError('Parameter "log_level" must be a non-empty Python str!')
        self._log = getLogger(log_name)
        self._log.setLevel(log_level.upper())
        formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stream = StreamHandler()
        stream.setFormatter(formatter)
        self._log.addHandler(stream)
        del stream
        if isinstance(log_file, str) and len(log_file) > 0:
            try:
                file = FileHandler(log_file)
                file.setFormatter(formatter)
                file.setLevel(log_level.upper())
                self._log.addHandler(file)
            except OSError as err:
                raise OSError(
                    'Failed to create log file "%s"! (%s)' % (log_file, str(err))
                )
            else:
                del file
        del formatter

    def info(self, message, err=None):
        if err is not None:
            self._log.info("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            self._log.debug("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.debug(message)

    def error(self, message, err=None):
        if err is not None:
            self._log.error("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            self._log.warning("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.warning(message)


# EOF
