import argparse
import logging


from fake_switches import switch_factory
from fake_switches.transports.ssh_service import SwitchSshService
from twisted.internet import reactor


logging.basicConfig(level='DEBUG')
logger = logging.getLogger()

# NOTE(mmitchell): This is necessary because some imports will initialize the root logger.
logger.setLevel('DEBUG')


def main():
    parser = argparse.ArgumentParser(description='Fake-switch simulator launcher',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', type=str, default='cisco_generic',
                        help='Switch model, allowed values are ' + ', '.join(switch_factory.DEFAULT_MAPPING.keys()))
    parser.add_argument('--hostname', type=str, default='switch', help='Switch hostname')
    parser.add_argument('--username', type=str, default='root', help='Switch username')
    parser.add_argument('--password', type=str, default='root', help='Switch password')
    parser.add_argument('--listen-host', type=str, default='0.0.0.0', help='Listen host')
    parser.add_argument('--listen-port', type=int, default=2222, help='Listen port')

    args = parser.parse_args()
    args.password = args.password.encode()

    factory = switch_factory.SwitchFactory()
    switch_core = factory.get(args.model, args.hostname, args.password)

    ssh_service = SwitchSshService(
        ip=args.listen_host,
        port=args.listen_port,
        switch_core=switch_core,
        users={args.username: args.password})
    ssh_service.hook_to_reactor(reactor)

    logger.info('Starting reactor')
    reactor.run()
