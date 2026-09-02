#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The hp-prime-kit command line.

    python hpprime.py <command> [arguments]

On Windows the hpprime.cmd wrapper next to this file lets you drop the
"python": hpprime doctor. On macOS and Linux, ./hpprime does the same.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hpkit.cli import main

if __name__ == '__main__':
    sys.exit(main())
