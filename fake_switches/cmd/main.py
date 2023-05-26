import argparse
import logging


from fake_switches import switch_factory
from fake_switches.transports.http_service import SwitchHttpService
from fake_switches.transports.ssh_service import SwitchSshService
from fake_switches.transports.telnet_service import SwitchTelnetService
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

    if args.model == "arista_generic":
        http_service = SwitchHttpService(
            ip=args.listen_host,
            port=80,
            switch_core=switch_core,
            users={args.username: args.password})
        http_service.hook_to_reactor(reactor)

    if args.model in ['cisco_generic',
                      'cisco_2960_24TT_L',
                      'cisco_2960_48TT_L',
                      'dell_generic',
                      'dell10g_generic']:
        telnet_service = SwitchTelnetService(
            ip=args.listen_host,
            port=args.listen_port+1,
            switch_core=switch_core,
            users={args.username: args.password})
        telnet_service.hook_to_reactor(reactor)

    ssh_service = SwitchSshService(
        ip=args.listen_host,
        port=args.listen_port,
        switch_core=switch_core,
        users={args.username: args.password})
    ssh_service.hook_to_reactor(reactor)

    logger.info('Starting reactor')
    reactor.run()
