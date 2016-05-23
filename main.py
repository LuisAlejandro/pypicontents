#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pypicontents.process import process

if __name__ == '__main__':
    try:
        process(os.environ.get('PYPICONTENTSRANGE'))
    except KeyboardInterrupt:
        sys.exit('Execution interrupted by user.')
