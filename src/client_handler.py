# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
import settings


class ClientHandler(Handler):
    def verify_len_swarm_peer_request(self, **kwargs):
        request_length = len(self.connection.get_request())
        required_length = self.parser.calc_requared_length(kwargs['package_protocol'])
        return required_length == request_length

    def verify_protocol_version(self, **kwargs):
        request_major_version_marker = self.parser.get_part('major_version_marker', kwargs['package_protocol'])
        request_minor_version_marker = self.parser.get_part('minor_version_marker', kwargs['package_protocol'])
        my_major_version_marker, my_minor_version_marker = self.protocol['client_protocol_version']
        return my_major_version_marker >= request_major_version_marker \
               and my_minor_version_marker >= request_minor_version_marker

    def verify_len_swarm_peer(self, **kwargs):
        # FIXME
        return False

    def verify_len_sstn_request(self, **kwargs):
        # FIXME
        return False

    def verify_len_sstn_list(self, **kwargs):
        # FIXME
        return False

    def verify_package_id_marker(self, **kwargs):
        package_protocol = kwargs['package_protocol']
        request_id_marker = self.parser.get_part('package_id_marker')
        required_id_marker = package_protocol['package_id_marker']
        return request_id_marker == required_id_marker

    def verify_timestamp(self, **kwargs):
        timestamp = self.parser.get_part('timestamp')
        return time() - settings.peer_ping_time_seconds < timestamp < time() + settings.peer_ping_time_seconds

    def verify_receiver_fingerprint(self, **kwargs):
        my_fingerprint_from_request = self.parser.get_part('receiver_fingerprint')
        my_fingerprint_reference = self.crypt_tools.get_fingerprint()
        return my_fingerprint_from_request == my_fingerprint_reference

    def swarm_peer_request(self, **kwargs):
        return self.make_message(
            package_name='swarm_peer_request',
            receiver_connection=kwargs['receiver_connection'])

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
        return self.protocol['packages'][kwargs['package_name']]['package_id_marker']

    def get_receiver_fingerprint(self, **kwargs):
        return kwargs['receiver_connection'].get_fingerprint()

    def get_timestamp(self, **kwargs):
        return self.parser.pack_timestemp()

    def get_requester_open_key(self, **kwargs):
        # I am requester
        return self.crypt_tools.get_open_key()
