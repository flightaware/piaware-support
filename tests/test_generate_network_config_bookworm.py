
from unittest import mock
from unittest.mock import Mock
import os
import unittest
import importlib  
import sys
sys.path.append("./scripts/")

from scripts.generate_network_config_bookworm import *
from scripts.piaware_config import *
import uuid

wired_template = """
[connection]
id=wired
uuid=e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c
type=ethernet
autoconnect-priority=999
interface-name=eth0

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

    def test_check_address_and_netmask_set(self):

        def get(k):
            if k == "wireless-address":
                return None
            elif k == "wireless-netmask":
                return None
            else:
                return True

        c = Mock()
        c.get = Mock(side_effect=get)
        with self.assertRaises(ValueError):
            check_address_and_netmask_set("wireless", c)
        
        check_address_and_netmask_set("s", c)

    def test_configure_static_network(self):
        enable_g = False
        enable_dns = False

        def get(k):
            if k == "wireless-address":
                return "192.111.1.42"
            elif k == "wireless-netmask":
                return 24
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

    def mock_uuid():
        return uuid.UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)

    def mock_csn(*args):
        return "sample_ip\n"

    @mock.patch("scripts.generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
    @mock.patch("scripts.generate_network_config_bookworm.uuid4", side_effect=mock_uuid)
    def test_wired_conn_file_template(self, uuid_mock, csn_mock):
        def get(k):
            if k == "wired-type":
                return "static"
            else:
                return None
        c = Mock()
        c.get = Mock(side_effect=get)
        template = wired_conn_file_template(c)
        assert template == wired_template.format("sample_ip\nmethod=manual")

        csn_mock.side_effect = ValueError("test")
        template = wired_conn_file_template(c)
        assert template == wired_template.format("method=auto")

        def get(k):
            if k == "wired-type":
                return "NetworkManager"
        c.get = Mock(side_effect=get)
        template = wired_conn_file_template(c)
        assert template == wired_template.format("method=auto")

    @mock.patch("scripts.generate_network_config_bookworm.configure_static_network", side_effect=mock_csn)
    @mock.patch("scripts.generate_network_config_bookworm.uuid4", side_effect=mock_uuid)
    def test_wireless_conn_file_template(self, uuid_mock, csn_mock):
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
        template = wireless_conn_file_template(c)
        assert template == wireless_template.format("sample_ip\nmethod=manual")

        csn_mock.side_effect = ValueError("test")
        template = wireless_conn_file_template(c)
        assert template == wireless_template.format("method=auto")

        def get(k):
            if k == "wireless-type":
                return "NetworkManager"
            elif k == "wireless-ssid":
                return "jukka"
            elif k == "wireless-password":
                return "sirasti"
        c.get = Mock(side_effect=get)
        template = wireless_conn_file_template(c)
        assert template == wireless_template.format("method=auto")

    @mock.patch("scripts.generate_network_config_bookworm.subprocess.run")
    def test_get_broadcast_address(self, run_mock):
        mock = Mock()
        mock.stdout = Mock()

        mock2 = Mock()
        mock2.stdout.decode = Mock(return_value=mock_ifaces)
        run_mock.side_effect = [mock, mock2]
        brd = get_broadcast_address("wlan0")
        assert brd == "192.168.1.255"

        run_mock.side_effect = [mock, mock2]
        brd = get_broadcast_address("wlan1230")
        assert brd is None

        run_mock.side_effect = [mock, mock2]
        brd = get_broadcast_address("eth0")
        assert brd == "192.168.255.255"

        exc = ValueError("test")
        run_mock.side_effect = exc
        brd = get_broadcast_address("eth0")
        assert brd is None
    
    def test_calculate_brd_by_hand(self):
        brd = calculate_brd_by_hand("192.168.1.24", 8)
        assert brd == "192.255.255.255"

        brd = calculate_brd_by_hand("192.168.1.24", 16)
        assert brd == "192.168.255.255"

        brd = calculate_brd_by_hand("192.168.1.24", 24)
        assert brd == "192.168.1.255"

        brd = calculate_brd_by_hand("192.168.1.24", 31)
        assert brd == "192.168.1.25"

    @mock.patch("scripts.generate_network_config_bookworm.get_broadcast_address")
    def test_verify_broadcast_address(self, get_broadcast_address_mock ):
        get_broadcast_address_mock.side_effect = [None, "192.111.1.255", "2"]

        def get(k):
            if k == "wireless-address":
                return "192.111.1.42"
            elif k == "wireless-netmask":
                return 45

        c = Mock()
        c.get = Mock(side_effect=get)

        resp = verify_broadcast_address("wireless", c)
        assert resp is False

        def get(k):
            if k == "wireless-address":
                return "192.111.1.42"
            elif k == "wireless-netmask":
                return 24

        c = Mock()
        c.get = Mock(side_effect=get)

        resp = verify_broadcast_address("wireless", c)
        assert resp is False

        resp = verify_broadcast_address("wireless", c)
        assert resp is True

        resp = verify_broadcast_address("wireless", c)
        assert resp is False