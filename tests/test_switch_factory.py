import unittest

import mock
from fake_switches import switch_core
from fake_switches import switch_factory
from hamcrest import assert_that, contains_string, is_, instance_of


class SwitchFactoryTest(unittest.TestCase):
    def test_switch_model_does_not_exist(self):
        factory = switch_factory.SwitchFactory(mapping={})
        with self.assertRaises(switch_factory.InvalidSwitchModel) as e:
            factory.get('invalid_model')

        assert_that(str(e.exception), contains_string('invalid_model'))

    def test_switch_model_exists(self):
        core_mock = mock.create_autospec(switch_core.SwitchCore)
        core_mock.get_default_ports.return_value = mock.sentinel.port_list
        with mock.patch('fake_switches.switch_factory.switch_configuration') as switch_conf_module:
            switch_conf_instance = mock.Mock()
            switch_conf_class = mock.Mock()
            switch_conf_class.return_value = switch_conf_instance
            switch_conf_module.SwitchConfiguration = switch_conf_class
            factory = switch_factory.SwitchFactory(mapping={'a': core_mock})
            switch = factory.get('a', 'my_hostname')

        assert_that(switch, is_(instance_of(switch_core.SwitchCore)))
        switch_conf_class.assert_called_with('127.0.0.1',
                                             name='my_hostname',
                                             ports=mock.sentinel.port_list,
                                             privileged_passwords=['root'])
        core_mock.assert_called_with(switch_conf_instance)
