from unittest import mock
import os
import io
import unittest
from flightaware_piaware_config.piaware_config import *
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

        with self.assertRaises(KeyError):
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

    def test_str_processor(self):
        s = StrProcessor
        for testcase in [ '',              # empty string
                          'abcd',          # regular ASCII
                          'abcd\u0000', ]: # non-printable ASCII
            with self.subTest(testcase=testcase):
                self.assertTrue(s.validate(testcase))
                self.assertEqual(s.parse(testcase), testcase)

        for testcase in [ 'abcd\u0099',    # refuse bytes > 127
                          'abcd\u11FF', ]: # refuse out of range unicode code points
            with self.subTest(testcase=testcase):
                self.assertFalse(s.validate(testcase))

    def test_bytes_processor(self):
        bp = BytesProcessor
        for value, expected in [ ('',           b''),                # empty string
                                 ('abcd',       b'abcd'),            # regular ASCII
                                 ('abcd\u0000', b'abcd\x00'),        # non-printable ASCII
                                 ('abcd\u0099', b'abcd\x99'), ]:     # bytes >127
            with self.subTest(value=value, expected=expected):
                self.assertTrue(bp.validate(value))
                self.assertEqual(bp.parse(value), expected)

        self.assertFalse(bp.validate('abcd\u11FF'))  # refuse out of range unicode code points

    def test_parse_value(self):
        testm = Metadata()
        assert testm.parse_value("image-type", "test_type") == "test_type"
        assert testm.parse_value("manage-config", "no") == False
        assert testm.parse_value("priority", "1") == 1
        assert testm.parse_value("adaptive-min-gain", "1.2") == 1.2
        assert testm.parse_value("force-macaddress", "01:23:45:67:89:AB") == "01:23:45:67:89:AB"
        assert testm.parse_value("feeder-id", "e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c") == UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
        assert testm.parse_value("rtlsdr-gain", "-10") == "max"

        with self.assertRaises(KeyError):
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

        with self.assertRaises(KeyError):
            testm.validate_value("test", "dne")

class TestConfigParser(unittest.TestCase):
    def test_parse_value(self):
        # a test wrapper around parse_config_value to capture any calls
        # to the warning function and return a "saw warning" flag as
        # part of the returned tuple
        def _parse(line):
            saw_warning = None
            def warn(msg: str):
                nonlocal saw_warning
                saw_warning = msg
            result = parse_config_value(line, warn)
            return result, saw_warning

        # input -> expected result (no warnings)
        testcases = [
            # Unquoted values
            ("", ""),                           # Empty value
            ("thing", "thing"),                 # Unquoted value
            ("thing  ", "thing"),               # Unquoted value with trailing whitespace
            ("thing  # comment", "thing"),      # Unquoted value with trailing comment
            ("th\\ing", "th\\ing"),             # Unquoted value with escape that should be ignored
            ("th\\'ing", "th\\'ing"),           # Unquoted value with escape that should be ignored
            ("th\\x37ing", "th\\x37ing"),       # Unquoted value with escape that should be ignored
            ("M\u00FCnchen", "M\u00FCnchen"),   # Unquoted value with iso-8859-1 passthrough

            # Double-quoted values
            ('"thing"', "thing"),               # Quoted value
            ('"  thing"', "  thing"),           # Quoted value with quoted leading whitespace
            ('"thing"  ', "thing"),             # Quoted value with unquoted trailing whitespace
            ('"thing  "', "thing  "),           # Quoted value with quoted trailing whitespace
            ('"thing # abc"', "thing # abc"),   # Quoted value with embedded comment char
            ('"thing"  # abc', "thing"),        # Quoted value with trailing comment
            ('"th\'ing"', "th'ing"),            # Doublequoted value with embedded unescaped single quote
            ('"M\u00FCnchen"', "M\u00FCnchen"), # Quoted value with iso-8859-1 passthrough

            # Single-quoted values
            ("'thing'", 'thing'),               # Quoted value
            ("'  thing'", '  thing'),           # Quoted value with quoted leading whitespace
            ("'thing'  ", 'thing'),             # Quoted value with unquoted trailing whitespace
            ("'thing  '", 'thing  '),           # Quoted value with quoted trailing whitespace
            ("'thing # abc'", "thing # abc"),   # Quoted value with embedded comment char
            ("'thing'  # abc", 'thing'),        # Quoted value with trailing comment
            ("'th\"ing'", 'th"ing'),            # Singlequoted value with embedded unescaped doublequote
            ('"M\u00FCnchen"', 'M\u00FCnchen'), # Quoted value with iso-8859-1 passthrough

            # Escape sequences
            ('"thi\\\\ng"',  "thi\\ng"),        # \\ -> \ escape
            ('"thi\\\'ng"',  "thi\'ng"),        # \' -> ' escape
            ('"thi\\"ng"',   'thi"ng'),         # \" -> " escape
            ('"thi\\x37ng"', 'thi7ng'),         # \x37 -> chr(0x37) hex escape
            ('"thi\\x87ng"', 'thi\u0087ng'),    # \x87 -> chr(0x87) hex escape
        ]

        for value, expected in testcases:
            with self.subTest(value=value, expected=expected):
                result, warning = _parse(value)
                self.assertEqual(result, expected)
                self.assertIsNone(warning)

        # malformed input -> expected result (with a warning)
        warning_testcases = [
            ('"quoted', "quoted"),             # Doublequoted string with no terminating quote
            ('"quoted" abc', "quoted"),        # Doublequoted string with trailing non-comment garbage

            ("'quoted", "quoted"),             # Singlequoted string with no terminating quote
            ("'quoted' abc", "quoted"),        # Singlequoted string with trailing non-comment garbage

            ("'quoted\\", "quoted\\"),         # Single backslash at end of line (not interpreted as a continuation!)
            ("'quoted\\xAZ'", "quoted\\xAZ"),  # Non-hex \x sequence
            ("'quoted\\x-A'", "quoted\\x-A"),  # Negative hex \x sequence
            ("'quoted\\x'", "quoted\\x"),      # Truncated \x sequence
            ("'quoted\\q'", "quoted\\q"),      # Unknown escape
        ]

        for value, expected in warning_testcases:
            with self.subTest(value=value, expected=expected):
                result, warning = _parse(value)
                self.assertEqual(result, expected)
                self.assertIsNotNone(warning)


    def test_parse_line(self):
        # a test wrapper around parse_config_line to capture any calls
        # to the warning function and return a "saw warning" flag as
        # part of the returned tuple
        def _parse(line):
            saw_warning = None
            def warn(msg: str):
                nonlocal saw_warning
                saw_warning = msg
            result = parse_config_line(line, warn)
            return result, saw_warning

        # input, expected_keyvalue, expected_warning
        testcases = [ ("",                   None, False),         # empty line
                      ("    # commented",    None, False),         # empty line with comment

                      ("  option      # whiteout entry, updated by fa_piaware_config in settings", ("option", ""),    False),
                      ("  option   \"yes\"    # updated by fa_piaware_config in settings",         ("option", "yes"), False),

                      # simple option values
                      ("option ",            ("option", ""),    False),   # whiteout
                      ("option #abc",        ("option", ""),    False),   # whiteout with trailing comment
                      ("option yes",         ("option", "yes"), False),   # simple value
                      ("option   yes  ",     ("option", "yes"), False),   # simple value with whitespace to strip
                      ("option   yes # abc", ("option", "yes"), False),   # simple value with trailing comment

                      # quoted option values using double-quote
                      ('option "yes"',          ("option", "yes"), False),     # simplest case
                      ('option ""',             ("option", ""),    False),     # whiteout
                      ('option "yes"   ',       ("option", "yes"), False),     # trailing whitespace, ignored
                      ('option "yes"  # abc ',  ("option", "yes"), False),     # trailing comment
                      ('option "yes"  abc',     ("option", "yes"), True),      # trailing garbage (with warning)
                      ('option "  yes"',        ("option", "  yes"), False),   # leading whitespace within value
                      ('option "yes  "',        ("option", "yes  "), False),   # trailing whitespace within value
                      ('option "yes',           ("option", "yes"), True),      # unclosed quote (with warning)
                      ('option "ab \\" cd"',    ("option", 'ab " cd'), False), # escaped quote
                      ('option "ab \' cd"',     ("option", "ab ' cd"), False), # unescaped single quote
                      
                      # quoted option values using single-quote
                      ("option 'yes'",          ('option', 'yes'), False),     # simplest case
                      ("option ''",             ('option', ''), False),        # whiteout
                      ("option 'yes'   ",       ('option', 'yes'), False),     # trailing whitespace, ignored
                      ("option 'yes'  # abc ",  ('option', 'yes'), False),     # trailing comment
                      ("option 'yes'  abc",     ('option', 'yes'), True),      # trailing garbage (with warning)
                      ("option '  yes'",        ('option', '  yes'), False),   # leading whitespace within value
                      ("option 'yes  '",        ('option', 'yes  '), False),   # trailing whitespace within value
                      ("option 'yes",           ('option', 'yes'), True),      # unclosed quote (with warning)
                      ("option 'ab \\' cd'",    ('option', "ab ' cd"), False), # escaped quote
                      ("option 'ab \" cd'",     ('option', 'ab " cd'), False), # unescaped double quote
                     ]

        for input, expected_keyvalue, expected_warning in testcases:
            with self.subTest(input=input, expected_keyvalue=expected_keyvalue, expected_warning=expected_warning):
                keyvalue, warning = _parse(input)
                if expected_warning:
                    self.assertIsNotNone(warning)
                else:
                    self.assertIsNone(warning)
                self.assertEqual(keyvalue, expected_keyvalue)

class TestConfigFile(unittest.TestCase):
    def test_read_config_into_list(self):
        test_input = io.BytesIO(b"""image-type image
adaptive-min-gain -1
manage-config 1232
adept-serverport 2
adept-serverport 5
wireless-netmask 255.255.255.0
adept-serverhosts test.usa.flightaware.com
use-gpsd
wireless-ssid M\xFCnchen
""")

        
        f = ConfigFile("test.txt")
        f._open = lambda: test_input
        f.warn = lambda lineno,msg: None

        l = f.read_config_into_list()
        self.assertEqual(l, [
            "image-type image",
            "adaptive-min-gain -1", 
            "manage-config 1232",
            "adept-serverport 2",
            "adept-serverport 5",
            "wireless-netmask 255.255.255.0",
            "adept-serverhosts test.usa.flightaware.com",
            "use-gpsd",
            "wireless-ssid M\u00FCnchen"
        ])

    def test_parse_config_from_list(self):
        testm = Metadata()

        warning_test_cases = [
            # unknown option
            [ "doesnt_exist nothing" ],
            # deprecated option
            [ "wireless-broadcast 192.168.1.255" ],
            # invalid option value
            [ "rfkill not_bool" ],
            # duplicated option
            [ "rfkill yes",
              "rfkill no" ]
        ]

        for testcase in warning_test_cases:
            f = ConfigFile("file", metadata = testm)

            # patch in a replacement for ConfigFile.warn()
            saw_warning = None
            def capture_warning(lineno, msg):
                nonlocal saw_warning
                saw_warning = msg
            f.warn = capture_warning

            f.parse_config_from_list(testcase)
            self.assertIsNotNone(saw_warning)

        # various value tests:
        #   line, key, expected value for key
        testcases = [
            ("wireless-netmask 255.255.255.0", "wireless-netmask", "255.255.255.0"),
            ("image-type image", "image-type", "image"),
            ("adaptive-min-gain -12.12", "adaptive-min-gain", -12.12),
            ("adept-serverhosts test.usa.flightaware.com", "adept-serverhosts", "test.usa.flightaware.com"),
            ("use-gpsd yes", "use-gpsd", True),
            ("slow-cpu auto", "slow-cpu", "auto"),
            ("priority 1", "priority", 1),
            ("allow-ble-setup yes", "allow-ble-setup", "yes"),
            ("wireless-ssid M\u00FCnchen", "wireless-ssid", b"M\xFCnchen"),
            ("wireless-ssid 'M\\xFCnchen'", "wireless-ssid", b"M\xFCnchen")
        ]
            
        for line, key, expected in testcases:
            with self.subTest(line=line, key=key, expected=expected):
                f = ConfigFile("file", metadata = Metadata())

                # patch in a replacement for ConfigFile.warn()
                saw_warning = None
                def capture_warning(lineno, msg):
                    nonlocal saw_warning
                    saw_warning = msg
                f.warn = capture_warning

                f.parse_config_from_list([line])
                
                self.assertEqual(f.get(key), expected)
                self.assertIsNone(saw_warning)

        # whiteout test (with is, not equal)
        f = ConfigFile("file", metadata = Metadata())
        f.parse_config_from_list(["rfkill"])
        self.assertIs(f.get("rfkill"), WHITEOUT)

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
