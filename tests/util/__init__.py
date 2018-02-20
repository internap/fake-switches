from fake_switches.switch_configuration import Port, AggregatedPort

_unique_port_index = 20000


def _unique_port():
    global _unique_port_index
    _unique_port_index += 1
    return _unique_port_index


def _juniper_ports_with_less_ae():
    return [Port("ge-0/0/{}".format(i)) for i in range(1, 5)] + \
           [AggregatedPort("ae{}".format(i)) for i in range(1, 5)]
