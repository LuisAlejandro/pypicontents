# -*- coding: utf-8 -*-
#
# Please refer to AUTHORS.rst for a complete list of Copyright holders.
# Copyright (C) 2016-2022, PyPIContents Developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
``pypicontents.core.logger`` is the global application logging module.

All modules use the same global logging object. No messages will be emitted
until the logger is started.
"""

import sys
import types
import logging

levelNames = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARN': 30,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
    'NOTSET': 0,
}


class ControlableLogger(logging.Logger):
    """
    This class represents a logger object that can be started and stopped.

    It has a start method which allows you to specify a logging level.
    The stop method halts output.
    """

    def __init__(self, name=None):
        """
        Initialize this ``ControlableLogger``.

        The name defaults to the application name. Loggers with the same name
        refer to the same underlying object. Names are hierarchical, e.g.
        'parent.child' defines a logger that is a descendant of 'parent'.

        :param name: a string containing the logger name.
        :return: a ``ControlableLogger`` instance.

        .. versionadded:: 0.1.0
        """
        # Initializing according to old-style or new-style clases
        if hasattr(types, 'ClassType') and \
           isinstance(logging.Logger, types.ClassType):
            logging.Logger.__init__(self, name)
        if (hasattr(types, 'TypeType') and
           isinstance(logging.Logger, types.TypeType)) or \
           isinstance(logging.Logger, type):
            super(ControlableLogger, self).__init__(name)

        self.parent = logging.root

        #: Attribute ``disabled`` (boolean): Stores the current status of the
        #: logger.
        self.disabled = True
        self.propagate = False

        #: Attribute ``formatstring`` (string): Stores the string that
        #: will be used to format the logger output.
        self.formatstring = '[%(levelname)s] %(message)s'

    def start(self, filename=None):
        """
        Start logging with this logger.

        Until the logger is started, no messages will be emitted. This applies
        to all loggers with the same name and any child loggers.

        .. versionadded:: 0.1.0
        """
        if self.disabled:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(logging.Formatter(self.formatstring))
            self.addHandler(sh)
            if filename:
                fh = logging.FileHandler(filename, mode='w')
                fh.setFormatter(logging.Formatter(self.formatstring))
                self.addHandler(fh)
            self.disabled = False

    def stop(self):
        """
        Stop logging with this logger.

        Remove available handlers and set disabled attribute to ``True``.

        .. versionadded:: 0.1.0
        """
        if not self.disabled:
            for h in list(self.handlers):
                self.removeHandler(h)
            self.disabled = True

    def loglevel(self, level='INFO'):
        """
        Set the log level for this logger.

        Messages less than the given priority level will be ignored. The
        default level is 'INFO', which conforms to the *nix convention that
        a successful run should produce no diagnostic output. Available levels
        and their suggested meanings:

        * ``NOTSET``: all messages are processed.
        * ``DEBUG``: output useful for developers.
        * ``INFO``: trace normal program flow, especially external
                    interactions.
        * ``WARNING``: an abnormal condition was detected that might need
                       attention.
        * ``ERROR``: an error was detected but execution continued.
        * ``CRITICAL``: an error was detected and execution was halted.

        :param level: a string containing the desired logging level.

        .. versionadded:: 0.1.0
        """
        if not self.disabled:
            self.setLevel(levelNames[level])

    def configpkg(self, name=None):

        if name:
            formatstring = '[%(levelname)s] ({0}) %(message)s'.format(name)
            for h in list(self.handlers):
                h.setFormatter(logging.Formatter(formatstring))
                self.removeHandler(h)
                self.addHandler(h)
        else:
            for h in list(self.handlers):
                h.setFormatter(logging.Formatter(self.formatstring))
                self.removeHandler(h)
                self.addHandler(h)


logging.setLoggerClass(ControlableLogger)
logger = logging.getLogger(__name__.split('.')[0])
