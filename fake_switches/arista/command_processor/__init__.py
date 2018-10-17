
def vlan_name(vlan):
    return vlan.name or ("default" if vlan.number == 1 else None)


def vlan_display_name(vlan):
    return vlan_name(vlan) or "VLAN{:04d}".format(vlan.number)
