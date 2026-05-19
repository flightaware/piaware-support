#!/usr/bin/env python3

from piaware_config import get_standard_config_group, ConfigGroup
from uuid import UUID
import subprocess
import os
import stat
import ipaddress

SYS_CON_DIR = "/etc/NetworkManager/system-connections"

def calculate_brd_by_hand(address: str, netmask: str) -> str:
    return format(ipaddress.IPv4Network(f"{address}/{netmask}", strict=False).broadcast_address)

def verify_broadcast_address(network: str, config: ConfigGroup) -> bool:
    assigned_ba = config.get(f"{network}-broadcast")
    if not assigned_ba:
        return
    address = config.get(f"{network}-address")
    if address is None:
        print(f"Tried to verify broadcast address, but static IP was not set.")
        return

    nm = get_prefix(address, config.get(f"{network}-netmask"))
    calculated_ba = calculate_brd_by_hand(address, nm)

    if assigned_ba != calculated_ba:
        print(f"Warning: the brd address that we've calculated: {calculated_ba} is different than the one you've assigned: {assigned_ba}.")

def format_dns(dns_string: str) -> str:
    names = dns_string.split()
    formatted = ";".join(names) + ";"
    return formatted

def check_address(address: str, network_type: str):
    if address is None:
        raise ValueError(f"{network_type}-type was set to static but {network_type}-address was not set")
    address = ipaddress.ip_address(address)

    if address.version != 4:
        raise ValueError(f"{network_type}-address needs an ipv4 address")

def get_prefix(address: str, netmask: str) -> int:
    if netmask is None:
        address = ipaddress.ip_address(address)
        first_byte = address.packed[0]
        if (first_byte >> 7) == 0b0:
            return 8
        elif (first_byte >> 6) == 0b10:
            return 16
        elif (first_byte >> 5) == 0b110:
            return 24
        else:
            raise ValueError(f"Cannot calculate default subnet prefix for ipaddress {address}")
        
    return ipaddress.IPv4Network('0.0.0.0/' + netmask).prefixlen

def configure_static_network(address: str, gateway: str, name_servers: str, netmask: str) -> str:
    prefix = str(get_prefix(address, netmask))
    ip = []
    static_ip = f"{address}/{prefix}"
    if gateway is not None:
        static_ip += f",{gateway}"
    ip.append(f"address1={static_ip}")

    if name_servers is not None:
        ip.append(f"dns={format_dns(name_servers)}")

    return ip

def get_wired_conn_file(config: ConfigGroup):
    uuid = UUID("e8a2fe66-8ecd-4b91-b6d5-7700a6fe3e1c", version=4)
    connect = "true" if config.get("wired-network") else "false"

    file = [
        "[connection]",
        "id=wired",
        f"uuid={uuid}",
        "type=ethernet",
        "autoconnect-priority=999",
        "interface-name=eth0",
        f"autoconnect={connect}",
        "[ethernet]",
        "[ipv4]"
    ]
    ipv4 = []
    if config.get("wired-type") == "static":
        address = config.get("wired-address")
        gateway = config.get("wired-gateway")
        nameservers = config.get("wired-nameservers")
        netmask = config.get("wired-netmask")

        check_address(address, "wired")

        ipv4.extend(configure_static_network(address, gateway, nameservers, netmask))
        ipv4.append("method=manual")

    else:
        ipv4.append("method=auto")

    file.extend(ipv4)
    ipv6 = [
        "[ipv6]",
        "addr-gen-mode=default",
        "method=auto",
        "[proxy]"
    ]

    file.extend(ipv6)

    return '\n'.join(file)

def escape_backslashes_for_network_manager(value: str) -> str:
    return value.replace("\\", "\\\\")

def get_wireless_conn_file(config: ConfigGroup):
    uuid = UUID("acc6cf97-9575-4f41-ad85-65af044288df", version=4)
    ssid = config.get("wireless-ssid")
    psk = config.get("wireless-password")
    connect = "true" if config.get("wireless-network") else "false"

    ssid = escape_backslashes_for_network_manager(ssid)
    psk = escape_backslashes_for_network_manager(psk)

    file = [
        "[connection]",
        "id=wireless",
        f"uuid={uuid}",
        "type=wifi",
        f"autoconnect={connect}",
        "[wifi]",
        "mode=infrastructure",
        f"ssid={ssid}",
        "[wifi-security]",
        "key-mgmt=wpa-psk",
        f"psk={psk}",
        "[ipv4]",
    ]
    ipv4 = []
    if config.get("wireless-type") == "static":
        address = config.get("wireless-address")
        gateway = config.get("wireless-gateway")
        nameservers = config.get("wireless-nameservers")
        netmask = config.get("wireless-netmask")
        check_address(address, "wireless")

        ipv4.extend(configure_static_network(address, gateway, nameservers, netmask))
        ipv4.append("method=manual")
    else:
        ipv4.append("method=auto")
    file.extend(ipv4)
    
    ipv6 = [    
        "[ipv6]",
        "addr-gen-mode=default",
        "method=auto",
        "[proxy]"
    ]
    file.extend(ipv6)
    return '\n'.join(file)

def generate_wired_network_config(config: ConfigGroup):
    with open(f"{SYS_CON_DIR}/wired.nmconnection", "w") as conn_file:
        conn_file.write(get_wired_conn_file(config))

    os.chmod(f"{SYS_CON_DIR}/wired.nmconnection", stat.S_IRUSR | stat.S_IWUSR)

def generate_wireless_network_config(config: ConfigGroup):
    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        conn_file.write(get_wireless_conn_file(config))

    os.chmod(f"{SYS_CON_DIR}/wireless.nmconnection", stat.S_IRUSR | stat.S_IWUSR)
    
def run(dryrun=False, extra_file_path: str = None):
    config_group = get_standard_config_group(extra_file_path)
    generate_wired_network_config(config_group)
    generate_wireless_network_config(config_group)
    verify_broadcast_address("wireless", config_group)
    verify_broadcast_address("wired", config_group)

if __name__ == "__main__":
    run()