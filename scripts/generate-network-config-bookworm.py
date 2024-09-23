from piaware_config import generate_from_args, ConfigGroup
from uuid import uuid4
import subprocess

SYS_CON_DIR = "/etc/NetworkManager/system-connections"

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

    if not config.get("wireless-network"):
        return

    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        new_uuid = uuid4()
        ssid = config.get("wireless-ssid")
        psk = config.get("wireless-password")

        conn_file.write(wireless_conn_file_template(new_uuid, ssid, psk))
    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wireless.nmconnection"])
    subprocess.run(["sync"])
    
def main(dryrun=False, extra_file_path: str = None):
    
    config_group = generate_from_args()
    generate_network_config(config_group)

main()
