# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import json
import sys
import random
import struct
from datetime import datetime, timedelta
import logging
import settings
import get_args
from cryptotool import *


DATA_FORMAT = '%Y.%m.%d %H:%M:%S'


class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class Peers(Singleton):
    def __init__(self):
        self.__load()

    def get_random_server_from_file(self):
        servers = self.__filter_peers_by_type('server')
        if not servers:
            return None
        return random.choice(servers)

    def save_server_last_response_time(self, connection):
        server = self.__find_peer({
            'type': 'server',
            'fingerprint': connection.get_fingerprint(),
            'host': connection.get_remote_host(),
            'port': connection.get_remote_port()})
        if isinstance(server, dict):
            server['last_response'] = now()
            self.__save()

    def __find_peer(self, filter_kwargs):
        for peer in self.__peers:
            for key, val in filter_kwargs.items():
                if peer.get(key) != val:
                    continue
            return peer

    def get_servers_list(self):
        servers = self.__filter_peers_by_type('server')
        if not servers:
            return None
        servers = self.__filter_peers_by_last_response_field(servers=servers, days_delta=settings.servers_timeout_days)
        return servers[settings.peer_connections]

    def put_servers_list(self, servers_list):
        for server_data in servers_list:
            server = self.__find_peer({
                'protocol': server_data['protocol'],
                'type': 'server',
                'fingerprint': server_data['fingerprint'],
                'host': server_data['host'],
                'port': server_data['port']})
            if server is None:
                self.__peers.append(server_data)
        self.__save()

    def __filter_peers_by_last_response_field(self, servers, days_delta):
        filtered_list = []
        for peer in servers:
            datatime_string = peer.get('last_response')
            if datatime_string is None:
                continue
            if str_to_datetime(datatime_string) + timedelta(days=days_delta) < now():
                continue
            filtered_list.append(peer)
        return filtered_list

    def __load(self):
        peers = self.__read_file()
        self.__peers = self.__unpack_peers_fingerprint(peers)

    def __save(self):
        peers = self.__pack_peers_fingerprint(self.__peers)
        self.__save_file(peers)

    def __read_file(self):
        with open(settings.peers_file, 'r') as f:
            peers_list = json.loads(f.read())
        return peers_list

    def __save_file(self, data):
        with open(settings.peers_file, 'w') as f:
            f.write(json.dumps(data))

    def __unpack_peers_fingerprint(self, peers_list):
        for peer_index in range(len(peers_list)):
            peer = peers_list[peer_index]
            peer['fingerprint'] = B58().unpack(peer['fingerprint'])
        return peers_list

    def __pack_peers_fingerprint(self, peers_list):
        for peer_index in range(len(peers_list)):
            peer = peers_list[peer_index]
            peer['fingerprint'] = B58().pack(peer['fingerprint'])
        return peers_list

    def __filter_peers_by_type(self, filter):
        filtered_peers = []
        for peer in self.__peers:
            if peer['type'] != filter:
                continue
            filtered_peers.append(peer)
        return filtered_peers


def now():
    return datetime.now().strftime(DATA_FORMAT)


def str_to_datetime(datatime_string):
    return datetime.strptime(datatime_string, DATA_FORMAT)


def setup_logger():
    settings.logger = logging.getLogger(__name__)
    settings.logger.setLevel(settings.logging_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(settings.logging_format)
    handler.setFormatter(formatter)
    settings.logger.addHandler(handler)


def read_config_file():
    with open(settings.config_file, 'r') as cfg_file:
        return json.loads(cfg_file.read())


def import_config():
    options, args = get_args.parser()
    options_items = vars(options)
    config = read_config_file()
    for k, v in config.items():
        if k in options_items and not getattr(options, k) is None:
            continue
        setattr(settings, k, v)


def import_options():
    options, args = get_args.parser()
    for key in vars(options):
        value = getattr(options, key)
        if value is None:
            continue
        setattr(settings, key, value)


def setup_settings():
    setup_logger()
    import_options()
    import_config()


def pack_host(host):
    return ''.join(map(chr, (map(int, map(str, host.split('.')))))).encode()


def pack_port(port):
    return struct.pack('H', port)


def unpack_stream(data, length):
    return data[ :length], data[length: ]


def encode(text):
    if isinstance(text, str):
        return text.encode()
    if isinstance(bytes, str):
        return text
    raise Exception('Error: can\' encode, twrong type is {}'.format(type(text)))
