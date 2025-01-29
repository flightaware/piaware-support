from unittest import mock
from unittest.mock import Mock
from ipaddress import NetmaskValueError
import os
import unittest
import importlib  
import sys
sys.path.append("./scripts/")


def import_bookworm():
    from importlib.machinery import SourceFileLoader
    import importlib.util
    loader = SourceFileLoader("generate_network_config_bookworm", "./scripts/generate_network_config_bookworm")

    spec = importlib.util.spec_from_loader("generate_network_config_bookworm", loader)
    generate_network_config_bookworm = importlib.util.module_from_spec(spec)
    sys.modules["generate_network_config_bookworm"] = generate_network_config_bookworm
    spec.loader.exec_module(generate_network_config_bookworm)

    return generate_network_config_bookworm


generate_network_config_bookworm = import_bookworm()
from generate_network_config_bookworm import *
from scripts.piaware_config import *
import uuid

wired_template = """
[connection]
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

[proxy]
"""

wireless_template = """
[connection]
id=wireless
uuid=e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c
type=wifi
autoconnect=false

[wifi]
mode=infrastructure
ssid=jukka

[wifi-security]
key-mgmt=wpa-psk
psk=sirasti

[ipv4]
{}

[ipv6]
addr-gen-mode=default
method=auto

[proxy]
"""

mock_ifaces = """
    inet 127.0.0.1/8 scope host lo
    inet 192.168.1.86/24 brd 192.168.1.255 scope global dynamic noprefixroute wlan0
    inet 192.168.1.42/12 brd 192.168.255.255 scope global noprefixroute eth0

"""

mock_ifaces_no_wlan0 = """
    inet 127.0.0.1/8 scope host lo
    inet 192.168.1.42/12 brd 192.168.255.255 scope global noprefixroute eth0

"""

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
        c = Mock()
        c.get = Mock(side_effect=[None])
        with self.assertRaises(ValueError):
            check_address("wireless", c)
        
        c.get = Mock(side_effect=["192.123"])
        with self.assertRaises(ValueError):
            check_address("s", c)

        c.get = Mock(side_effect=["2001:db8:3333:4444:5555:6666:7777:8888"])
        with self.assertRaises(ValueError):
            check_address("s", c)

    def test_get_netmask(self):
        c = Mock()

        test_cases = [
            {
                "se": ["255.255.255.0"],
                "ex": "255.255.255.0"
            },
            {
                "se": [None, "0.0.0.0"],
                "ex": "255.0.0.0"
            },
            {
                "se": [None, "128.0.0.0"],
                "ex": "255.255.0.0"
            },
            {
                "se": [None, "192.0.0.0"],
                "ex": "255.255.255.0"
            },
        ]

        for t in test_cases:
            c.get = Mock(side_effect=t["se"])
            nm = get_netmask("wireless", c)
            assert nm == t["ex"]

    def test_configure_static_network(self):
        enable_g = False
        enable_dns = False

        def get(k):
            if k == "wireless-address":
                return "192.111.1.42"
            elif k == "wireless-netmask":
                return "255.255.255.0"
            elif k == "wireless-gateway" and enable_g:
                return "192.111.1.33"
            elif k == "wireless-nameservers" and enable_dns:
                return "8.8.8.8"
            else:
                return None

        c = Mock()
        c.get = Mock(side_effect=get)
        network = configure_static_network("wireless", c)
        assert network == "address1=192.111.1.42/24\n"

        enable_g = True
        network = configure_static_network("wireless", c)
        assert network == "address1=192.111.1.42/24,192.111.1.33\n"

        enable_dns = True
        network = configure_static_network("wireless", c)
        assert network == "address1=192.111.1.42/24,192.111.1.33\ndns=8.8.8.8;\n"

        with self.assertRaises(NetmaskValueError):
            c.get = Mock(side_effect=["192.111.1.42", "255.255", "255.255"])
            network = configure_static_network("wireless", c)

    def mock_uuid():
        return uuid.UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)

    def mock_csn(*args):
        return "sample_ip\n"

    @mock.patch("generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
    @mock.patch("generate_network_config_bookworm.uuid4", side_effect=mock_uuid)
    def test_get_wired_conn_file(self, uuid_mock, csn_mock):
        def get(k):
            if k == "wired-type":
                return "static"
            else:
                return None
        c = Mock()
        c.get = Mock(side_effect=get)
        template = get_wired_conn_file(c)
        assert template == wired_template.format("sample_ip\nmethod=manual")

        csn_mock.side_effect = ValueError("test")
        with self.assertRaises(ValueError):
            get_wired_conn_file(c)

        def get(k):
            if k == "wired-type":
                return "dhcp"
        c.get = Mock(side_effect=get)
        template = get_wired_conn_file(c)
        assert template == wired_template.format("method=auto")

    @mock.patch("generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
    @mock.patch("generate_network_config_bookworm.uuid4", side_effect=mock_uuid)
    def test_get_wireless_conn_file(self, uuid_mock, csn_mock):
        def get(k):
            if k == "wireless-type":
                return "static"
            elif k == "wireless-ssid":
                return "jukka"
            elif k == "wireless-password":
                return "sirasti"
            else:
                return None
        c = Mock()
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        assert template == wireless_template.format("sample_ip\nmethod=manual")

        csn_mock.side_effect = ValueError("test")
        with self.assertRaises(ValueError):
            template = get_wireless_conn_file(c)

        def get(k):
            if k == "wireless-type":
                return "NetworkManager"
            elif k == "wireless-ssid":
                return "jukka"
            elif k == "wireless-password":
                return "sirasti"
        c.get = Mock(side_effect=get)
        template = get_wireless_conn_file(c)
        assert template == wireless_template.format("method=auto")
    
    def test_calculate_brd_by_hand(self):
        brd = calculate_brd_by_hand("192.168.1.24", 8)
        assert brd == "192.255.255.255"
        brd = calculate_brd_by_hand("192.168.1.24", 16)
        assert brd == "192.168.255.255"
        brd = calculate_brd_by_hand("192.168.1.24", 24)
        assert brd == "192.168.1.255"
        brd = calculate_brd_by_hand("192.168.1.24", 31)
        assert brd == "192.168.1.25"

    @mock.patch("generate_network_config_bookworm.calculate_brd_by_hand")
    @mock.patch("generate_network_config_bookworm.print")
    @mock.patch("generate_network_config_bookworm.get_netmask")
    def test_verify_broadcast_address(self, net_mask_mock, print_mock, calculate_brd_by_hand_mock):
        c = Mock()
        c.get = Mock(side_effect=[None])
        verify_broadcast_address("wireless", c)
        calculate_brd_by_hand_mock.assert_not_called()
        assert c.get.call_count == 1

        c.get = Mock(side_effect=["192.111.1.255", None, None])
        verify_broadcast_address("wireless", c)
        calculate_brd_by_hand_mock.assert_not_called()
        assert c.get.call_count == 2

        c.get = Mock(side_effect=["192.111.255.255", "192.111.1.42"])
        net_mask_mock.side_effect = ["255.255.0.0"]
        calculate_brd_by_hand_mock.side_effect = ["192.111.255.255"]
        print_mock.reset_mock()
        assert verify_broadcast_address("wireless", c) == True
        calculate_brd_by_hand_mock.assert_called()
        assert print_mock.call_count == 1

        c.get = Mock(side_effect=["192.111.255.255", "192.111.1.42"])
        calculate_brd_by_hand_mock.side_effect = ["not equal"]
        net_mask_mock.side_effect = ["255.255.255.0"]
        print_mock.reset_mock()
        assert verify_broadcast_address("wireless", c) == False
        calculate_brd_by_hand_mock.assert_called()
        assert print_mock.call_count == 2
