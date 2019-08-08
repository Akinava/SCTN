#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import random


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import host


def message():
    msg = 'bla'
    msg *= random.randint(1, 5)
    msg += random.choice(['.', '!', '?'])
    return msg.encode('utf8')


if __name__ == "__main__":
    print('start client test')
    client = host.UDPHost(host='127.0.0.1', port=10002, handler=None)
    client.send(message())
    print('stop client test')

