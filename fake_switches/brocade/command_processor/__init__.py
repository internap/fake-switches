from fake_switches.switch_configuration import split_port_name


def explain_missing_port(port_name):
    _, number = split_port_name(port_name)
    slot, port = number.split('/', 1)
    if int(port) > 64:
        return ['Invalid input -> {}'.format(number),
                'Type ? for a list']
    else:
        if int(slot) > 1:
            return ['Error - interface {} is not an ETHERNET interface'.format(number)]
        else:
            return ["Error - invalid interface {}".format(number)]
