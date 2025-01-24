"""
    This file is a re-write of https://github.com/flightaware/piaware/blob/master/package/fa_piaware_config.tcl.
    It reads from the three default config files to obtain various settings for the piaware machine.
"""

from uuid import UUID
import re
import os

PIAWARE_CONFIG_ENUMS = {}
PIAWARE_CONFIG_ENUMS["country"] = [ "AD","AE","AF","AG","AI","AL","AM","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE",
                                    "BF","BG","BH","BI","BJ","BL","BM","BN","BO","BQ","BR","BS","BT","BV","BW","BY","BZ","CA","CC","CD",
                                    "CF","CG","CH","CI","CK","CL","CM","CN","CO","CR","CU","CV","CW","CX","CY","CZ","DE","DJ","DK","DM",
                                    "DO","DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ","FK","FM","FO","FR","GA","GB","GD","GE","GF",
                                    "GG","GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT","GU","GW","GY","HK","HM","HN","HT","HU","ID",
                                    "IE","IL","IM","IN","IO","IQ","IR","IS","IT","JE","JM","JO","JP","KE","KG","KH","KI","KM","KN","KP",
                                    "KR","KW","KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT","LU","LV","LY","MA","MC","MD","ME","MF",
                                    "MG","MH","MK","ML","MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC",
                                    "NE","NF","NG","NI","NL","NO","NP","NR","NU","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PN",
                                    "PR","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SD","SE","SG","SH","SI","SJ",
                                    "SK","SL","SM","SN","SO","SR","SS","ST","SV","SX","SY","SZ","TC","TD","TF","TG","TH","TJ","TK","TL",
                                    "TM","TN","TO","TR","TT","TV","TW","TZ","UA","UG","UM","US","UY","UZ","VA","VC","VE","VG","VI","VN",
                                    "VU","WF","WS","YE","YT","ZA","ZM","ZW","00"]

PIAWARE_CONFIG_ENUMS["receiver"] = ["rtlsdr", "sdr", "bladerf", "beast", "relay", "radarcape", "radarcape-local", "other", "none"]
PIAWARE_CONFIG_ENUMS["uat_receiver"] = ["sdr", "stratuxv3", "other", "none"]
PIAWARE_CONFIG_ENUMS["network_type"] = ["static", "dhcp"]
PIAWARE_CONFIG_ENUMS["slow_cpu"] = ["yes", "no", "auto"]
PIAWARE_CONFIG_ENUMS["network_config_style"] = ["default", "buster", "jessie"]
PIAWARE_IMAGE_CONF = "/usr/share/piaware-support/piaware-image-config.txt"
PIAWARE_CONF = "/etc/piaware.conf"
BOOT_PIAWARE_CONF = "/boot/firmware/piaware-config.txt"

def check_enums(setting_type: str, value: str) -> bool:
    if setting_type in PIAWARE_CONFIG_ENUMS and value in PIAWARE_CONFIG_ENUMS[setting_type]:
        return True
    else:
        return False

class MetadataSettings():
    def __init__(self, default: any = None, setting_type: str = None, protect: str = None, sdonly: bool = None, network: str = None, ignore_list = []) -> None:
        self.default = default
        self.setting_type = setting_type
        self.protect = protect
        self.sdonly = sdonly
        self.network = network
        self.ignore_list = ignore_list

class Metadata():
    settings: MetadataSettings = {
        "priority" : MetadataSettings(setting_type="int"),
        "image-type" : MetadataSettings(setting_type="str"),
        "manage-config" : MetadataSettings(setting_type="bool", default=False),
        "feeder-id" : MetadataSettings(setting_type="UUID"),
        "force-macaddress" : MetadataSettings(setting_type="MAC"),
        "allow-auto-updates" : MetadataSettings(setting_type="bool", default=False),
        "allow-manual-updates" : MetadataSettings(setting_type="bool", default=False),
        "network-config-style" : MetadataSettings(setting_type="network_config_style", default="default", sdonly=True, network=True),
        "wired-network" : MetadataSettings(setting_type="bool", default=True, sdonly=True, network=True),
        "wired-type" : MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wired-address" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wired-netmask" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        # Setting broadcast address directly through boot/firmare/piaware-config.txt has been deprecated.
        "wired-broadcast" : MetadataSettings(sdonly=True, network=True, setting_type="str", ignore_list=[BOOT_PIAWARE_CONF]),
        "wired-gateway" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wired-nameservers" : MetadataSettings(default= "8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),
        "wireless-network" : MetadataSettings(setting_type="bool", default=False, sdonly=True, network=True),
        "wireless-ssid" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wireless-password" : MetadataSettings(protect=True, sdonly=True, network=True, setting_type="str"),
        "wireless-type" : MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wireless-address" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wireless-broadcast" : MetadataSettings(sdonly=True, network=True, setting_type="str", ignore_list=[BOOT_PIAWARE_CONF]),
        "wireless-netmask" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wireless-gateway" : MetadataSettings(sdonly=True, network=True, setting_type="str"),
        "wireless-nameservers" : MetadataSettings(default = "8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),
        "wireless-country" : MetadataSettings(default = "00", setting_type="country", sdonly=True, network=True),
        "allow-dhcp-duic" : MetadataSettings(default=True, setting_type="bool", sdonly=True, network=True),
        "http-proxy-host" : MetadataSettings(network=True),
        "http-proxy-port" : MetadataSettings(network=True),
        "http-proxy-user" : MetadataSettings(network=True),
        "http-proxy-password" : MetadataSettings(protect=True, network=True),
        "adept-serverhosts" : MetadataSettings(), # Come back to this
        "adept-serverport" : MetadataSettings(setting_type="int", default=1200),
        "rfkill" : MetadataSettings(setting_type="bool", default=False, sdonly=True),
        "receiver-type" : MetadataSettings(setting_type="receiver", default="rtlsdr"),
        "rtlsdr-device-index" : MetadataSettings(default=False, sdonly=True),
        "rtlsdr-ppm" : MetadataSettings(setting_type = "int", default = 0, sdonly=True),
        "rtlsdr-gain" : MetadataSettings(setting_type = "gain", default = "max", sdonly=True),
        "beast-baudrate" : MetadataSettings(setting_type = "int", sdonly=True),
        "radarcape-host" : MetadataSettings(sdonly = True),
        "receiver-port" : MetadataSettings(setting_type = "int", default = 30005),
        "allow-modeac" : MetadataSettings(setting_type = "bool", default = True, sdonly=True),
        "allow-mlat" : MetadataSettings(setting_type = "bool", default = True),
        "mlat-results" : MetadataSettings(setting_type = "bool", default = True),
        "mlat-results-anon" : MetadataSettings(setting_type = "bool", default = True),
        "mlat-results-format" : MetadataSettings(default = "beast,connect,localhost:30104 beast,listen,30105 ext_basestation,listen,30106"),
        "slow-cpu" : MetadataSettings(default = "auto", sdonly = True),
        "adaptive-dynamic-range" : MetadataSettings(setting_type="bool", default = True, sdonly=True),
        "adaptive-dynamic-range-target" : MetadataSettings(setting_type="double", sdonly=True),
        "adaptive-burst" : MetadataSettings(setting_type="bool", default=False, sdonly=True),
        "adaptive-min-gain" : MetadataSettings(setting_type="double", sdonly=True),
        "adaptive-max-gain" : MetadataSettings(setting_type="double", sdonly=True),
        "enable-firehose" : MetadataSettings(setting_type="bool", default = False),
        "allow-ble-setup" : MetadataSettings(default = "auto", sdonly = True),
        "uat-receiver-type" : MetadataSettings(setting_type = "uat_receiver", default=None),
        "uat-receiver-host" : MetadataSettings(),
        "uat-receiver-port" : MetadataSettings(setting_type = "int", default = 30978),
        "uat-sdr-gain" : MetadataSettings(setting_type = "gain", default = "max", sdonly = True),
        "uat-sdr-ppm" : MetadataSettings(setting_type = "double", default = 0, sdonly = True),
        "uat-sdr-device" : MetadataSettings(default = "driver=rtlsdr", sdonly = True),
        "use-gpsd" : MetadataSettings(setting_type="bool", default = True)
    }

    def get_setting(self, setting_key: str) -> MetadataSettings:
        if setting_key in self.settings:
            return self.settings[setting_key]
        print(f"Could not find {setting_key} in settings")
        return None

    def convert_str_to_bool(self, val: str) -> bool:
        if val.lower() == "yes":
            return True
        elif val.lower() == "no":
            return False

    def convert_str_to_uuid(self, val: str , version = 4) -> UUID:
        return UUID(val, version=version)
    
    def convert_str_to_gain(self, val) -> str | float:
        val = val.lower()
        if (isinstance(val, str) and val == "max") or (self.validate_int(val) and int(val) <= -10):
            return "max"
        elif self.validate_int(val):
            return int(val)
        else:
            return float(val)
    
    def convert_value(self, key, val) -> any:
        setting = self.settings[key]
        t = setting.setting_type

        if check_enums(t, val):
            return val
            
        match t:
            case "str":
                return val

            case "bool":
                return self.convert_str_to_bool(val)

            case "int":
                return int(val)

            case "double":
                return float(val)

            case "MAC":
                return val

            case "UUID":
                return self.convert_str_to_uuid(val)

            case "gain":
                return self.convert_str_to_gain(val)

            case _:
                raise TypeError(f"Cannot convert unrecognized type {t} for {key}, {val}")

    def validate_bool(self, val: str) -> bool:
        val = val.lower()
        if val == "yes" or val == "no":
            return True
        else:
            return False


    def validate_int(self, val: str) -> bool:
        try: 
            int(val)
        except ValueError:
            return False
        else:
            return True

    def validate_double(self, val: str) -> bool:
        try: 
            float(val)
        except ValueError:
            return False
        else:
            return True

    def validate_mac(self, val: str) -> bool:
        val = val.lower()
        m = re.fullmatch("^[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}$", val)
        if m is None:
            return False
        
        if m.start() == 0 and m.end() == len(val):
            return True
        else:
            return False

    def validate_uuid(self, val: str, version=4) -> bool:
        try:
            uuid_obj = UUID(val, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == val

    def validate_gain(self, val: str) -> bool:
        return self.validate_double(val) or (isinstance(val, str) and val == "max")

    def validate_value(self, key, val) -> bool:
        setting = self.settings[key]
        t = setting.setting_type

        if check_enums(t, val):
            return  True
            
        match t:
            case "str":
                return True

            case "bool":
                return self.validate_bool(val)

            case "int":
                return self.validate_int(val)

            case "double":
                return self.validate_double(val)

            case "MAC":
                return self.validate_mac(val)

            case "UUID":
                return self.validate_uuid(val)

            case "gain":
                return self.validate_gain(val)

            case _:
                raise TypeError(f"Cannot validate Unrecognized type {t} from {key}, {val}")

            
class ConfigFile():
    def __init__(self, filename: str, metadata: Metadata = None, priority: int =0, readonly: bool = True) -> None:
        self._metadata = metadata
        self._priority = priority
        self._readonly = readonly
        self._filename = filename
        self.values = {}
    
    def process_quotes(self, line: str) -> str:
        if len(line) == 0:
            return line

        if line[0] != "\"" and line[0] != "'":
            comment_index = line.find("#")
            if comment_index == -1:
                return line
            else:
                return line[0:comment_index].strip()

        val = ""
        esc = False
        for i in range(1, len(line)):
            char = line[i]
            if esc:
                val += char
                esc = False
                continue

            if char == "\"" or char == "'":
                break

            if char == "\\":
                esc = True
                continue

            val += char
        return val.strip()


    def parse_line(self, line) -> tuple | None:
        if re.search(r"^\s*#.*", line):
            return None

        if re.search(r"^\s*([a-zA-Z0-9_-]+)\s*(?:#.*)?$", line):
            return (line.strip(), "")

        option_line = re.search(r"^\s*([a-zA-Z0-9_-]+)\s+(.+)$", line)
        if option_line:
            return (option_line.group(1), self.process_quotes(option_line.group(2)))

        return None

    def get(self, setting_key: str) -> any:
        if setting_key in self.values:
            return self.values[setting_key]
        else:
            return None

    def read_config(self) -> None:

        if not os.path.isfile(self._filename):
            print(f"{self._filename} does not exist.")
            return
        try:
            with open(self._filename, "r") as config:
                values = {}
                for idx, line in enumerate(config):
                        l = self.parse_line(line)

                        if not l:
                            continue
                        
                        key, val = l
                        key = key.lower()
                        setting = self._metadata.get_setting(key)
                        if setting is None:
                            print(f"{self._filename}:{idx}: unrecognized option {key}")
                            continue

                        if self._filename in setting.ignore_list:
                            print(f"{self._filename}:{idx}: option {key} has {self._filename} in its ignore_list")
                            continue
                        
                        if val != "":
                            if not self._metadata.validate_value(key, val):
                                print(f"{self._filename}:{idx}: invalid value for option {key}:{val}")
                                continue

                            if key in values:
                                print(f"{self._filename}:{idx}: {key} overrides an existing instance of {key}")

                            values[key] = val
                for k, v in values.items():
                    self.values[k] = self._metadata.convert_value(k, v)
                        
        except Exception as e:
            print(f"Something went wrong while reading config file {self._filename}: {e}")

class ConfigGroup():
    files: list[ConfigFile]
    _metadata: Metadata

    def __init__(self, metadata: Metadata = None, files: list[ConfigFile] = None) -> None:
        if files is None:
            self.files = []
        else:
            self.files = files
        self._metadata = metadata

    def reorder_files_in_priority(self):
        self.files = sorted(self.files, key=lambda x: x._priority, reverse=True)
    
    def read_configs(self):
        for file in self.files:
            file.read_config()
        
        if len(self.files) > 0:
            self.reorder_files_in_priority()
        else:
            print(f"No files to sort for ConfigGroup")

    def get(self, setting_key: str) -> any:
        for file in self.files:
            val = file.get(setting_key)
            if val is not None:
                return val
        
        return self._metadata.get_setting(setting_key).default

# Create a standard piaware config group from these 3 default locations.
# Create ConfigFile objects and reorder them based on priority.
def create_standard_piaware_config_group(extra_file_path: str = None) -> ConfigGroup:
    files = []
    f = ConfigFile(filename=PIAWARE_IMAGE_CONF, priority=30, metadata = Metadata())
    files.append(f)

    if extra_file_path is not None:
        f = ConfigFile(filename=extra_file_path, priority=100, metadata = Metadata())
        files.append(f)
    else:
        f1 = ConfigFile(filename=PIAWARE_CONF, priority=40, metadata = Metadata())
        f2 = ConfigFile(filename=BOOT_PIAWARE_CONF, priority=50, metadata = Metadata())

        files.append(f1)
        files.append(f2)
    
    return ConfigGroup(files=files, metadata = Metadata())

# Get standard config group.
# Validate and read in the values.
def get_standard_config_group(extra_file_path: str = None) -> ConfigGroup():
    cg = create_standard_piaware_config_group(extra_file_path=extra_file_path)
    cg.read_configs()
    return cg

