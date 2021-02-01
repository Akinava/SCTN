# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import asyncio


class EchoClientProtocol:
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        print("Received:", data.decode())

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost0 = loop.create_future()
    on_con_lost1 = loop.create_future()
    message = "Hello Server"

    transport0, protocol0 = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(message, on_con_lost0),
        local_addr=('0.0.0.0', 9995),
        remote_addr=('127.0.0.1', 9990))
    transport1, protocol1 = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(message, on_con_lost1),
        local_addr=('0.0.0.0', 9996),
        remote_addr=('127.0.0.1', 9991))

    try:
        await on_con_lost0
        await on_con_lost1
    finally:
        transport0.close()
        transport1.close()


asyncio.run(main())