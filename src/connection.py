# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import settings


class Connection:
    def __init__(self):
        self.live_points = settings.peer_live_points

    def loads(self, connection_data):
        for key, val in connection_data.items():
            setattr(self, key, val)
        return self
