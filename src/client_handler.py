# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


class ClientHandler(handler.Handler):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'
    addr_info_len = 6
    server_protocol_map = {'udp': b'\x00'}

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_response': 'handle_peer',
        'swarm_peer_request': 'swarm_peer_response',
        'sstn_list_request': 'sstn_list',
        'sstn_list': 'save_sstn_list',
    }

    def do_swarm_peer_request(self, connection):
        logger.info('')
        connection.send(connection.get_fingerprint() + self.crypt_tools.get_fingerprint())

    def __do_sstn_list_request(self, connection):
        connection.send(self.crypt_tools.get_fingerprint() + connection.get_fingerprint())

    def define_sstn_list_request(self, connection):
        if self.crypt_tools.get_fingerprint() != self.__unpack_sstn_list_request(connection)['my_fingerprint']:
            return False
        if self.__check_sstn_list_request_len(connection):
            return False
        return True

    def __check_sstn_list_request_len(self, connection):
        control_length = len(connection.get_request()) - self.crypt_tools.fingerprint_length
        return control_length % self.__get_sstn_pack_data_length()

    def do_sstn_list(self, connection):
        self.__save_fingerprint_from_sstn_list_request(connection)
        servers = self.__make_sstn_list()
        message = connection.get_fingerprint() + self.__pack_sstn_list(servers)
        sign_message = self.__sign_message(message)
        connection.send(sign_message)

    def __make_sstn_list(self):
        return Peers().get_servers_list()

    def __pack_sstn_list(self, servers):
        message = b''
        for server in servers:
            connection = Connection(
                remote_host=server['host'],
                remote_port=server['port'])
            message += server['fingerprint']
            message += self.server_protocol_map[server['protocol']]
            message += connection.dump_addr()
        return message

    def __get_sstn_pack_data_length(self):
        return addr_info_len + self.crypt_tools.fingerprint_length + __get_server_protocol_map_length()

    def __save_fingerprint_from_sstn_list_request(self, connection):
        neighbour_fingerprint = self.__unpack_sstn_list_request(connection)['neighbour_fingerprint']
        connection.set_fingerprint(neighbour_fingerprint)

    def define_sstn_list(self, connection):
        if self.__check_my_fingerprint(connection) is False:
            return False
        if self.__check_sstn_list_len(connection) is False:
            return False
        if self.__check_message_sign(connection.get_request()) is False:
            return False
        print('define_sstn_list', self.__check_my_fingerprint(connection), self.__check_sstn_list_len(connection), self.__check_message_sign(connection.get_request()))
        return True

    def do_save_sstn_list(self, connection):
        servers = self.__unpack_sstn_list(connection)
        Peers().put_servers_list(servers)

    def __unpack_sstn_list_request(self, connection):
        response = connection.get_request()
        neighbour_fingerprint, my_fingerprint = unpack_stream(response, self.crypt_tools.fingerprint_length)
        return {'neighbour_fingerprint': neighbour_fingerprint,
                'my_fingerprint': my_fingerprint}

    def define_swarm_peer_response(self, connection):
        if self.__check_my_fingerprint(connection) is False:
            return False
        if self.__check_connect_flag(connection) is False:
            return False
        if self.__check_swarm_peer_response_len(connection) is False:
            return False
        if self.__check_connection_fingerprint(connection) is False:
            return False
        if self.__check_message_sign(connection.get_request()) is False:
            return False
        return True

    def do_handle_peer(self, connection):
        connect_flag = self.__get_connect_flag(connection)
        if connect_flag == self.disconnect_flag():
            Peers().save_server_last_response_time(connection)
            connection.shutdown()
        neighbour_fingerprint = self.__unpack_swarm_peer(connection)['neighbour_fingerprint']
        neighbour_ip = self.__unpack_swarm_peer(connection)['neighbour_ip']
        neighbour_port = self.__unpack_swarm_peer(connection)['neighbour_port']
        self.__try_connect_to_neighbour(neighbour_fingerprint, neighbour_ip, neighbour_port)
        self.__init_user_client()

    def __try_connect_to_neighbour(self, neighbour_fingerprint, neighbour_ip, neighbour_port):
        connection = self.make_connection(remote_host=neighbour_ip, remote_port=neighbour_port)
        connection.set_fingerprint(neighbour_fingerprint)
        connection.set_type('client')

        for _ in range(settings.attempt_connect):
            self.__do_sstn_list_request(connection)
            if not self.__check_connection_has_received(connection):
                continue
            self.init(connection)
        self.__set_swarm_connection_status()

    def __unpack_sstn_list(self, connection):
        message = connection.get_request()
        my_figerprint, rest = unpack_stream(message, self.crypt_tools.fingerprint_length)
        servers_pack_data = rest[:-(self.crypt_tools.sign_length+self.crypt_tools.pub_key_length)]
        server_data = []
        while servers_pack_data:
            server_pack_data, servers_pack_data = unpack_stream(servers_pack_data, self.__get_server_pack_data_len())
            server_fingerprint, rest = unpack_stream(server_pack_data, self.crypt_tools.fingerprint_length)
            server_addr, server_protocol = unpack_stream(rest, self.addr_info_len)
            server_ip, server_port = Connection.loads_addr(server_addr)
            server_protocol = {v: k for k, v in self.server_protocol_map.items()}[server_protocol]
            server_data.append({
                'protocol': server_protocol,
                'type': 'server',
                'fingerprint': server_fingerprint,
                'host': server_ip,
                'port': server_port})
        return server_data

        def __unpack_swarm_peer(self, connection):
            message = connection.get_request()
            my_figerprint, rest = unpack_stream(message, self.crypt_tools.fingerprint_length)
            neighbour_fingerprint, rest = unpack_stream(rest, self.crypt_tools.fingerprint_length)
            addr, rest = unpack_stream(rest, self.addr_info_len)
            connect_flag, rest = unpack_stream(rest, len(self.disconnect_flag))
            sign, neighbour_pub_key = unpack_stream(rest, self.crypt_tools.sign_length)
            ip, port = Connection.loads_addr(addr)
            return {'my_figerprint': my_figerprint,
                    'neighbour_fingerprint': neighbour_fingerprint,
                    'neighbour_ip': ip,
                    'neighbour_port': port,
                    'connect_flag': connect_flag,
                    'sign': sign,
                    'responding_pub_key': neighbour_pub_key}

    def __check_sstn_list_len(self, connection):
        message_len = len(connection.get_request())
        message_len -= self.crypt_tools.fingerprint_length
        message_len -= self.crypt_tools.sign_length
        message_len -= self.crypt_tools.pub_key_length
        return message_len % self.__get_server_pack_data_len() == 0

    def __get_server_pack_data_len(self):
        return self.crypt_tools.fingerprint_length + self.addr_info_len + self.__get_server_protocol_map_length()

    def __get_server_protocol_map_length(self):
        return len(next(iter(self.server_protocol_map.values())))

    def __check_connection_has_received(self, connection):
        return not connection.last_request_is_time_out() is None

    def __check_my_fingerprint(self, connection):
        return self.__unpack_my_fingerprint(connection) == self.crypt_tools.get_fingerprint()

    def __get_connect_flag(self, connection):
        return self.__unpack_swarm_peer(connection)['connect_flag']

    def __check_connect_flag(self, connection):
        if self.__get_connect_flag(connection) in [self.disconnect_flag, self.keep_connection_flag]:
            return True
        return False

    def __check_connection_fingerprint(self, connection):
        responding_pub_key = self.__unpack_swarm_peer(connection)['responding_pub_key']
        responding_fingerprint = self.crypt_tools.make_fingerprint(responding_pub_key)
        reference_fingerprint = connection.get_fingerprint()
        return responding_fingerprint == reference_fingerprint

    def __check_message_sign(self, message):
        return self.crypt_tools.check_signature(message)

    def __sign_message(self, message):
        return self.crypt_tools.sign_message(message)

    def __check_swarm_peer_response_len(self, connection):
        request_len = len(connection.get_request())
        required_len = self.crypt_tools.fingerprint_length * 2 + \
                       len(self.addr_info_len) + \
                       len(self.keep_connection_flag) + \
                       self.crypt_tools.sign_length + \
                       self.crypt_tools.pub_key_length
        return request_len == required_len

    def __unpack_my_fingerprint(self, connection):
        message = connection.get_request()
        return message[: self.crypt_tools.fingerprint_length]
