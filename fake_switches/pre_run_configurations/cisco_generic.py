import random
import re

import fake_switches.switch_configuration as switch_configuration
from fake_switches.switch_configuration import Port
from netaddr import IPNetwork, IPAddress
START_VLAN_NUMBER = 2000
NO_OF_VRFS = 10


def add_vrfs(pre_run_switch_configuration, static_configurations):
    """
    @type pre_run_switch_configuration: switch_configuration.SwitchConfiguration
    @param pre_run_switch_configuration:
    @param count: Number of VRFs to create
    @return:
    """
    for i in xrange(static_configurations['switch_level_configs']['vrfs']['number']):
        pre_run_switch_configuration.add_vrf(switch_configuration.VRF(name="vrf_{}".format(i + 2001)))
        # if static_configurations['switch_level_configs']['vrfs']['no_of_routes'].startswith('random'):
        #     re.match()
        # add_routes_for_vrf(pre_run_switch_configuration, )


def add_vlans(pre_run_switch_configuration, static_configurations):
    """
    @type pre_run_switch_configuration: switch_configuration.SwitchConfiguration
    @param pre_run_switch_configuration:
    @param count: Number of VLANs to create
    @return:
    """
    for i in xrange(static_configurations['switch_level_configs']['vlans']['number']):
        pre_run_switch_configuration.add_vlan(switch_configuration.Vlan(name="vlan_{}".format(i + START_VLAN_NUMBER),
                                                                        number=i + 2000,
                                                                        switch_configuration=pre_run_switch_configuration))


def add_routes(pre_run_configurations, static_configurations):
    """
    @param pre_run_configurations: switch_configuration.SwitchConfiguration
    @param count: Number of routes
    @return:
    """
    add_routes_for_vrf(pre_run_configurations, static_configurations['switch_level_configs']['routes']['number'],
                       'DEFAULT-LAN')


def add_routes_for_vrf(pre_run_configurations, no_of_routes, vrf_name):
    for i in xrange(no_of_routes):
        ip = IPAddress(3221225985 + i * 256)
        pre_run_configurations.add_static_route(
            switch_configuration.Route(destination=ip, mask='24', next_hop="10.1.1.1", vrf_name=vrf_name))


def get_mac_addr():
    mac = [ 0x00, 0x16, 0x3e,
    random.randint(0x00, 0x7f),
    random.randint(0x00, 0xff),
    random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def add_macs(pre_run_configurations, static_configurations):
    """
    @param pre_run_configurations: switch_configuration.SwitchConfiguration
    @param count:
    @return:
    """
    for i in xrange(static_configurations['switch_level_configs']['mac_table']['number']):
        mac = get_mac_addr()
        pre_run_configurations.add_mac_entry(
            switch_configuration.MACEntry(mac_address=mac, vlan=i % 10 + START_VLAN_NUMBER,
                                          interface="FastEthernet0/1"))


def add_ports(pre_run_configurations, static_configurations):
    port_list = [Port("Eth1/{}".format(x)) for x in xrange(1, 33)]
    for port, static_config_port in zip(port_list, static_configurations['switch_level_configs']['ports']):
        port.mode = static_config_port['mode']
        port.access_vlan = static_config_port['access_vlan']
        port.shutdown = static_config_port['status']


def pre_run_configurations(pre_run_switch_configuration, static_configurations):
    """
    @type pre_run_switch_configuration: switch_configuration.SwitchConfiguration
    @return:
    """
    add_vrfs(pre_run_switch_configuration, static_configurations)
    add_vlans(pre_run_switch_configuration, static_configurations)
    add_routes(pre_run_switch_configuration, static_configurations)
    add_ports(pre_run_switch_configuration, static_configurations)
    add_macs(pre_run_switch_configuration, static_configurations)



