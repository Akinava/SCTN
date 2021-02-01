import asyncio


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        request = data.decode()
        response = "Hello Client"
        print('Received %r from %s' % (request, addr))
        print('Send %r to %s' % (response, addr))
        self.transport.sendto(response.encode(), addr)

    def connection_lost(self, addr):
        pass


async def main():
    print("Starting UDP server")

    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all
    # client requests.
    transport0, protocol0 = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('0.0.0.0', 9990))
    transport1, protocol1 = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('0.0.0.0', 9991))

    try:
        await asyncio.sleep(20)
    finally:
        transport0.close()
        transport1.close()
    print("Stop UDP server")


asyncio.run(main())