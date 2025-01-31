from unittest import mock
from unittest.mock import Mock
from ipaddress import NetmaskValueError
import os
import unittest
import importlib  
import sys
sys.path.append("./flightaware_piaware_config/src/flightaware_piaware_config/")

from generate_network_config_bookworm import *
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
                "se": ["128.1.1.1", None],
                "ex": 16
            },
            {
                "se": [address, None],
                "ex": 24
            },
        ]

        for t in test_cases:
            nm = get_prefix(*t["se"])
            assert nm == t["ex"]
        with self.assertRaises(NetmaskValueError):
            get_prefix(address, "2221ds")

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

    @mock.patch("generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
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

    @mock.patch("generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
    def test_get_wireless_conn_file(self, csn_mock):
        c = Mock()

        valid_netmask = "255.255.255.0"
        def get(k):
            if k == "wireless-type":
                return "static"
            elif k == "wireless-ssid":
                return "jukka"
            elif k == "wireless-password":
                return "sirasti"
            elif k == "wireless-address":
                return "192.1.1.1"
            elif k == "wireless-netmask":
                return return_netmask
            else:
                return None
        c.get = Mock(side_effect=get)
        return_netmask = valid_netmask
        template = get_wireless_conn_file(c)
        assert template == wireless_template.format(f"{self.mock_csn()[0]}\nmethod=manual")

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

    @mock.patch("generate_network_config_bookworm.print")
    def test_verify_broadcast_address(self, print_mock):
        c = Mock()
        c.get = Mock(side_effect=[None])
        verify_broadcast_address("wireless", c)
        print_mock.assert_not_called()
        assert c.get.call_count == 1

        c.get = Mock(side_effect=["192.111.1.255", None])
        verify_broadcast_address("wireless", c)
        print_mock.assert_called_with("Tried to verify broadcast address, but static IP was not set.")
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
