from piaware_config import get_standard_config_group, ConfigGroup
import subprocess

def main():
    try:
        subprocess.run(["nmcli", "con", "up", "wired"])
    except Exception as e:
        print(f"{e} occured when trying to activate wired network. Check your ethernet connection")

    c = get_standard_config_group()
    if c.get("wireless-network"):
        print("wireless-network set to yes. Enabling...")
        subprocess.run(["nmcli", "radio", "wifi", "on"])
        subprocess.run(["nmcli", "con", "up", "wireless"])
    else:
        print("wireless-network set to no. Disabling...")
        subprocess.run(["nmcli", "radio", "wifi", "off"])

if __name__ == "__main__":
    main()