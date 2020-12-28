# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


from settings import logger
import settings
import host
import protocol
import crypt_tools


def server_run():
    logger.info('server start')
    server_handler = protocol.Handler(protocol.server, crypt_tools=crypt_tools.Tools())
    server = host.UDPHost(handler=server_handler, host='', port=settings.default_port)
    server.listener_start()
    logger.info('server shutdown')


if __name__ == '__main__':
    server_run()
