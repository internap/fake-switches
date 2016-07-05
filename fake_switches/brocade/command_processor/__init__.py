from fake_switches.switch_configuration import split_port_name


def explain_missing_port(port_name):
    name, number = split_port_name(port_name)
    try:
        slot, port = number.split('/', 1)

        if int(port) > 64:
            return ['Invalid input -> {}'.format(number),
                    'Type ? for a list']
        else:
            if int(slot) > 1:
                return ['Error - interface {} is not an ETHERNET interface'.format(number)]
            else:
                return ["Error - invalid interface {}".format(number)]
    except ValueError:
        return ['Invalid input -> {0}  {1}'.format(name.replace('ethe ', ''), number),
                'Type ? for a list']
