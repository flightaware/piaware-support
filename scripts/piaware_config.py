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
PIAWARE_CONFIG_ENUMS["network_config_style"] = ["sdr", "stratuxv3", "other", "none"]
PIAWARE_CONFIG_ENUMS["network_type"] = ["static", "dhcp"]
PIAWARE_CONFIG_ENUMS["slow_cpu"] = ["yes", "no", "auto"]


def check_enums(setting_type: str, value: str) -> bool:
    if setting_type in PIAWARE_CONFIG_ENUMS and value in PIAWARE_CONFIG_ENUMS[setting_type]:
        return True
    else:
        return False


class MetadataSettings():
    def __init__(self, default: any = None, setting_type: str = None, protect: str = None, sdonly: bool = None, network: str = None) -> None:
        self.default = default
        self.setting_type = setting_type
        self.protect = protect
        self.sdonly = sdonly
        self.network = network

class Metadata():
    settings: MetadataSettings = {}

    def __init__(self, **kwargs):
        self.settings["priority"] = MetadataSettings(setting_type="int")
        self.settings["image-type"] = MetadataSettings(setting_type="str")
        self.settings["manage-config"] = MetadataSettings(setting_type="bool", default=False)
        self.settings["feeder-id"] = MetadataSettings(setting_type="UUID")
        self.settings["force-mac-address"] = MetadataSettings(setting_type="MAC")
        self.settings["allow-auto-updates"] = MetadataSettings(setting_type="bool", default=False)
        self.settings["allow-manual-updates"] = MetadataSettings(setting_type="bool", default=False)
        self.settings["network-config-style"] = MetadataSettings(setting_type="network_config_style", default="buster", sdonly=True, network=True)
        self.settings["wired-network"] = MetadataSettings(setting_type="bool", default=True, sdonly=True, network=True)
        self.settings["wired-type"] = MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True)
        self.settings["wired-address"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wired-netmask"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wired-broadcast"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wired-gateway"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wired-nameservers"] = MetadataSettings(default= ["8.8.8.8", "8.8.4.4"], sdonly=True, network=True)
        self.settings["wireless-network"] = MetadataSettings(setting_type="bool", default=False, sdonly=True, network=True)
        self.settings["wireless-ssid"] = MetadataSettings(sdonly=True, network=True, setting_type="str")
        self.settings["wireless-password"] = MetadataSettings(protect=True, sdonly=True, network=True, setting_type="str")
        self.settings["wireless-type"] = MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True)
        self.settings["wireless-address"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wireless-broadcast"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wireless-netmask"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wireless-gateway"] = MetadataSettings(sdonly=True, network=True)
        self.settings["wireless-nameserver"] = MetadataSettings(default = ["8.8.8.8", "8.8.4.4"], sdonly=True, network=True)
        self.settings["wireless-country"] = MetadataSettings(default = "00", setting_type="country", sdonly=True, network=True)
        self.settings["allow-dhcp-duic"] = MetadataSettings(default=True, setting_type="bool", sdonly=True, network=True)
        self.settings["http-proxy-host"] = MetadataSettings(network=True)
        self.settings["http-proxy-port"] = MetadataSettings(network=True)
        self.settings["http-proxy-user"] = MetadataSettings(network=True)
        self.settings["http-proxy-password"] = MetadataSettings(protect=True, network=True)
        self.settings["adept-serverhosts"] = MetadataSettings() # Come back to this
        self.settings["adept-serverport"] = MetadataSettings(setting_type="int", default=1200)
        self.settings["rfkill"] = MetadataSettings(setting_type="bool", default=False, sdonly=True)
        self.settings["receiver-type"] = MetadataSettings(setting_type="receiver", default="rtlsdr")
        self.settings["rtlsdr-device-index"] = MetadataSettings(default=False, sdonly=True)
        self.settings["rtlsdr-ppm"] = MetadataSettings(setting_type = "int", default = 0, sdonly=True)
        self.settings["rtlsdr-gain"] = MetadataSettings(setting_type = "gain", default = "max", sdonly=True)
        self.settings["beast-baudrate"] = MetadataSettings(setting_type = "int", sdonly=True)
        self.settings["radarcape-host"] = MetadataSettings(sdonly = True)
        self.settings["receiver-port"] = MetadataSettings(setting_type = "int", default = 30005)
        self.settings["allow-modeac"] = MetadataSettings(setting_type = "bool", default = True, sdonly=True)
        self.settings["allow-mlat"] = MetadataSettings(setting_type = "bool", default = True)
        self.settings["mlat-results"] = MetadataSettings(setting_type = "bool", default = True)
        self.settings["mlat-results-anon"] = MetadataSettings(setting_type = "bool", default = True)
        self.settings["mlat-results-format"] = MetadataSettings(default = "beast,connect,localhost:30104 beast,listen,30105 ext_basestation,listen,30106")
        self.settings["slow-cpu"] = MetadataSettings(default = "auto", sdonly = True)
        self.settings["adaptive-dynamic-range"] = MetadataSettings(setting_type="bool", default = True, sdonly=True)
        self.settings["adaptive-dynamic-range-target"] = MetadataSettings(setting_type="double", sdonly=True)
        self.settings["adaptive-burst"] = MetadataSettings(setting_type="bool", default=False, sdonly=True)
        self.settings["adaptive-min-gain"] = MetadataSettings(setting_type="double", sdonly=True)
        self.settings["adaptive-max-gain"] = MetadataSettings(setting_type="double", sdonly=True)
        self.settings["enable-firehose"] = MetadataSettings(setting_type="bool", default = False)
        self.settings["allow-ble-setup"] = MetadataSettings(default = "auto", sdonly = True)
        self.settings["uat-receiver-type"] = MetadataSettings(setting_type = "uat_receiver", default=None)
        self.settings["uat-receiver-host"] = MetadataSettings()
        self.settings["uat-receiver-port"] = MetadataSettings(setting_type = "int", default = 30978)
        self.settings["uat-sdr-gain"] = MetadataSettings(setting_type = "gain", default = "max", sdonly = True)
        self.settings["uat-sdr-ppm"] = MetadataSettings(setting_type = "double", default = 0, sdonly = True)
        self.settings["uat-sdr-device"] = MetadataSettings(default = "driver=rtlsdr", sdonly = True)
        self.settings["use-gpsd"] = MetadataSettings(setting_type="bool", default = True)

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
        if (isinstance(val, str) and val == "max") or (isinstance(val, int) and val == -10):
            return "max"
        elif isinstance(val, int):
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
                return float(double)

            case "mac":
                return val

            case "uuid":
                return self.convert_str_to_uuid(val)

            case "gain":
                return self.convert_str_to_gain(val)

            case _:
                raise TypeError("Unrecognized type {t}")

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
        m = re.match("^[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}$", val)
        if m.start() == 0 and m.end == len(val):
            return True
        
        return False

    def validate_uuid(self, val: str, version=4) -> bool:
        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

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

            case "mac":
                return self.validate_mac(val)

            case "uuid":
                return self.validate_uuid(val)

            case "gain":
                return self.validate_gain(val)

            case _:
                raise TypeError(f"Unrecognized type {t}")

            
class ConfigFile():
    def __init__(self, filename: str, metadata: Metadata = None, priority: int =0, readonly: bool = True) -> None:
        self._metadata = metadata
        self._priority = priority
        self._readonly = readonly
        self._filename = filename
        self.values = {}
    
    def process_quotes(self, line: str) -> str:
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
                        if self._metadata.get_setting(key) is None:
                            print(f"{self._filename}:{idx}: unrecognized option {key}")
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
            if val:
                return val
        
        return self._metadata.get_setting(setting_key).default


def create_standard_piaware_config_group(extra_file_path: str = None) -> ConfigGroup:
    piaware_image_config = "/usr/share/piaware-support/piaware-image-config.txt"
    piaware_conf = "/etc/piaware.conf"
    boot_piaware_config = "/boot/piaware-config.txt"


    files = []
    f = ConfigFile(filename=piaware_image_config, priority=30, metadata = Metadata())
    files.append(f)

    if extra_file_path is not None:
        f = ConfigFile(filename=extra_file_path, priority=100, metadata = Metadata())
        files.append(f)
    else:
        f1 = ConfigFile(filename=piaware_conf, priority=40, metadata = Metadata())
        f2 = ConfigFile(filename=boot_piaware_config, priority=50, metadata = Metadata())

        files.append(f1)
        files.append(f2)
    
    return ConfigGroup(files=files, metadata = Metadata())

def generate_from_args(extra_file_path: str = None) -> ConfigGroup():
    cg = create_standard_piaware_config_group(extra_file_path=extra_file_path)
    cg.read_configs()
    return cg

