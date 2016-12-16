#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import doctest
import unittest

from pypicontents.core.logger import logger


class TestLogger(unittest.TestCase):

    def setUp(self):
        logger.start()

    def test_01_default_level(self):
        pass


def load_tests(loader, tests, pattern):
    tests.addTests(doctest.DocTestSuite('pypicontents.core.logger'))
    return tests


if __name__ == '__main__':
    sys.exit(unittest.main())
