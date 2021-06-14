# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler


class ClientHandler(Handler):
    def swarm_peer_request(self, **kwargs):
        return self.make_message(
            package_name='swarm_peer_request',
            server_connection=kwargs['server_connection'])
