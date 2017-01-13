import argparse

from fake_switches import switch_factory
from fake_switches.ssh_service import SwitchSshService
from twisted.internet import reactor


def main():
    parser = argparse.ArgumentParser(description='Fake-switch simulator launcher')
    parser.add_argument('model', type=str, help='Switch model')
    parser.add_argument('hostname', type=str, nargs='?', help='Switch hostname')
    parser.add_argument('listen_host', type=str, help='Listen host')
    parser.add_argument('listen_port', type=int, help='Listen port')

    args = parser.parse_args()

    factory = switch_factory.SwitchFactory()
    hostname = args.hostname or 'hostname.invalid'
    switch_core = factory.get(args.model, hostname)

    ssh_service = SwitchSshService(
        ip=args.listen_host,
        ssh_port=int(args.listen_port),
        switch_core=switch_core)
    ssh_service.hook_to_reactor(reactor)

    print('Starting reactor')
    reactor.run()

