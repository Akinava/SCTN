# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import json
import random
from datetime import timedelta, datetime
from cryptotool import B58
from utilit import Singleton, now
import settings
from settings import logger


class Peers(Singleton):
    def __init__(self):
        self.__load()

    def add_client_peer(self, client_connection):
        # TODO save only peer with ports < settings.host_max_user_port
        client = {
            'type': 'client',
                  }
        # TODO

    def save_servers_list(self, servers_list):
        mapping_list = [
            ['hpn_servers_pub_key', 'pub_key'],
            ['hpn_servers_protocol', 'protocol'],
        ]
        for server_src in servers_list:
            server_dst = {'type': 'server'}
            for src, dst in mapping_list:
                server_dst[dst] = server_src[src]
            host, port = server_src['hpn_servers_addr']
            server_dst['host'] = host
            server_dst['port'] = port
            print(server_dst)
            if self.__has_peer_in_list(server_dst):
                logger.info('server {host}:{port} already in peers list'.format_map(server_dst))
                continue
            logger.info('server {host}:{port} added in peers list'.format_map(server_dst))
            self.__peers.append(server_dst)
        self.__save()

    def update_peer_last_response_field(self, connection):
        server = {
            'protocol': 'udp',
            'type': 'server',
            'pub_key': connection.get_pub_key(),
        }
        server['host'], server['port'] = connection.get_remote_addr()
        peer = self.__find_peer(server)
        peer['last_response'] = now()
        self.__save()

    def __has_peer_in_list(self, peer):
        peer = self.__find_peer(peer)
        return False if peer is None else True

    def get_random_server_from_file(self):
        servers = self.__filter_peers_by_type('server')
        if len(servers) == 0:
            return None
        filtered_servers = self.__filter_peers_by_last_response_field(servers=servers, days_delta=settings.servers_timeout_days)
        if len(filtered_servers) > 0:
            return random.choice(filtered_servers)
        return random.choice(servers)

    def __find_peer(self, peer_data):
        for peer in self.__peers:
            for key in ['host', 'port', 'pub_key', 'type']:
                if peer.get(key) != peer_data.get(key):
                    continue
            return peer
        return None

    def get_servers_list(self, max):
        servers = self.__filter_peers_by_type('server')
        if len(servers) > 0:
            servers = self.__filter_peers_by_last_response_field(servers=servers, days_delta=settings.servers_timeout_days)
        return servers[: max]

    def __filter_peers_by_last_response_field(self, servers, days_delta):
        filtered_list = []
        for peer in servers:
            datatime_string = peer.get('last_response')
            if datatime_string is None:
                continue
            if datetime.strptime(datatime_string, settings.DATA_FORMAT) + timedelta(days=days_delta) < datetime.now():
                continue
            filtered_list.append(peer)
        return filtered_list

    def __load(self):
        self.__peers = self.__read_file()
        self.__unpack_peers_property()

    def __save(self):
        packed_peers = self.__pack_peers_property()
        self.__save_file(packed_peers)

    def __read_file(self):
        with open(settings.peers_file, 'r') as f:
            peers_list = json.loads(f.read())
        return peers_list

    def __save_file(self, packed_peers):
        with open(settings.peers_file, 'w') as f:
            f.write(json.dumps(packed_peers, indent=4))

    def __unpack_peers_property(self):
        for peer in self.__peers:
            peer['pub_key'] = B58().unpack(peer['pub_key'])

    def __pack_peers_property(self):
        packed_peers = []
        for peer in self.__peers:
            copied_peer = peer.copy()
            copied_peer['pub_key'] = B58().pack(copied_peer['pub_key'])
            packed_peers.append(copied_peer)
        return packed_peers

    def __filter_peers_by_type(self, peers_filter):
        filtered_peers = []
        for peer in self.__peers:
            if peer['type'] != peers_filter:
                continue
            filtered_peers.append(peer)
        return filtered_peers
