[![Build Status](https://travis-ci.org/internap/fake-switches.svg?branch=master)](https://travis-ci.org/internap/fake-switches)
[![PyPI version](https://badge.fury.io/py/fake-switches.svg)](http://badge.fury.io/py/fake-switches)

Fake-switches
=============

Fake-switches is a pluggable switch/router command-line simulator. It is meant
to help running integrated tests against network equipment without the burden
of having devices in a lab. This helps testing the communication with the
equipment along with all of its layers for more robust high level tests.  Since
it is meant to be used by other systems and not humans, error handling on
incomplete commands and fail-proofing has been mostly left out and only
relevant errors are shown. 

The library can easily be extended to react to some changes in the fake switch
configuration and control an actual set of tools to have an environment
behaving like a real one driven by a switch.  For example, you could hook
yourself to the VLAN creation and use vconfig to create an actual vlan on a
machine for some network testing.

This library is NOT supported by any vendor, it was built by
reverse-engineering network equipment.


Actual supported commands
=========================

Command support has been added in a as-needed manner for the purpose of what
was tested and how.  So see which commands may be used and their supported
behavior, please see the tests section for each model.

| Model   | Protocols        | Test location |
| ------- | ---------------- | ------------- |
| Cisco   | ssh and telnet   | [tests/cisco/test_cisco_switch_protocol.py](tests/cisco/test_cisco_switch_protocol.py) |             
| Brocade | ssh              | [tests/brocade/test_brocade_switch_protocol.py](tests/brocade/test_brocade_switch_protocol.py) |
| Juniper | netconf over ssh | [tests/juniper/juniper_base_protocol_test.py](tests/juniper/juniper_base_protocol_test.py) |
| Dell    | ssh and telnet   | [tests/dell/](tests/dell/) |


Making the switches more real
=============================

The SwitchConfiguration class can be extended and given an object factory with
custom classes that can act upon resources changes. For example :

```python

from twisted.internet import reactor
from fake_switches.switch_configuration import SwitchConfiguration, Port
from fake_switches.ssh_service import SwitchSshService
from fake_switches.cisco.cisco_core import CiscoSwitchCore

class MySwitchConfiguration(SwitchConfiguration):
    def __init__(self, *args, **kwargs):
        super(MySwitchConfiguration, self).__init__(objects_overrides={"Port": MyPort}, *args, **kwargs)


class MyPort(Port):
    def __init__(self, name):
        self._access_vlan = None

        super(MyPort, self).__init__(name)

    @property
    def access_vlan(self):
        return self._access_vlan

    @access_vlan.setter
    def access_vlan(self, value):
        if self._access_vlan != value:
            self._access_vlan = value
            print "This could add vlan to eth0"


if __name__ == '__main__':
    ssh_service = SwitchSshService(
        ip="127.0.0.1",
        ssh_port=11001,
        switch_core=CiscoSwitchCore(MySwitchConfiguration("127.0.0.1", "my_switch", ports=[MyPort("FastEthernet0/1")])))
    ssh_service.hook_to_reactor(reactor)
    reactor.run()
```

Then, if you connect to the switch and do

```
    ssh root@127.0.0.1 -p 11001
    password : root
    > enable
    password:
    # configure terminal
    # vlan 1000
    # interface FastEthernet0/1
    # switchport access vlan 1000
```

Your program should say "This could add vlan to eth0" or do anything you would
want it to do :)


Contributing
============

Feel free raise issues and send some pull request,
we'll be happy to look at them!
