# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import pycrypto

class Tools:
    def __init__(self):
        self.__get_fingerprint()

    def __get_fingerprint(self):
        if self.__get_fingerprint_from_file():
            return
        self.__generate_new_fingerprin()

    def __get_fingerprint_from_file(self):
        # TODO
        pass

    def __generate_new_fingerprin(self):
        # TODO
        pass


