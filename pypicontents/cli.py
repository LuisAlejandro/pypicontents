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

This modue handles the commands for using PyPIContents. It also parses
parameters, show help, version and controls the logging level.
"""
from __future__ import absolute_import, print_function

from argparse import ArgumentParser

from . import __version__, __description__
from .core.logger import logger
from .api.process import main as process
from .api.stdlib import main as stdlib
from .api.merge_pypi import main as merge_pypi
from .api.merge_stdlib import main as merge_stdlib
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
    process_parser = subparsers.add_parser('process')
    process_parser.set_defaults(command=process)
    process_parser.add_argument(
        '-l', '--loglevel', default='INFO',
        help='')
    process_parser.add_argument(
        '-f', '--logfile', required=True,
        help='')
    process_parser.add_argument(
        '-o', '--outputfile', required=True,
        help='')
    process_parser.add_argument(
        '-R', '--letter-range', default='0-z',
        help='')
    process_parser.add_argument(
        '-L', '--limit-log-size', default='3M',
        help='')
    process_parser.add_argument(
        '-M', '--limit-mem', default='2G',
        help='')
    process_parser.add_argument(
        '-T', '--limit-time', default='2100',
        help='')
    stdlib_parser = subparsers.add_parser('stdlib')
    stdlib_parser.set_defaults(command=stdlib)
    stdlib_parser.add_argument(
        '-o', '--outputfile', required=True,
        help='')
    stdlib_parser.add_argument(
        '-p', '--pyver', default='2.7',
        help='')
    merge_pypi_parser = subparsers.add_parser('merge_pypi')
    merge_pypi_parser.set_defaults(command=merge_pypi)
    merge_pypi_parser.add_argument(
        '-i', '--inputdir', required=True,
        help='')
    merge_pypi_parser.add_argument(
        '-o', '--outputfile', required=True,
        help='')
    merge_stdlib_parser = subparsers.add_parser('merge_stdlib')
    merge_stdlib_parser.set_defaults(command=merge_stdlib)
    merge_stdlib_parser.add_argument(
        '-i', '--inputdir', required=True,
        help='')
    merge_stdlib_parser.add_argument(
        '-o', '--outputfile', required=True,
        help='')
    errors_parser = subparsers.add_parser('errors')
    errors_parser.set_defaults(command=errors)
    errors_parser.add_argument(
        '-i', '--inputdir', required=True,
        help='')
    errors_parser.add_argument(
        '-o', '--outputfile', required=True,
        help='')
    stats_parser = subparsers.add_parser('stats')
    stats_parser.set_defaults(command=stats)
    stats_parser.add_argument(
        '-i', '--inputdir', required=True,
        help='')
    stats_parser.add_argument(
        '-o', '--outputfile', required=True,
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
