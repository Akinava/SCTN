# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import os
import json
import pycrypto
import settings
from settings import logger


class Tools:
    def __init__(self):
        logger.info('crypt_tools init')
        self.init_ecdsa()

    def init_ecdsa(self):
        logger.info('crypt_tools init_ecdsa')
        if self.get_ecdsa_from_file():
            return
        self.generate_new_ecdsa()
        self.save_ecdsa()

    def read_shadow_file(self):
        logger.info('crypt_tools read_shadow_file')
        if not os.path.isfile(settings.shadow_file):
            return None
        with open(settings.shadow_file) as shadow_file:
            try:
                return json.loads(shadow_file.read())
            except json.decoder.JSONDecodeError:
                return None

    def save_shadow_file(self, data):
        logger.info('crypt_tools save_shadow_file')
        with open(settings.shadow_file, 'w') as shadow_file:
            shadow_file.write(json.dumps(data, indent=2))

    def update_shadow_file(self, new_data):
        logger.info('crypt_tools update_shadow_file')
        file_data = {} or self.read_shadow_file()
        if file_data is None:
            file_data = {}
        file_data.update(new_data)
        self.save_shadow_file(file_data)

    def get_ecdsa_from_file(self):
        logger.info('crypt_tools get_ecdsa_from_file')
        shadow_data = self.read_shadow_file()
        if shadow_data is None:
            return False
        ecdsa_priv_key_b58 = shadow_data.get('ecdsa', {}).get('key')
        if ecdsa_priv_key_b58 is None:
            return False
        ecdsa_priv_key = pycrypto.B58().unpack(ecdsa_priv_key_b58)
        self.ecdsa = pycrypto.ECDSA(priv_key=ecdsa_priv_key)
        return True

    def generate_new_ecdsa(self):
        logger.info('crypt_tools generate_new_ecdsa')
        self.ecdsa = pycrypto.ECDSA()

    def save_ecdsa(self):
        logger.info('crypt_tools save_ecdsa')
        ecdsa_priv_key = self.ecdsa.get_priv_key()
        ecdsa_priv_key_b58 = pycrypto.B58().pack(ecdsa_priv_key)
        fingerprint_b58 = pycrypto.B58().pack(self.get_fingerprint())
        self.update_shadow_file(
            {'ecdsa': {
                'key': ecdsa_priv_key_b58,
                'fingerprint': fingerprint_b58}}
        )

    def get_fingerprint(self):
        logger.info('crypt_tools get_fingerprint')
        if not hasattr(self, 'fingerprint'):
            self.make_fingerprint()
        return self.fingerprint

    def make_fingerprint(self):
        open_key = self.ecdsa.get_pub_key()
        self.fingerprint = pycrypto.sha256(open_key)
