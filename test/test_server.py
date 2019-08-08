#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import host


class Handler:
    pass


if __name__ == "__main__":
    print('start test')
    server = host.UDPHost(host='', port=10002, handler=Handler)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    print('end test')
