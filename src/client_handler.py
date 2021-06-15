# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
import settings


class ClientHandler(Handler):
    def swarm_peer_request(self, **kwargs):
        return self.make_message(
            package_name='swarm_peer_request',
            server_connection=kwargs['server_connection'])

    def get_markers(self, **kwargs):
        markers = 0
        for marker_name in kwargs['markers']['name']:
            get_marker_value_function = getattr(self, '_get_marker_{}'.format(marker_name))
            marker = get_marker_value_function(**kwargs)
            marker_description = self.protocol['markers'][marker_name]
            markers ^= self.build_marker(marker, marker_description, kwargs['markers'])
        return self.parser.pack_int(markers, kwargs['markers']['length'])

    def build_marker(self, marker, marker_description, part_structure):
        part_structure_length_bits = part_structure['length'] * 8
        left_shift = part_structure_length_bits - marker_description['start_bit'] - marker_description['length']
        return marker << left_shift

    def _get_marker_major_version_marker(self, **kwargs):
        return self.protocol['client_protocol_version'][0]

    def _get_marker_minor_version_marker(self, **kwargs):
        return self.protocol['client_protocol_version'][1]

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol == True

    def _get_marker_package_id_marker(self, **kwargs):
        return self.protocol['package'][kwargs['package_name']]['package_id_marker']

    def get_my_fingerprint(self, **kwargs):
        # return receiver fingerprint
        return kwargs['server_connection'].get_fingerprint()

    def get_timestamp(self, **kwargs):
        return self.parser.pack_timestemp()

    def get_requester_open_key(self, **kwargs):
        # I am requester
        return self.crypt_tools.get_open_key()