# -*- coding: utf-8 -*-
#
#   This file is part of PyPIContents.
#   Copyright (C) 2016-2017, PyPIContents Developers.
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

import os
from argparse import ArgumentParser

from . import __version__, __description__
from .core.logger import logger
from .core.utils import create_file_if_notfound
from .api.pypi import pypi
from .api.stdlib import stdlib
from .api.merge import merge
from .api.errors import errors
from .api.stats import stats


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

    parser = ArgumentParser(
        prog='pypicontents', description=__description__, add_help=False,
        usage='\t%(prog)s [options]\n\t%(prog)s <command> [options]')
    gen_options = parser.add_argument_group('General Options')
    gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    subparsers = parser.add_subparsers(title='Commands', metavar='')

    # pypi command
    pypi_parser = subparsers.add_parser(
        'pypi', prog='pypicontents', usage='%(prog)s pypi [options]',
        help='Generate a JSON Module Index from PyPI.', add_help=False)
    pypi_parser.set_defaults(command=pypi)
    pypi_gen_options = pypi_parser.add_argument_group('General Options')
    pypi_gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    pypi_gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    pypi_options = pypi_parser.add_argument_group('Pypi Options')
    pypi_options.add_argument(
        '-l', '--loglevel', default='INFO', metavar='<level>',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help=('Logger verbosity level (default: INFO). Must be one of: '
              'DEBUG, INFO, WARNING, ERROR or CRITICAL.'))
    pypi_options.add_argument(
        '-f', '--logfile', metavar='<path>',
        help='A path pointing to a file to be used to store logs.')
    pypi_options.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'JSON Module Index (required).'))
    pypi_options.add_argument(
        '-e', '--extractdir', default='/tmp/pypic-extract', metavar='<path>',
        help=('A path pointing to a directory that will be used to store the '
              'extracted python packages.'))
    pypi_options.add_argument(
        '-c', '--cachedir', default='/tmp/pypic-cache', metavar='<path>',
        help=('A path pointing to a directory that will be used to store '
              'downloaded python tarballs.'))
    pypi_options.add_argument(
        '-R', '--letter-range', default='0-z', metavar='<letter/number>',
        help=('An expression representing an alphanumeric range to be used to '
              'filter packages from PyPI (default: 0-z). You can use a single '
              'alphanumeric character like "0" to process only packages '
              'beginning with "0". You can use commas use as a list o dashes '
              'to use as an interval.'))
    pypi_options.add_argument(
        '-L', '--limit-log-size', default='3M', metavar='<size>',
        help='Stop processing if log size exceeds <size> (default: 3M).')
    pypi_options.add_argument(
        '-M', '--limit-mem', default='2G', metavar='<size>',
        help='Stop processing if process memory exceeds <size> (default: 2G).')
    pypi_options.add_argument(
        '-T', '--limit-time', default='2100', metavar='<sec>',
        help='Stop processing if process time exceeds <sec> (default: 2100).')
    pypi_options.add_argument(
        '-C', '--clean', action='store_true',
        help='Clean downloaded files after extracting information.')

    # stdlib command
    stdlib_parser = subparsers.add_parser(
        'stdlib', prog='pypicontents', usage='%(prog)s stdlib [options]',
        help=('Generate a JSON Module Index based on the Python '
              'Standard Library.'), add_help=False)
    stdlib_parser.set_defaults(command=stdlib)
    stdlib_gen_options = stdlib_parser.add_argument_group('General Options')
    stdlib_gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    stdlib_gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    stdlib_options = stdlib_parser.add_argument_group('Stdlib Options')
    stdlib_options.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'JSON Module Index (required).'))

    # merge command
    merge_parser = subparsers.add_parser(
        'merge', prog='pypicontents', usage='%(prog)s merge [options]',
        help='Merge JSON files generated by pypi or stdlib commands.',
        add_help=False)
    merge_parser.set_defaults(command=merge)
    merge_gen_options = merge_parser.add_argument_group('General Options')
    merge_gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    merge_gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    merge_options = merge_parser.add_argument_group('Merge Options')
    merge_options.add_argument(
        '-i', '--inputdir', required=True, metavar='<path>',
        help=('A path pointing to a directory containing JSON files generated '
              'by pypi or stdlib commands (required).'))
    merge_options.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'merged JSON files (required).'))

    # errors command
    errors_parser = subparsers.add_parser(
        'errors', prog='pypicontents', usage='%(prog)s errors [options]',
        help='Extract errors from log files generated by the pypi command.',
        add_help=False)
    errors_parser.set_defaults(command=errors)
    errors_gen_options = errors_parser.add_argument_group('General Options')
    errors_gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    errors_gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    errors_options = errors_parser.add_argument_group('Errors Options')
    errors_options.add_argument(
        '-i', '--inputdir', required=True, metavar='<path>',
        help=('A path pointing to a directory containing log files generated '
              'by the pypi command (required).'))
    errors_options.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'errors (required).'))

    # stats command
    stats_parser = subparsers.add_parser(
        'stats', prog='pypicontents', usage='%(prog)s stats [options]',
        help=('Extract statistics from log files generated by the '
              'pypi command.'), add_help=False)
    stats_parser.set_defaults(command=stats)
    stats_gen_options = stats_parser.add_argument_group('General Options')
    stats_gen_options.add_argument(
        '-V', '--version', action='version',
        version='pypicontents {0}'.format(__version__),
        help='Print version and exit.')
    stats_gen_options.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit.')
    stats_options = stats_parser.add_argument_group('Stats Options')
    stats_options.add_argument(
        '-i', '--inputdir', required=True, metavar='<path>',
        help=('A path pointing to a directory containing JSON files generated '
              'by the pypi command (required).'))
    stats_options.add_argument(
        '-o', '--outputfile', required=True, metavar='<path>',
        help=('A path pointing to a file that will be used to store the '
              'statistics (required).'))

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

    if args.command.__name__ == 'pypi':
        if args.logfile and not os.path.isfile(args.logfile):
            create_file_if_notfound(args.logfile)
    else:
        args.logfile = None
        args.loglevel = 'INFO'

    logger.start(args.logfile)
    logger.loglevel(args.loglevel)
    logger.info('Starting execution.')

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
