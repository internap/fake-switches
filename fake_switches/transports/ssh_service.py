# Copyright 2015 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from twisted.conch import avatar, interfaces as conchinterfaces
from twisted.conch.insults import insults
from twisted.conch.ssh import factory, keys, session
from twisted.cred import portal, checkers
from zope.interface import implementer

from fake_switches.terminal.ssh import SwitchSSHShell
from fake_switches.transports.base_transport import BaseTransport


@implementer(conchinterfaces.ISession)
class SSHDemoAvatar(avatar.ConchUser):
    def __init__(self, username, switch_core):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.switch_core = switch_core
        self.channelLookup.update({b'session': session.SSHSession})

        netconf_protocol = switch_core.get_netconf_protocol()
        if netconf_protocol:
            self.subsystemLookup.update({b'netconf': netconf_protocol})

    def openShell(self, protocol):
        server_protocol = insults.ServerProtocol(SwitchSSHShell, self, switch_core=self.switch_core)
        server_protocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(server_protocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        raise NotImplementedError()

    def closed(self):
        pass

    def windowChanged(self, newWindowSize):
        pass

    def eofReceived(self):
        pass


@implementer(portal.IRealm)
class SSHDemoRealm:
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def requestAvatar(self, avatarId, mind, *interfaces):
        if conchinterfaces.IConchUser in interfaces:
            return interfaces[0], SSHDemoAvatar(avatarId, switch_core=self.switch_core), lambda: None
        else:
            raise Exception("No supported interfaces found.")


def getRSAKeys():
    host_public_key = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC53ANLkvrZmufQsXuIZch7zrzWbevrqQpNT+/YUBffi3wX+I4lfJibL4lFwqgwR3Hshy7hqX4tgQiU6nWSz5QD/dcCuoaMvhVxVH0WyCtzc69xL9GBfHzyDvWYV/SU1bMiWwzWsFXSrnASeok1/zuDK4z5F0+U5gOtN009988/sw5DYBNer8gYq04Lt4r1WlCEPdyemLNkwHqNLMI7zgZw65djAEK7m+t8DhjtpV7ODxKi/ZB5TegoIbdMciMOTR+alX4bdw85d9tkVot7wLFX627/+DIbO0DokFfIDgJAt/jBVZf+MFhzjta/ZicxIWsTxK1yyOpmDlGFTHDR0Zwp fake@ssh"""
    host_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAudwDS5L62Zrn0LF7iGXIe8681m3r66kKTU/v2FAX34t8F/iO
JXyYmy+JRcKoMEdx7Icu4al+LYEIlOp1ks+UA/3XArqGjL4VcVR9Fsgrc3OvcS/R
gXx88g71mFf0lNWzIlsM1rBV0q5wEnqJNf87gyuM+RdPlOYDrTdNPffPP7MOQ2AT
Xq/IGKtOC7eK9VpQhD3cnpizZMB6jSzCO84GcOuXYwBCu5vrfA4Y7aVezg8Sov2Q
eU3oKCG3THIjDk0fmpV+G3cPOXfbZFaLe8CxV+tu//gyGztA6JBXyA4CQLf4wVWX
/jBYc47Wv2YnMSFrE8StcsjqZg5RhUxw0dGcKQIDAQABAoIBABHi5YJJY9C7QqHn
4q6OtQuNKsksDO9B9lbYYYmcs590yf14kx1ybzFIEtrez9bNmV4c6FsZN6Zja5MB
OU1moqT7scx2bOpwhJnCesNNgjj7IiAvbOccNt4IqIP/uu7z3ehpgMPMdoXu+aQd
nMTQikamU0vJfYQj2qi50Los9gn4JEEkqS9aG6i/78WOOY4bc6+WPvavvv9+yCVO
CMLuYatByqvdHM3PO5+9ktRyUC8UpOocsQqX+we3ZKCcjXbvy/f7WxViNMueKXdO
dCrAXks0e3lFBwAAFs/5sYnMsDU4plZsgYD+7DmnrP5RgM4oMHKSjo7NRx03ODGP
YzSFoIECgYEA7IEcUJ1Vvt76Gqf4jJG+5TfBW7gwgxleGHYE198TwXylOpSY3+EF
322N+c5Yie+Z6XAIPpPP1IqYK3QWyXJUJtJmL0udQvZTIqRwgv4p9drqUi/JBT9F
ruSb5ye8580vd7emfQOsepoB2c/RRXqzfOMhUmAW2osDrjjjy8a0z5ECgYEAyS4n
5x+MfR11RN0mfkYt4CfBXLJXj0PNjguzyQoUuD50UCf+jl6KyT8zQwsfBUbSMWh4
vldDzg6FrSDsk8uS5Go0yOqrO+6YuVblXVCiVtfFs7x6Vi20G0mghRqlNIN9pNXG
poGKRVSVHsm7ULLwXJA6Gd8ICNqppvXjZdlGZxkCgYEAqP0oKkIBvry8oMdcxbRu
XoKUWuElaMd7gKbzlvwCtcJGnbEH+xBijd9ODyzt/sGBjFdMzMn5Ork9Oe9dSNu0
XXkBItI4sFwp0xsEedT6Tn356HfUfzdSp0EaVPUD+e2W+Uf0Ymd5mrDomaXwtmCS
V65DZQTbz5R9MMPdoQF+uMECgYAodw4zoNbjO4+g4FKjx33mvlhYSs7t1Bd+YMAy
ycJNJNLEZKcA/+cuf3XSIGSG7S3OHlNbBbZvteARaLPtLl9Hbk1btEfo8B7r+Jx9
3oAos5HiiyCYQO0fJ/oPi8J7A4+8Hfus9hVXyKGN5cm1e6h5FdF57rBxB3pkSMUK
cV+F0QKBgQDM+fA+670fIxMNa4pi+0NE00WzfZm03PzIajXXSyYdLuA77kLa3eb4
J2mT3sY7auegAXuPFKiEr2jLkgsLIuN0P8RWU/m3zPKEkOgIG3X5nOLc25E0wh0F
Jk9Gg4yPCL/ZKyIEQzqtkBUyK2P5x1OP32tcC9CxHZlXJLJdhtuQTw==
-----END RSA PRIVATE KEY-----
"""
    return host_public_key, host_private_key


class SwitchSshService(BaseTransport):
    def hook_to_reactor(self, reactor):
        ssh_factory = factory.SSHFactory()
        ssh_factory.portal = portal.Portal(SSHDemoRealm(self.switch_core))
        if not self.users:
            self.users = {'root': b'root'}
        ssh_factory.portal.registerChecker(
            checkers.InMemoryUsernamePasswordDatabaseDontUse(**self.users))

        host_public_key, host_private_key = getRSAKeys()
        ssh_factory.publicKeys = {
            b'ssh-rsa': keys.Key.fromString(data=host_public_key.encode())}
        ssh_factory.privateKeys = {
            b'ssh-rsa': keys.Key.fromString(data=host_private_key.encode())}

        lport = reactor.listenTCP(port=self.port, factory=ssh_factory, interface=self.ip)
        logging.info(lport)
        logging.info(
            "%s (SSH): Registered on %s tcp/%s" % (self.switch_core.switch_configuration.name, self.ip, self.port))
        return lport
