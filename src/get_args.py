# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from optparse import OptionParser


def parser():
    parser = OptionParser()
    parser.add_option('-p', '--port', dest='default_port', type='int',
                  help='listener port', default=None)
    parser.add_option('-w', '--wallet', dest='shadow_file', metavar='FILE',
                      help='shadow file', default=None)
    parser.add_option('-c', '--connections', dest='peers_file', metavar='FILE',
                      help='peers file', default=None)
    return parser.parse_args()
