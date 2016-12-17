# -*- coding: utf-8 -*-
#
#   This file is part of PyPIContents.
#   Copyright (C) 2016, PyPIContents Developers.
#
#   Please refer to AUTHORS.rst for a complete list of Copyright holders.
#
#   PyPIContents is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyPIContents is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see http://www.gnu.org/licenses.
"""
``pypicontents.cli`` is a module for handling the command line interface.

This module handles the commands for using PyPIContents. It also parses
parameters, show help, version and controls the logging level.
"""
from __future__ import absolute_import, print_function

from argparse import ArgumentParser

from . import __version__, __description__
from .core.logger import logger
from .api.pypi import main as pypi
from .api.stdlib import main as stdlib
from .api.merge import main as merge
from .api.errors import main as errors
from .api.stats import main as stats


def commandline(argv=None):
    """
    Configure ``ArgumentParser`` to accept custom arguments and commands.

    :param argv: a list of commandline arguments like ``sys.argv``.
                 For example::

                    ['-v', '--loglevel', 'INFO']

    :return: a ``Namespace`` object.

    .. versionadded:: 0.1.0
    """
    assert isinstance(argv, (list, type(None)))

    parser = ArgumentParser(description=__description__)
    parser.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {:s}'.format(__version__),
        help='Print version and exit.')
    subparsers = parser.add_subparsers(title='commands')

    # pypi command
    pypi_parser = subparsers.add_parser('pypi')
    pypi_parser.set_defaults(command=pypi)
    pypi_parser.add_argument(
        '-l', '--loglevel', default='INFO', metavar='<level>',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help=('Logger verbosity level (default: INFO). Must be one of: '
              'DEBUG, INFO, WARNING, ERROR or CRITICAL.'))
    pypi_parser.add_argument(
        '-f', '--logfile', metavar='<path>',
        help='A path pointing to a file to be used to store logs.')
    pypi_parser.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'JSON Module Index.'))
    pypi_parser.add_argument(
        '-R', '--letter-range', default='0-z', metavar='<letter/number>',
        help=('An expression representing an alphanumeric range to be used to '
              'filter packages from PyPI. You can use a single alphanumeric '
              'character like "0" to process only packages beginning with '
              '"0". You can use commas use as a list o dashes to use as an '
              'interval.'))
    pypi_parser.add_argument(
        '-L', '--limit-log-size', default='3M', metavar='<size>',
        help='Stop processing if log size exceeds <size>.')
    pypi_parser.add_argument(
        '-M', '--limit-mem', default='2G', metavar='<size>',
        help='Stop processing if process memory exceeds <size>.')
    pypi_parser.add_argument(
        '-T', '--limit-time', default='2100', metavar='<sec>',
        help='Stop processing if process time exceeds <sec>.')

    # stdlib command
    stdlib_parser = subparsers.add_parser('stdlib')
    stdlib_parser.set_defaults(command=stdlib)
    stdlib_parser.add_argument(
        '-o', '--outputfile', required=True, metavar='',
        help='')
    stdlib_parser.add_argument(
        '-p', '--pyver', default='2.7',
        help='')

    # merge command
    merge_parser = subparsers.add_parser('merge')
    merge_parser.set_defaults(command=merge)
    merge_parser.add_argument(
        '-i', '--inputdir', required=True, metavar='',
        help='')
    merge_parser.add_argument(
        '-o', '--outputfile', required=True, metavar='',
        help='')

    # errors command
    errors_parser = subparsers.add_parser('errors')
    errors_parser.set_defaults(command=errors)
    errors_parser.add_argument(
        '-i', '--inputdir', required=True, metavar='',
        help='')
    errors_parser.add_argument(
        '-o', '--outputfile', required=True, metavar='',
        help='')

    # stats command
    stats_parser = subparsers.add_parser('stats')
    stats_parser.set_defaults(command=stats)
    stats_parser.add_argument(
        '-i', '--inputdir', required=True, metavar='',
        help='')
    stats_parser.add_argument(
        '-o', '--outputfile', required=True, metavar='',
        help='')

    return parser.parse_args(argv)


def main(argv=None):
    """
    Handle arguments and commands.

    :param argv: a list of commandline arguments like ``sys.argv``.
                 For example::

                    ['-v', '--loglevel', 'INFO']

    :return: an exit status.

    .. versionadded:: 0.1.0
    """
    assert isinstance(argv, (list, type(None)))

    args = commandline(argv)

    logger.start(args.logfile)
    logger.loglevel(args.loglevel)
    logger.info('Starting execution.')
    logger.debug('Processed arguments: {:s}'.format(vars(args)))

    try:
        status = args.command(**vars(args))
    except KeyboardInterrupt:
        logger.critical('Execution interrupted by user!')
        status = 1
    except Exception as e:
        logger.exception(e)
        logger.critical('Shutting down due to fatal error!')
        status = 1
    else:
        logger.info('Ending execution.')

    logger.stop()
    return status


if __name__ == '__main__':
    import re
    import sys
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
