from piaware_config import get_standard_config_group, ConfigGroup
from uuid import uuid4
import subprocess
import os

SYS_CON_DIR = "/etc/NetworkManager/system-connections"
FIRSTBOOT_PATH = "/run/firstboot"

def format_dns(dns_string: str) -> str:
    names = dns_string.strip(" \n\t")
    names = names.split(" ")
    formatted = ";".join(names) + ";"
    return formatted

def wireless_conn_file_template(new_uuid: str, config: ConfigGroup):
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

    ip = """
[ipv4]
    """
    if config.get("wireless-type") == "static":
        static_ip = config.get("wireless-address") + "/" + config.get("wireless-netmask")
        gateway = config.get("wireless-gateway")
        name_servers = format_dns(config.get("wireless-nameservers"))

        if gateway is not None:
            static_ip += f",{gateway}"
        ip += f"""
address1={static_ip}
dns={name_servers}
method=manual
            """
    else:
        ip += """
method=auto
        """

    ip += """
[ipv6]
addr-gen-mode=default
method=auto

[proxy]
        """
    file += ip
    return file

def generate_network_config(config: ConfigGroup):
    if not config.get("wireless-network"):
        print("wireless-network set to no")
        subprocess.run(["nmcli", "radio", "wifi", "off"])
        return

    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        new_uuid = uuid4()
        conn_file.write(wireless_conn_file_template(new_uuid, config))

    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wireless.nmconnection"])
    subprocess.run(["sync"])

    print("Upping wireless")
    subprocess.run(["nmcli", "radio", "wifi", "on"])
    subprocess.run(["nmcli", "con", "up", "wireless"])
    
def main(dryrun=False, extra_file_path: str = None):
    config_group = get_standard_config_group(extra_file_path)
    generate_network_config(config_group)

if __name__ == "__main__":
    main()
