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
        assert testm.convert_value("force-macaddress", "01:23:45:67:89:AB") == "01:23:45:67:89:AB"
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
        assert testm.validate_mac("13423:01:23:45:67:89:AB") == False
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
        tests = [
            (testm.validate_value("image-type", "test_type")),
            (testm.validate_value("manage-config", "no")),
            (testm.validate_value("priority", "1")),
            (testm.validate_value("adaptive-min-gain", "1.2")),
            (testm.validate_value("force-macaddress", "01:23:45:67:89:AB")),
            (testm.validate_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c")),
            (testm.validate_value("rtlsdr-gain", "-10"))
        ]

        for t in tests:
            assert t == True

        testm.settings["test"] = MetadataSettings(setting_type="dne", default = True)
        with self.assertRaises(TypeError):
            testm.validate_value("test", "dne")

class TestConfigFile(unittest.TestCase):

    def mock_config_file(*args):
        class Example:
            def __enter__(self):
                return ["image-type image", 
                "adaptive-min-gain -1" , 
                "doesnt exist" , 
                "manage-config 1232", 
                "test 1", 
                "adept-serverport 2", 
                "adept-serverport 5",
                "wireless-netmask 255.255.255.0"
                ]

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return Example()

    def is_file_mock(*args):
        return True

    def test_process_quotes(self):
        testc = ConfigFile("file")

        assert testc.process_quotes("") == ""
        assert testc.process_quotes("\"thing\"") == "thing"
        assert testc.process_quotes("commented  # 1 23 ") == "commented"

        assert testc.process_quotes("\"commented  1\"# 1 23 ") == "commented  1"
        assert testc.process_quotes("\"commented\\s  1\"# 1 23 ") == "commenteds  1"
        assert testc.process_quotes("\"commented\\s\\1") == "commenteds1"

    def test_parse_line(self):
        testc = ConfigFile("file")

        assert testc.parse_line("    # commented") is None
        key, val = testc.parse_line("option ")
        assert key == "option"
        assert val == ""

        key, val = testc.parse_line("option yes")
        assert key == "option"
        assert val == "yes"

        key, val = testc.parse_line("option \"yes\"")
        assert key == "option"
        assert val == "yes"

        key, val = testc.parse_line("option \"   yes    ")
        assert key == "option"
        assert val == "yes"

    @mock.patch("builtins.open", side_effect=mock_config_file)
    @mock.patch("os.path.isfile", side_effect=is_file_mock)
    def test_read_config(self, open_mock, is_file_mock):
        testm = Metadata()
        testm.settings["test"] = MetadataSettings(setting_type="int", deprecated=True)
        testc = ConfigFile("file", metadata = Metadata())
        testc.read_config()

        assert testc.get("image-type") == "image"
        assert testc.get("adaptive-min-gain") == -1
        assert testc.get("test") is None
        print(testc.get("wireless-netmask"))

class TestConfigGroup(unittest.TestCase):

    def mock_config_file(*args, **kwargs):
        print(*args)

        class Example:
            def __enter__(self):
                if args[0] == "file1":
                    return ["image-type image", "adaptive-min-gain -1"]
                else:
                    return ["image-type image_2", "adaptive-min-gain -2", "wired-network no"]

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return Example()

    def is_file_mock(*args):
        return True

    @mock.patch("builtins.open", side_effect=mock_config_file)
    @mock.patch("os.path.isfile", side_effect=is_file_mock)
    def test_config_group(self, config_mock, is_file_mock):

        f1 = ConfigFile(filename="file1", priority=30, metadata = Metadata())
        f2 = ConfigFile(filename="file2", priority=40, metadata = Metadata())

        cfg = ConfigGroup(metadata=Metadata(), files=[f1, f2])
        cfg.read_configs()

        assert cfg.files[0]._priority == 40
        assert cfg.files[1]._priority == 30
        assert cfg.get("image-type") == "image_2"
        assert cfg.get("wired-network") is False
        assert cfg.get("wireless-network") is False

    def test_create_standard_piaware_config_group(self):
        cfg = create_standard_piaware_config_group()
        assert cfg.files[0]._priority == 30
        assert cfg.files[1]._priority == 40
        assert cfg.files[2]._priority == 50

class TestHelpers(unittest.TestCase):
    def test_check_enum(self):
        assert check_enums("receiver", "sdr") is True