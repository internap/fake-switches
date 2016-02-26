import unittest


class SupportLegacyImportPathTest(unittest.TestCase):
    def test_old_import_path_still_works(self):
        from fake_switches.juniper.juniper_qfx_copper_core import JuniperQfxCopperSwitchCore
