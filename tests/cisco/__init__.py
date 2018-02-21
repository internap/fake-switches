def enable(t):
    t.write("enable")
    t.read("Password: ")
    t.write_invisible(t.conf["extra"].get("password", "root"))
    t.read("my_switch#")


def create_vlan(t, vlan, name=None):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("vlan %s" % vlan)
    t.read("my_switch(config-vlan)#")
    if name:
        t.write("name %s" % name)
        t.read("my_switch(config-vlan)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def create_interface_vlan(t, vlan):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface vlan %s" % vlan)
    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def create_port_channel_interface(t, po_id):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface port-channel %s" % po_id)
    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def remove_vlan(t, vlan):
    configuring(t, do="no vlan %s" % vlan)


def set_interface_on_vlan(t, interface, vlan):
    configuring_interface(t, interface, do="switchport mode access")
    configuring_interface(t, interface, do="switchport access vlan %s" % vlan)


def revert_switchport_mode_access(t, interface):
    configuring_interface(t, interface, do="no switchport access vlan")
    configuring_interface(t, interface, do="no switchport mode access")


def configuring(t, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")

    t.write(do)

    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_interface(t, interface, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface %s" % interface)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_interface_vlan(t, interface, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface vlan %s" % interface)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_port_channel(t, number, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface port-channel %s" % number)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interface %s " % interface)
    t.readln("Building configuration...")
    t.readln("")
    t.readln("Current configuration : \d+ bytes", regex=True)
    t.readln("!")
    for line in config:
        t.readln(line)
    t.readln("")
    t.read("my_switch#")
