from unittest import mock
import os
import unittest
from flightaware_piaware_config.src.flightaware_piaware_config.piaware_config import *
from uuid import UUID

class TestMetadataSettings(unittest.TestCase):
    def test_initialization(seflf):
        testm = MetadataSettings(IntegerProcessor)
        assert testm.processor is not None
        assert testm.setting_type is None
        assert testm.default is None
        assert testm.protect is None
        assert testm.sdonly is None
        assert testm.network is None
        assert testm.deprecated is False

class TestMetadata(unittest.TestCase):
    def test_get_setting(self):
        testm = Metadata()

        with self.assertRaises(ValueError):
            testm.get_setting("doesnt exist")

        exists = testm.get_setting("use-gpsd")
        assert exists.setting_type == "bool"
        assert exists.default == True

    def test_enum_processor(self):
        e = EnumProcessor(SLOW_CPU)
        assert e.validate("yes") is True
        assert e.validate("adwaiocmisow") is False
        assert e.parse("yes") == "yes"

    def test_bool_processor(self):
        bp = BoolProcessor
        assert bp.validate("yes") is True
        assert bp.validate("no") is True
        assert bp.validate("No") is True
        assert bp.validate("122,.21s") is False

        assert bp.parse("yes") is True
        assert bp.parse("no") is False

    def test_uuid_processor(self):
        p = UUIDProcessor
        assert p.validate("123") == False
        assert p.validate("e8a2fe66-8ecd-4b91-b6d5-7700a1c") == False
        assert p.validate("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == True

        assert p.parse("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
        
    def test_gain_processor(self):
        g = GainProcessor
        assert g.validate("-10") is True
        assert g.validate("-11") is True
        assert g.validate("10") is True
        assert g.validate("-10.2") is True
        
        assert g.validate("max") is True
        assert g.validate("-noasdw") is False

        assert g.parse("max") == "max"
        assert g.parse("-10") == "max"
        assert g.parse("-11") == "max"
        assert g.parse("5") == 5
        assert g.parse("4.5") == 4.5

    def test_int_processor(self):
        a = IntegerProcessor
        assert a.validate("1") is True
        assert a.validate("-1") is True
        assert a.validate("no") is False
        assert a.validate("1.222") is False

        assert a.parse("1") == 1
        assert a.parse("-1") == -1
    

    def test_double_processor(self):
        d = DoubleProcessor
        assert d.validate("1") is True
        assert d.validate("-1") is True
        assert d.validate("no") is False
        assert d.validate("1.222") is True
        assert d.validate("-1.222") is True

        assert d.parse("1") == 1
        assert d.parse("-1") == -1
        assert d.parse("0") == 0
        assert d.parse("23.1") == 23.1
        assert d.parse("-12.23") == -12.23

    def test_mac_processor(self):
        m = MACProcessor
        assert m.validate("01:23:45:67:89:AB") == True
        assert m.validate("01:23:45:67:89") == False
        assert m.validate("01:23:45:67:89:") == False
        assert m.validate("13423:01:23:45:67:89:AB") == False
        assert m.validate("312") == False
        assert m.validate("false12") == False

        assert m.parse("01:23:45:67:89:AB") == "01:23:45:67:89:AB"

    def test_netmask_processor(self):
        n = NetmaskProcessor
        assert n.validate("255.255.255.0") is True
        assert n.validate("255.255.0") is False
        assert n.validate("255.301.0.0") is False
        assert n.validate("123") is False
        assert n.validate("False") is False
        assert n.validate("adawf") is False

        assert n.parse("255.255.255.0") == "255.255.255.0"

    def test_parse_value(self):
        testm = Metadata()
        assert testm.parse_value("image-type", "test_type") == "test_type"
        assert testm.parse_value("manage-config", "no") == False
        assert testm.parse_value("priority", "1") == 1
        assert testm.parse_value("adaptive-min-gain", "1.2") == 1.2
        assert testm.parse_value("force-macaddress", "01:23:45:67:89:AB") == "01:23:45:67:89:AB"
        assert testm.parse_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
        assert testm.parse_value("rtlsdr-gain", "-10") == "max"

        with self.assertRaises(ValueError):
            testm.parse_value("test", "dne")

    def test_validate_value(self):
        testm = Metadata()
        tests = [
            (testm.validate_value("image-type", "test_type")),
            (testm.validate_value("manage-config", "no")),
            (testm.validate_value("priority", "1")),
            (testm.validate_value("adaptive-min-gain", "1.2")),
            (testm.validate_value("force-macaddress", "01:23:45:67:89:AB")),
            (testm.validate_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c")),
            (testm.validate_value("rtlsdr-gain", "-10")),
            (testm.validate_value("wireless-netmask", "255.255.0.0"))
        ]

        for t in tests:
            assert t == True

        with self.assertRaises(ValueError):
            testm.validate_value("test", "dne")

class TestConfigFile(unittest.TestCase):

    def mock_config_file(*args):
        class Example:
            def __enter__(self):
                return ["image-type image\n", 
                "adaptive-min-gain -1\n" , 
                "manage-config 1232\n", 
                "adept-serverport 2\n", 
                "adept-serverport 5\n",
                "wireless-netmask 255.255.255.0\n",
                "adept-serverhosts test.usa.flightaware.com\n",
                "use-gpsd\n"
                ]

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return Example()

    @mock.patch("builtins.open", side_effect=mock_config_file)
    def test_read_config_into_list(self, open_mock):
        f = ConfigFile("test.txt")        
        l = f.read_config_into_list()
        assert len(l) == 8
        assert l[0] == "image-type image"
        assert l[1] =="adaptive-min-gain -1"
        assert l[2] =="manage-config 1232"
        assert l[3] =="adept-serverport 2"
        assert l[4] =="adept-serverport 5"
        assert l[5] =="wireless-netmask 255.255.255.0"
        assert l[6] =="adept-serverhosts test.usa.flightaware.com"
        assert l[7] =="use-gpsd"


    def test_process_quotes(self):
        testc = ConfigFile("file")

        assert testc.process_quotes("") == ""
        assert testc.process_quotes("\"thing\"") == "thing"
        assert testc.process_quotes("commented  # 1 23 ") == "commented"

        assert testc.process_quotes("\"commented  1\"# 1 23 ") == "commented  1"
        assert testc.process_quotes("\"commented\\s  1\"# 1 23 ") == "commenteds  1"

        # pass'word
        assert testc.process_quotes("pass'word") == "pass'word"

        # pass"word
        assert testc.process_quotes('pass"word') == 'pass"word'

        ### Escape special characters in quotes/ticks
        # "commented\s\1"
        assert testc.process_quotes(r'"commented\s\1"') == "commenteds1"

        # "back \ slash"
        assert testc.process_quotes(r'"back \\ slash"') == r"back \ slash"

        # "some " thing"
        assert testc.process_quotes(r'"some \" thing"') == r'some " thing'

        # "some \" thing"
        assert testc.process_quotes(r'"some \\\" thing"') == r'some \" thing'

        # "some ' thing"
        assert testc.process_quotes("\"some \' thing\"") == "some ' thing"

        # 'commented\s\1'
        assert testc.process_quotes(r"'commented\s\1'") == "commenteds1"

        # 'back \ slash'
        assert testc.process_quotes(r"'back \\ slash'") == r"back \ slash"

        # 'some " thing'
        assert testc.process_quotes(r"'some \" thing'") == r'some " thing'

        # tick' mark
        assert testc.process_quotes(r"'tick\' mark'") == "tick' mark"

        # Te!st"\pas\s
        assert testc.process_quotes(r'"Te!st\"\\pas\\s"') == r'Te!st"\pas\s'

        ### Bad Cases
        assert testc.process_quotes(r'"input with "unescaped quote"') == "input with "
        assert testc.process_quotes(r'"input with \ backslash"') == "input with  backslash"

    def test_parse_line(self):
        testm = Metadata()
        testm.settings["option"] = MetadataSettings(StrProcessor)
        testc = ConfigFile("file", metadata = testm)

        key, val = testc.parse_line("  option      # whiteout entry, updated by fa_piaware_config in settings")
        assert key == "option"
        assert val == ""

        key, val = testc.parse_line("  option   \"yes\"    # updated by fa_piaware_config in settings")
        assert key == "option"
        assert val == "yes"

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

        key, val = testc.parse_line("option \"   yes   \"")
        assert key == "option"
        assert val == "   yes   "

        key, val = testc.parse_line("   option \"   yes   \" # comment")
        assert key == "option"
        assert val == "   yes   "

        key, val = testc.parse_line(r'   option " \  yes   " # comment')
        assert key == "option"
        assert val == "   yes   "

        key, val = testc.parse_line(r'   option \  yes  # comment')
        assert key == "option"
        assert val == r"\  yes"

        key, val = testc.parse_line(r'   option \ " y"es " # comment')
        assert key == "option"
        assert val == r'\ " y"es "'

    def test_parse_config_from_list(self):
        testm = Metadata()
        testm.settings["test"] = MetadataSettings(IntegerProcessor, deprecated=True)

        test_cases = [
            {
                "config": [
                    "wireless-netmask 255.255.255.0",
                    "doesnt_exist nothing"
                ],
                "raises_error": True,
                "error_type": ValueError
            },
            {
                "config": [
                    "wireless-netmask 255.255.255.0",
                    "test nothing"
                ],
                "raises_error": True,
                "error_type": ValueError
            },
            {
                "config": [
                    "wireless-netmask 255.255.255.0",
                    "rfkill not_bool"
                ],
                "raises_error": True,
                "error_type": ValueError
            }
        ]

        for test in test_cases:
            f = ConfigFile("file", metadata = testm)
            if test["raises_error"]:
                with self.assertRaises(test["error_type"]):
                    f.parse_config_from_list(test["config"])

        f = ConfigFile("file", metadata = Metadata())
        f.parse_config_from_list([
            "wireless-netmask 255.255.255.0",
            "rfkill",
            "image-type image",
            "adaptive-min-gain -12.12",
            "adept-serverhosts test.usa.flightaware.com",
            "use-gpsd yes",
            "slow-cpu auto",
            "priority 1",
            "allow-ble-setup yes"
        ])
        assert f.get("wireless-netmask") == "255.255.255.0"
        assert f.get("rkfill") is None
        assert f.get("image-type") == "image"
        assert f.get("adaptive-min-gain") == -12.12
        assert f.get("adept-serverhosts") == "test.usa.flightaware.com"
        assert f.get("use-gpsd") is True
        assert f.get("slow-cpu") == "auto"
        assert f.get("priority") == 1
        assert f.get("allow-ble-setup") == "yes"

class TestConfigGroup(unittest.TestCase):

    def default_config_data(self):
        return ["image-type image", "adaptive-min-gain -1"]

    def test_config_group(self):

        f1 = ConfigFile(filename="file1", priority=30, metadata = Metadata())
        f1.read_config_into_list = mock.Mock(return_value=self.default_config_data())

        f2 = ConfigFile(filename="file2", priority=40, metadata = Metadata())
        f2.read_config_into_list = mock.Mock(return_value=["image-type image_2", "adaptive-min-gain -2", "wired-network no"])

        cfg = ConfigGroup(metadata=Metadata(), files=[f1, f2])
        cfg.load_configs()

        assert cfg.files[0]._priority == 40
        assert cfg.files[1]._priority == 30
        assert cfg.get("image-type") == "image_2"
        assert cfg.get("wired-network") is False
        assert cfg.get("wireless-network") is False

    def three_files(self):
        files = [
            ConfigFile(filename="file1", priority=30, metadata = Metadata()),
            ConfigFile(filename="file2", priority=40, metadata = Metadata()),
            ConfigFile(filename="file3", priority=50, metadata = Metadata())
        ]

        for f in files:
            f.read_config_into_list = self.default_config_data

        return files

    def test_config_group_whiteout(self):
        f1, f2, f3 = self.three_files()

        uat = "uat-receiver-port"
        f3.values[uat] = WHITEOUT
        f2.values[uat] = 10000

        cfg = ConfigGroup(metadata=Metadata(), files=[f1, f2, f3])
        cfg.load_configs()

        assert cfg.get(uat) == 30978

        f3.values[uat] = 10000
        f2.values[uat] = WHITEOUT

        assert cfg.get(uat) == 10000

    def test_config_group_get_val_no_default(self):
        f1, f2, f3 = self.three_files()

        cfg = ConfigGroup(metadata=Metadata(), files=[f1, f2, f3])
        cfg.load_configs()

        assert cfg.get("http-proxy-host") is None

    def test_create_standard_piaware_config_group(self):
        cfg = create_standard_piaware_config_group()
        assert cfg.files[0]._priority == 50
        assert cfg.files[1]._priority == 40
        assert cfg.files[2]._priority == 30