# install pytest
# run `python3 -m pytest`

from unittest import mock
import os
import unittest
from scripts.piaware_config import *
from uuid import UUID

class TestMetadata(unittest.TestCase):
    def test_get_setting(self):
        testm = Metadata()

        dne = testm.get_setting("doesnt exist")
        assert dne is None

        exists = testm.get_setting("use-gpsd")
        assert exists.setting_type == "bool"
        assert exists.default == True

    def test_convert_str_to_bool(self):
        testm = Metadata()
        assert testm.convert_str_to_bool("yes") == True
        assert testm.convert_str_to_bool("no") == False

    def test_convert_str_to_uuid(self):
        testm = Metadata()
        assert testm.convert_str_to_uuid("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
    
    def test_convert_str_to_gain(self):
        testm = Metadata()
        assert testm.convert_str_to_gain("max") == "max"
        assert testm.convert_str_to_gain("-10") == "max"
        assert testm.convert_str_to_gain("-11") == "max"
        assert testm.convert_str_to_gain("5") == 5
        assert testm.convert_str_to_gain("4.5") == 4.5
        
    
    def test_convert_value(self):
        testm = Metadata()
        assert testm.convert_value("image-type", "test_type") == "test_type"
        assert testm.convert_value("manage-config", "no") == False
        assert testm.convert_value("priority", "1") == 1
        assert testm.convert_value("adaptive-min-gain", "1.2") == 1.2
        assert testm.convert_value("force-mac-address", "01:23:45:67:89:AB") == "01:23:45:67:89:AB"
        assert testm.convert_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
        assert testm.convert_value("rtlsdr-gain", "-10") == "max"

        testm.settings["test"] = MetadataSettings(setting_type="dne", default = True)
        with self.assertRaises(TypeError):
            testm.convert_value("test", "dne")

    def test_validate_bool(self):
        testm = Metadata()
        assert testm.validate_bool("yes") == True
        assert testm.validate_bool("no") == True
        assert testm.validate_bool("123") == False


    def test_validate_int(self):
        testm = Metadata()
        assert testm.validate_int("1") == True
        assert testm.validate_int("-1") == True
        assert testm.validate_int("no") == False
        assert testm.validate_int("1.222") == False

    def test_validate_double(self):
        testm = Metadata()
        assert testm.validate_double("1") == True
        assert testm.validate_double("-1") == True
        assert testm.validate_double("no") == False
        assert testm.validate_double("1.222") == True
        assert testm.validate_double("-1.222") == True

    def test_validate_mac(self):
        testm = Metadata()
        assert testm.validate_mac("01:23:45:67:89:AB") == True
        assert testm.validate_mac("01:23:45:67:89") == False
        assert testm.validate_mac("01:23:45:67:89:") == False
        assert testm.validate_mac("312") == False

    def test_validate_uuid(self):
        testm = Metadata()
        assert testm.validate_uuid("123") == False
        assert testm.validate_uuid("e8a2fe66-8ecd-4b91-b6d5-7700a1c") == False
        assert testm.validate_uuid("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == True
        
    def test_validate_gain(self):
        testm = Metadata()
        assert testm.validate_gain("-10") == True
        assert testm.validate_gain("-11") == True
        assert testm.validate_gain("10") == True
        assert testm.validate_gain("-10.2") == True
        assert testm.validate_gain("max") == True

        assert testm.validate_gain("-noasdw") == False

    def test_validate_value(self):
        testm = Metadata()
        print("validate")
        tests = [
            (testm.validate_value("image-type", "test_type")),
            (testm.validate_value("manage-config", "no")),
            (testm.validate_value("priority", "1")),
            (testm.validate_value("adaptive-min-gain", "1.2")),
            (testm.validate_value("force-mac-address", "01:23:45:67:89:AB")),
            (testm.validate_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c")),
            (testm.validate_value("rtlsdr-gain", "-10"))
        ]

        for t in tests:
            assert t == True

        testm.settings["test"] = MetadataSettings(setting_type="dne", default = True)
        with self.assertRaises(TypeError):
            testm.validate_value("test", "dne")