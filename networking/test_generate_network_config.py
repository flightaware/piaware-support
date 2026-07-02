from unittest import mock
from unittest.mock import Mock
from ipaddress import NetmaskValueError
import os
import unittest
import importlib  
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../flightaware_piaware_config/src/flightaware_piaware_config/"))

from generate_network_config import *
import uuid

wired_template = """[connection]
id=wired
uuid=e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c
type=ethernet
autoconnect-priority=999
interface-name=eth0
autoconnect=false
[ethernet]
[ipv4]
{}
[ipv6]
addr-gen-mode=default
method=auto
[proxy]"""

wireless_template = """[connection]
id=wireless
uuid=acc6cf97-9575-4f41-ad85-65af044288df
type=wifi
autoconnect={}
[wifi]
mode=infrastructure
ssid={}
[wifi-security]
key-mgmt=wpa-psk
psk={}
[ipv4]
{}
[ipv6]
addr-gen-mode=default
method=auto
[proxy]"""

class TestCases(unittest.TestCase):
    def test_format_dns(self):
        val = "8.8.8.8;8.8.4.4;"
        ret = format_dns("     \n 8.8.8.8 8.8.4.4      \t  ")
        assert ret == val

        ret = format_dns("8.8.8.8 8.8.4.4")
        assert ret == val

        ret = format_dns("   8.8.8.8  \n  8.8.4.4  ")
        assert ret == val

    def test_check_address(self):
        with self.assertRaises(ValueError):
            check_address(None, "wireless")
        
        with self.assertRaises(ValueError):
            check_address(None, "wireless")

        with self.assertRaises(ValueError):
            check_address("2001:db8:3333:4444:5555:6666:7777:8888", "wireless")

        try:
            check_address("192.1.1.1", "wireless")
        except Exception as e:
            assert False, f"check_address raised exception {e}"

    def test_get_prefix(self):
        c = Mock()
        address = "192.1.1.1"
        test_cases = [
            {
                "se": [address, "255.255.255.0"],
                "ex": 24
            },
            {
                "se": ["0.0.0.0", None],
                "ex": 8
            },
            {
                "se": ["10.0.0.0", None],
                "ex": 8
            },
            {
                "se": ["124.0.0.0", None],
                "ex": 8
            },
            {
                "se": ["127.0.0.0", None],
                "ex": 8
            },
            {
                "se": ["128.1.1.1", None],
                "ex": 16
            },
            {
                "se": ["154.1.1.1", None],
                "ex": 16
            },
            {
                "se": ["191.1.1.1", None],
                "ex": 16
            },
            {
                "se": [address, None],
                "ex": 24
            },
            {
                "se": ["200.1.1.1", None],
                "ex": 24
            },
            {
                "se": ["223.1.1.1", None],
                "ex": 24
            },
        ]

        for n, t in enumerate(test_cases):
            with self.subTest(n=n, t=n):
                nm = get_prefix(*t["se"])
                self.assertEqual(nm, t["ex"])

        with self.assertRaises(NetmaskValueError):
            get_prefix(address, "2221ds")

        with self.assertRaises(NetmaskValueError):
            get_prefix(address, "192.1")

        with self.assertRaises(ValueError):
            get_prefix("255.1.1.1", None)

    def test_escape_string_for_network_manager(self):
        testcases = [
            ("", ""),                   # empty string
            ("abc", "abc"),             # simplest case
            ("abc def", "abc def"),     # embedded whitespace
            ("abc   ", "abc   "),       # trailing whitespace
            ("   abc", r"\s  abc"),     # leading whitespace (must avoid it getting stripped)
            ("abc\\def", "abc\\\\def"), # backslash
            ("abc\ndef", "abc\\ndef"),  # embedded LF
            ("abc\rdef", "abc\\rdef"),  # embedded CR
            ("abc\tdef", "abc\\tdef"),  # embedded tab
        ]

        for unescaped, expected in testcases:
            with self.subTest(unescaped=unescaped, expected=expected):
                self.assertEqual(escape_string_for_network_manager(unescaped), expected)

    def test_escape_ssid_for_network_manager(self):
        testcases = [
            (b"", ""),                  # empty SSID

            # pure ascii cases
            (b'\x61\x62\x63',             r'abc'),      # simplest case
            (b'\x20\x20',                 r'\s '),      # whitespace only
            (b'\x5c',                     r'\\'),       # one backslash
            (b'\x5c\x5c',                 r'\\\\'),     # two backslashes
            (b'\x22',                     r'"'),        # ascii doublequote
            (b'\x5c\x78\x34\x30',         r'\\x40'),    # \x40 (4 bytes, not an escape sequence)
            (b'\x5c\x75\x30\x30\x34\x30', r'\\u0040'),  # \u0040 (6 bytes, not an escape sequence)
            (b'\x5c\x78\x41\x5a',         r'\\xAZ'),    # \xAZ (4 bytes, not an escape sequence)
            (b'\x5c\x75\x41\x5a\x42\x5a', r'\\uAZBZ'),  # \uAZBZ (6 bytes, not an escape sequence)
            (b'\x20\x61\x62\x63\x20',     r'\sabc '),   # leading/trailing whitespace
            (b'\x33\x31\x33\x30\x33\x31\x33\x42', r'3130313B'),  # SSID that could be interpreted as hex bytes

            # cases that require decimal-byte-list encoding
            (b'\x00\x00\x00\x00', "0;0;0;0;"),                                         # all NULs
            (b'\x0d\x0a', "13;10;"),                                                   # CR LF
            (b'\xe2\x80\x9c\xe2\x80\x9d', "226;128;156;226;128;157;"),                 # U+201C U+201D (“”), UTF-8 encoding
            (b'\xe2\x80\x98\xe2\x80\x99', "226;128;152;226;128;153;"),                 # U+2018 U+2019 (‘’), UTF-8 encoding
            (b'\x4D\xC3\xBC\x6E\x63\x68\x65\x6E', "77;195;188;110;99;104;101;110;"),   # München, UTF-8 encoding
            (b'\x4D\xFC\x6E\x63\x68\x65\x6E', "77;252;110;99;104;101;110;"),           # München, ISO-8859-1 encoding
            (b'\xF0\x9F\x98\x80', "240;159;152;128;"),                                 # U+1F600 GRINNING FACE, UTF-8 encoding
            (b'\x31\x30\x30\x3b', "49;48;48;59;"),                                     # 100; (4 bytes, not a decimal-byte-list)
        ]

        for ssid_bytes, expected in testcases:
            with self.subTest(ssid_bytes=ssid_bytes, expected=expected):
                self.assertEqual(escape_ssid_for_network_manager(ssid_bytes), expected)

    def test_configure_static_network(self):
        address = "192.111.1.42"
        gateway = "192.111.1.33"
        nameservers = "8.8.8.8 8.8.4.4"
        netmask = "255.255.255.0"

        test_cases = [
            {
                "test": [address, None, None, netmask],
                "ex": [[f"address1={address}/24"], 1]
            },
            {
                "test": [address, gateway, None, netmask],
                "ex": [[f"address1={address}/24,{gateway}"], 1]
            },
            {
                "test": [address, gateway, nameservers, netmask],
                "ex": [[f"address1={address}/24,{gateway}", "dns=8.8.8.8;8.8.4.4;"], 2]
            },
        ]

        for t in test_cases:
            network = configure_static_network(*t["test"])
            for n, ex in zip(network, t["ex"][0]):
                assert n == ex
            assert len(network) == t["ex"][1]

        with self.assertRaises(NetmaskValueError):
            configure_static_network("192.111.1.42", None, None, "255.255")

    def mock_csn(*args):
        return ["sample_ip/24"]

    @mock.patch("generate_network_config.configure_static_network", side_effect=mock_csn)
    def test_get_wired_conn_file(self, csn_mock):
        def get(k):
            if k == "wired-type":
                return "static"
            elif k == "wired-address":
                return "192.1.1.1"
            elif k == "wired-netmask":
                return "255.255.255.0"
            else:
                return None
        c = Mock()
        c.get = Mock(side_effect=get)
        template = get_wired_conn_file(c)
        assert template == wired_template.format(f"{self.mock_csn()[0]}\nmethod=manual")

        def get(k):
            if k == "wired-type":
                return "dhcp"
        c.get = Mock(side_effect=get)
        template = get_wired_conn_file(c)
        assert template == wired_template.format("method=auto")

    @mock.patch("generate_network_config.configure_static_network", side_effect=mock_csn)
    def test_get_wireless_conn_file_when_enabled(self, csn_mock):
        c = Mock()

        valid_netmask = "255.255.255.0"
        def get(k):
            if k == "wireless-network":
                return True
            elif k == "wireless-type":
                return "static"
            elif k == "wireless-ssid":
                return b"jukka"
            elif k == "wireless-password":
                return "sirasti"
            elif k == "wireless-address":
                return "192.1.1.1"
            elif k == "wireless-netmask":
                return valid_netmask
            else:
                return None
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        self.assertEqual(template, wireless_template.format("true", "jukka", "sirasti", f"{self.mock_csn()[0]}\nmethod=manual"))

        def get(k):
            if k == "wireless-network":
                return True
            elif k == "wireless-type":
                return "NetworkManager"
            elif k == "wireless-ssid":
                return b"jukka"
            elif k == "wireless-password":
                return "sirasti"
            else:
                return None
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        self.assertEqual(template, wireless_template.format("true", "jukka", "sirasti", "method=auto"))

        def get(k):
            if k == "wireless-network":
                return True
            elif k == "wireless-type":
                return "NetworkManager"
            elif k == "wireless-password":
                return "sirasti"
            else:
                return None
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        self.assertEqual(template, wireless_template.format("false", "", "", "method=auto"))
    
    @mock.patch("generate_network_config.configure_static_network", side_effect=mock_csn)
    def test_get_wireless_conn_file_when_disabled(self, csn_mock):
        c = Mock()

        valid_netmask = "255.255.255.0"
        def get(k):
            if k == "wireless-network":
                return False
            elif k == "wireless-type":
                return "static"
            elif k == "wireless-ssid":
                return b"jukka"
            elif k == "wireless-password":
                return "sirasti"
            elif k == "wireless-address":
                return "192.1.1.1"
            elif k == "wireless-netmask":
                return valid_netmask
            else:
                return None
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        self.assertEqual(template, wireless_template.format("false", "", "", f"{self.mock_csn()[0]}\nmethod=manual"))

        def get(k):
            if k == "wireless-network":
                return False
            elif k == "wireless-type":
                return "NetworkManager"
            elif k == "wireless-ssid":
                return b"jukka"
            elif k == "wireless-password":
                return "sirasti"
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        self.assertEqual(template, wireless_template.format("false", "", "", "method=auto"))
    

    def test_calculate_brd_by_hand(self):
        brd = calculate_brd_by_hand("192.168.1.24", 8)
        assert brd == "192.255.255.255"
        brd = calculate_brd_by_hand("192.168.1.24", 16)
        assert brd == "192.168.255.255"
        brd = calculate_brd_by_hand("192.168.1.24", 24)
        assert brd == "192.168.1.255"
        brd = calculate_brd_by_hand("192.168.1.24", 31)
        assert brd == "192.168.1.25"

    @mock.patch("generate_network_config.print")
    def test_verify_broadcast_address(self, print_mock):
        c = Mock()
        c.get = Mock(side_effect=[None])
        verify_broadcast_address("wireless", c)
        print_mock.assert_not_called()
        assert c.get.call_count == 1

        c.get = Mock(side_effect=["192.111.1.255", None])
        verify_broadcast_address("wireless", c)
        print_mock.assert_called_with("Tried to verify wireless broadcast address, but static IP was not set.")
        assert print_mock.call_count == 1
        assert c.get.call_count == 2

        c.get = Mock(side_effect=["192.111.255.255", "192.111.1.42", "255.255.0.0"])
        print_mock.reset_mock()
        verify_broadcast_address("wireless", c)
        assert print_mock.call_count == 0
        assert c.get.call_count == 3

        c.get = Mock(side_effect=["192.111.255.255", "192.111.1.42", "255.0.0.0"])
        print_mock.reset_mock()
        verify_broadcast_address("wireless", c)
        print_mock.assert_called_with(f"Warning: the brd address that we've calculated: 192.255.255.255 is different than the one you've assigned: 192.111.255.255.")
        assert print_mock.call_count == 1
        assert c.get.call_count == 3
