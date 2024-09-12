from piaware_config import generate_from_args

def wireless_conn_file_template(new_uuid: str, psk: str, ssid: str):
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

def generate_network_config():
    with open("/etc/NetworkManager/system-connections", "w") as conn_file:
        conn_file.write()

def main(dryrun=False):
    
    config_group = generate_from_args()

main()
