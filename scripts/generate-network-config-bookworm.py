from piaware_config import get_standard_config_group, ConfigGroup
from uuid import uuid4
import subprocess
import os

SYS_CON_DIR = "/etc/NetworkManager/system-connections"
FIRSTBOOT_PATH = "/run/firstboot"

def wireless_conn_file_template(new_uuid: str, ssid: str, psk: str):
    return f"""[connection]
    id=wireless
    uuid={new_uuid}
    type=wifi

    [wifi]
    mode=infrastructure
    ssid={ssid}

    [wifi-security]
    key-mgmt=wpa-psk
    psk={psk}

    [ipv4]
    method=auto

    [ipv6]
    addr-gen-mode=default
    method=auto

    [proxy]"""

def generate_network_config(config: ConfigGroup):
    if config.get("wired-network"):
        print("wired-network set to yes")
    else:
        print("wired-network set to no")
        subprocess.run(["nmcli", "con", "down", "eth0"])

    if not config.get("wireless-network"):
        print("wireless-network set to no")
        subprocess.run(["nmcli","con","down","wireless"])
        subprocess.run(["nmcli", "radio", "wifi", "off"])
        return

    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        new_uuid = uuid4()
        ssid = config.get("wireless-ssid")
        psk = config.get("wireless-password")

        conn_file.write(wireless_conn_file_template(new_uuid, ssid, psk))
    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wireless.nmconnection"])
    subprocess.run(["sync"])

    if not os.path.exists(FIRSTBOOT_PATH):
        print("Upping wireless")
        subprocess.run(["nmcli", "radio", "wifi", "on"])
        subprocess.run(["nmcli", "con", "up", "wireless"])
        with open(FIRSTBOOT_PATH, "w") as f:
            f.write("Used by generate-network-config-bookworm.py to determine if it's being run for the first time after a bootup.")
    
def main(dryrun=False, extra_file_path: str = None):
    
    config_group = get_standard_config_group(extra_file_path)
    generate_network_config(config_group)

if __name__ == "__main__":
    main()
