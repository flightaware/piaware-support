from piaware_config import get_standard_config_group, ConfigGroup
from uuid import uuid4
import subprocess
import os

SYS_CON_DIR = "/etc/NetworkManager/system-connections"

def get_broadcast_address():
    ips = subprocess.run(["ip", "addr", "show"], capture_output=True)
    ips = ips.stdout.decode("utf-8")
    ips = ips.split("\n")
    x = 0
    for index, line in enumerate(ips):
        if "wlan0" in line:
            x = index
            break

    for line in ips[x:]:
        if "inet" in line:
            line = line.strip()
            line = line.split(" ")
            for index, l in enumerate(line):
                if l == "brd":
                    return line[index + 1]
    return None

# We're calculating broadcast address for an ipv4 address.
# Hence the magic number 32. Ipv4 addresses are 32 bits.
def calculate_brd_by_hand(addr: str, nm: int) -> str:
    values = addr.split(".")
    binaries = [f"{int(v):08b}" for v in values]
    full_bin = list("".join(binaries))
    for i in range(32 - nm):
        full_bin[i + nm] = "1"

    cur = ""
    base_10_val = []
    for index, i in enumerate(full_bin):
        cur += i

        if (index + 1) % 8 == 0 and index > 0:
            base_10_val.append(f"{(int(cur, 2))}")
            cur = ""

    ba = ".".join(base_10_val)
    return ba

def verify_broadcast_address(network: str,config: ConfigGroup) -> bool:
    print("Verifying broadcast address")
    addr = config.get(f"{network}-address")
    nm = config.get(f"{network}-netmask")

    if addr is None or nm is None:
        print(f"Addr: {addr}, Netmask: {nm}")
        return False

    if nm > 32:
        print("Netmask cannot be greater than 32. Stopping brd verification...")
        return False
    calculated_ba = calculate_brd_by_hand(addr, nm)
    assigned_ba = get_broadcast_address()
    if assigned_ba is None:
        print("Could not find brd address")
    elif assigned_ba == calculated_ba:
        print(f"The assigned brd address {assigned_ba} looks good")
    else:
        print(f"Warning: the brd address that we've calculated {calculated_ba} is different than the assigned one {assigned_ba}")

    return assigned_ba == calculated_ba

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
    static_ip = config.get(f"{network_type}-address") + "/" + str(config.get(f"{network_type}-netmask"))
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


def generate_wireless_network_config(config: ConfigGroup):
    if not config.get("wireless-network"):
        print("wireless-network set to no")
        return

    with open(f"{SYS_CON_DIR}/wireless.nmconnection", "w") as conn_file:
        conn_file.write(wireless_conn_file_template(config))

    subprocess.run(["chmod", "600", f"{SYS_CON_DIR}/wireless.nmconnection"])
    subprocess.run(["sync"])
    
def main(dryrun=False, extra_file_path: str = None):
    config_group = get_standard_config_group(extra_file_path)
    generate_wired_network_config(config_group)
    generate_wireless_network_config(config_group)
    verify_broadcast_address("wireless", config_group)
    verify_broadcast_address("wired", config_group)

if __name__ == "__main__":
    main()
