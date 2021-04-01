from random import choice, randint
from time import sleep


net_size = 500
peer_connections = 20
connect_probability = 0.55
disconnect_probability = 0.35
time_sleep = 0


def log(*t):
    return
    print(*t)


def get_next_peer(net, index):
    next_peer_index = net[index].get('next_peer_for_connect', index)
    next_peer_index += 1
    if next_peer_index == index:
        next_peer_index += 1
    if next_peer_index == net_size:
        next_peer_index = 0
    net[index]['next_peer_for_connect'] = next_peer_index
    return next_peer_index


def request_neighbors_for_connect(net, index):
    neighbors = net[index]['connections']
    if len(neighbors) == 0:
        log('= peer {} has no neighbors {}'.format(index, neighbors))
        return None
    neighbor = choice(list(neighbors))
    log('= peer {} request neighbor {} for connections {}'.format(index, neighbor, net[neighbor]['connections']))
    peers_to_connect = list(net[neighbor]['connections'])
    if index in peers_to_connect:
        peers_to_connect.remove(index)
    if len(peers_to_connect) == 0:
        log('= neighbor {} has no peer to connect {}'.format(neighbor, peers_to_connect))
        return None
    return choice(peers_to_connect)


def do_connect(net, index):
    log('+ try_to_connect', index, net[index]['connections'])
    if check_the_chance(connect_probability) is False:
        return

    peer = net[index]
    if peer['established']:
        peer_for_connect_index = request_neighbors_for_connect(net, index)
    else:
        peer_for_connect_index = get_next_peer(net, index)

    if peer_for_connect_index is None:
        return

    net[index]['connections'].add(peer_for_connect_index)
    net[peer_for_connect_index]['connections'].add(index)
    log('+ peer {}|{} connect with {}|{}'.format(index, net[index]['connections'], peer_for_connect_index, net[peer_for_connect_index]['connections']))
    net_is_established(net)



def check_the_chance(connect_probability):
    chance = randint(0, 100)
    log('= check_the_chance', chance, int(connect_probability * 100), chance < connect_probability * 100)
    return chance < connect_probability * 100
    #return randint(0, 100) < connect_probability * 100


def net_is_established(net):
    established = True
    for peer in net:
        if peer['established']:
            continue
        if len(peer['connections']) >= peer_connections:
            peer['established'] = True
            del peer['next_peer_for_connect']
            log('peer {} get established with peers {}'.format(peer['peer_index'], peer['connections']))
            continue
        established = False
    return established


def do_disconnect(net, index):
    log('- try_to_disconnect', index, net[index]['connections'])
    peer = net[index]
    if len(peer['connections']) == 0:
        log('- peer is alone', peer)
        return
    if check_the_chance(disconnect_probability) is False:
        return
    peer_to_disconnect_index = choice(list(peer['connections']))

    peer['connections'].remove(peer_to_disconnect_index)
    net[peer_to_disconnect_index]['connections'].remove(index)
    log('- peer {}|{} disconnect with {}|{}'.format(index, net[index]['connections'], peer_to_disconnect_index, net[peer_to_disconnect_index]['connections']))


def net_is_intact(net):
    if not net_is_established(net):
        return True

    net_parents = set()
    net_parents_connections = net[0]['connections']

    while net_parents != net_parents_connections:
        net_parents = net_parents_connections
        for peer_index in net_parents:
            peer = net[peer_index]
            net_parents_connections = net_parents_connections.union(peer['connections'])

    log('!' * 3, 'net is intact', len(net_parents) == net_size, net_parents)
    return len(net_parents) == net_size


def make_net():
    net = []
    for index in range(net_size):
        net.append({'connections': set(), 'established': False, 'peer_index': index})
    return net


def main():
    net = make_net()
    iteration = 0

    while True:
        print(iteration)
        for peer in net:
            log('>' * 3, peer)

        for index in range(net_size):
            if net_is_established(net):
                do_disconnect(net, index)

            if len(net[index]['connections']) < peer_connections:
                do_connect(net, index)

        for peer in net:
            log('<' * 3, peer)

        if not net_is_intact(net):
            break

        log('=' * 10)
        sleep(time_sleep)

        iteration += 1

    print('#' * 10)
    print(iteration)
    print(net)


if __name__ == '__main__':
    main()
