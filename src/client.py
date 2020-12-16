# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


from settings import logger


def client_run():
    logger.info('client start')
    logger.info('client shutdown')


if __name__ == '__main__':
    client_run()