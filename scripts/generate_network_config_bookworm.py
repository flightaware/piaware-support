from piaware_config import get_standard_config_group, ConfigGroup
from uuid import uuid4
import subprocess
import os

SYS_CON_DIR = "/etc/NetworkManager/system-connections"

def format_dns(dns_string: str) -> str:
    names = dns_string.strip(" \n\t")
    names = names.split(" ")
    formatted = ";".join(names) + ";"
    return formatted

def check_address_and_netmask_set(network_type: str, config: ConfigGroup):
    if config.get(f"{network_type}-address") is None:
        raise ValueError(f"{network_type}-type was set to static but address was not set")
    if config.get(f"{network_type}-netmask") is None:
        raise ValueError(f"{network_type}-type was set to static but netmask was not set")

def configure_static_network(network_type: str, config: ConfigGroup):
    check_address_and_netmask_set(network_type, config)

    ip = ""
    static_ip = config.get(f"{network_type}-address") + "/" + config.get(f"{network_type}-netmask")
    gateway = config.get(f"{network_type}-gateway")
    if gateway is not None:
        static_ip += f",{gateway}"
    ip += f"address1={static_ip}\n"

    name_servers = config.get(f"{network_type}-nameservers")
    if name_servers is not None:
        ip += f"dns={format_dns(name_servers)}\n"
    return ip

def wired_conn_file_template(config: ConfigGroup):
    new_uuid = uuid4()
    file = f"""
[connection]
id=wired
uuid={new_uuid}
type=ethernet
autoconnect-priority=999
interface-name=eth0

[ethernet]
"""
    ipv4 = """
[ipv4]
"""
    if config.get("wired-type") == "static":
        try:
            ipv4 += configure_static_network("wired", config)
            ipv4 += "method=manual\n"
        except ValueError:
            ipv4 += "method=auto\n"
    else:
        ipv4 += "method=auto\n"
    file += ipv4
    file += """
[ipv6]
addr-gen-mode=default
method=auto

[proxy]
"""

    return file

def wireless_conn_file_template(config: ConfigGroup):
    new_uuid = uuid4()
    ssid = config.get("wireless-ssid")
    psk = config.get("wireless-password")

    file = f"""
[connection]
id=wireless
uuid={new_uuid}
type=wifi

[wifi]
mode=infrastructure
ssid={ssid}

[wifi-security]
key-mgmt=wpa-psk
psk={psk}
"""

    ipv4 = """
[ipv4]
"""
    if config.get("wireless-type") == "static":
        try:
            ipv4 += configure_static_network("wireless", config)
            ipv4 += f"method=manual\n"
        except ValueError:
            ipv4 += "method=auto\n"
    else:
        ipv4 += "method=auto\n"

    ipv4 += """
[ipv6]
addr-gen-mode=default
method=auto

[proxy]
"""
    file += ipv4
    return file

def generate_wired_network_config(config: ConfigGroup):
    with open(f"{SYS_CON_DIR}/wired.nmconnection", "w") as conn_file:
        conn_file.write(wired_conn_file_template(config))

    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wired.nmconnection"])
    subprocess.run(["sync"])

    print("Created wired connection")
    subprocess.run(["nmcli", "con", "up", "wired"])


def generate_wireless_network_config(config: ConfigGroup):
    if not config.get("wireless-network"):
        print("wireless-network set to no")
        subprocess.run(["nmcli", "radio", "wifi", "off"])
        return

    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        conn_file.write(wireless_conn_file_template(config))

    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wireless.nmconnection"])
    subprocess.run(["sync"])

    print("Upping wireless")
    subprocess.run(["nmcli", "radio", "wifi", "on"])
    subprocess.run(["nmcli", "con", "up", "wireless"])
    
def main(dryrun=False, extra_file_path: str = None):
    config_group = get_standard_config_group(extra_file_path)
    generate_wired_network_config(config_group)
    generate_wireless_network_config(config_group)

if __name__ == "__main__":
    main()
