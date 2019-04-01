import os
import yaml
import argparse
import logging


from fake_switches import switch_factory
from fake_switches.transports.ssh_service import SwitchSshService
from twisted.internet import reactor
from fake_switches.pre_run_configurations import cisco_generic

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
    parser.add_argument('--static_configs', type=str, help='Static configurations')

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

    with open("%s%s%s%s%s%s%s" % (os.path.dirname(__file__), os.path.sep, '..', os.path.sep,
                                  "pre_run_configurations",
                                  os.path.sep,
                                  args.static_configs)) as f:
        static_configs = yaml.load(f)
        cisco_generic.pre_run_configurations(switch_core.switch_configuration, static_configs)
    logger.info('Starting reactor')
    reactor.run()


if __name__ == "__main__":
    main()