"""
    This file is a re-write of https://github.com/flightaware/piaware/blob/master/package/fa_piaware_config.tcl.
    It reads from the three default config files to obtain various settings for the piaware machine.
"""

from uuid import UUID, uuid4
import re
import os
from ipaddress import IPv4Network, NetmaskValueError

COUNTRY = "country"
RECEIVER = "receiver"
UAT_RECEIVER = "uat_receiver"
NETWORK_TYPE = "network_type"
SLOW_CPU = "slow_cpu"
NETWORK_CONFIG_STYLE = "network_config_style"

PIAWARE_CONFIG_ENUMS = {
    COUNTRY: ["AD","AE","AF","AG","AI","AL","AM","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE",
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
                "VU","WF","WS","YE","YT","ZA","ZM","ZW","00" ],
    RECEIVER: ["rtlsdr", "sdr", "bladerf", "beast", "relay", "radarcape", "radarcape-local", "other", "none"],
    UAT_RECEIVER: ["sdr", "stratuxv3", "other", "none"],
    NETWORK_TYPE: ["static", "dhcp"],
    SLOW_CPU: ["yes", "no", "auto"],
    NETWORK_CONFIG_STYLE: ["default", "buster", "jessie"]
}
PIAWARE_IMAGE_CONF = "/usr/share/piaware-support/piaware-image-config.txt"
PIAWARE_CONF = "/etc/piaware.conf"
BOOT_PIAWARE_CONF = "/boot/firmware/piaware-config.txt"
WHITEOUT = "WHITEOUT"

class ENUMProcessor():
    def __init__(self, enum: str):
        self.enum = enum

    def validate(self, val: str) -> bool:
        if val in PIAWARE_CONFIG_ENUMS[self.enum]:
            return True
        else:
            return False

    def parse(self, val: str) -> str:
        return val

class StrProcessor():
    def validate(self, val) -> bool:
        return True

    def parse(self, val) -> str:
        return val

class IntegerProcessor():
    def validate(self, val) -> bool:
        try: 
            int(val)
        except ValueError:
            return False
        else:
            return True

    def parse(self, val) -> int:
        return int(val)

class DoubleProcessor():
    def validate(self, val) -> bool:
        try: 
            float(val)
        except ValueError:
            return False
        else:
            return True

    def parse(self, val) -> float:
        return float(val)

class BoolProcessor():
    def validate(self, val) -> bool:
        val = val.lower()
        return val == "yes" or val == "no"

    def parse(self, val) -> bool:
        if val.lower() == "yes":
            return True
        else:
            return False

class MACProcessor():
    def validate(self, val) -> bool:
        val = val.lower()
        m = re.fullmatch("^[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}$", val)
        if m is None:
            return False
        return True

    def parse(self, val) -> str:
        return val

class UUIDProcessor():
    def validate(self, val, version=4) -> bool:
        try:
            uuid_obj = UUID(val, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == val

    def parse(self, val, version=4) -> uuid4:
        return UUID(val, version=version)


class GainProcessor():
    int_proc = IntegerProcessor()

    def validate(self, val: str) -> bool:
        return DoubleProcessor().validate(val) or (isinstance(val, str) and val == "max")

    def parse(self, val) -> str | float:
        val = val.lower()
        if (isinstance(val, str) and val == "max") or (GainProcessor.int_proc.validate(val) and int(val) <= -10):
            return "max"
        elif GainProcessor.int_proc.validate(val):
            return int(val)
        else:
            return float(val)

class NetmaskProcessor():
    def validate(self, val: str) -> bool:
        try: 
            IPv4Network(f"0.0.0.0/{val}")
            return True
        except NetmaskValueError:
            return False

    def parse(self, val: str) -> str:
        return val

class MetadataSettings():
    def __init__(self, processor, default: any = None, setting_type: str = None, protect: str = None, sdonly: bool = None, network: str = None, deprecated = False) -> None:
        self.default = default
        self.setting_type = setting_type
        self.protect = protect
        self.sdonly = sdonly
        self.network = network
        self.deprecated = deprecated
        self.processor = processor

class Metadata():
    int_proc = IntegerProcessor()
    str_proc = StrProcessor()
    bool_proc = BoolProcessor()
    gain_proc = GainProcessor()
    double_proc = DoubleProcessor()
    mac_proc = MACProcessor()
    netmask_proc = NetmaskProcessor()
    uuid_proc = UUIDProcessor()

    settings: MetadataSettings = {
        "priority":                         MetadataSettings(int_proc),
        "image-type":                       MetadataSettings(str_proc),
        "manage-config":                    MetadataSettings(bool_proc, setting_type="bool", default=False),
        "feeder-id":                        MetadataSettings(uuid_proc, setting_type="UUID",),
        "force-macaddress":                 MetadataSettings(mac_proc, setting_type="MAC"),
        "allow-auto-updates":               MetadataSettings(bool_proc, setting_type="bool", default=False),
        "allow-manual-updates":             MetadataSettings(bool_proc, setting_type="bool", default=False),
        "network-config-style":             MetadataSettings(ENUMProcessor(NETWORK_CONFIG_STYLE), setting_type="network_config_style", default="default", sdonly=True, network=True),
        "wired-network":                    MetadataSettings(bool_proc, setting_type="bool", default=True, sdonly=True, network=True),
        "wired-type":                       MetadataSettings(ENUMProcessor(NETWORK_TYPE), setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wired-address":                    MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str"),
        "wired-netmask":                    MetadataSettings(netmask_proc, sdonly=True, network=True, setting_type="netmask"),
        # Setting broadcast address directly through boot/firmare/piaware-config.txt has been deprecated.
        "wired-broadcast":                  MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str", deprecated=True),
        "wired-gateway":                    MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str"),

        "wired-nameservers":                MetadataSettings(str_proc, default="8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),

        "wireless-network":                 MetadataSettings(bool_proc, setting_type="bool", default=False, sdonly=True, network=True),
        "wireless-ssid":                    MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str"),
        "wireless-password":                MetadataSettings(str_proc, protect=True, sdonly=True, network=True, setting_type="str"),
        "wireless-type":                    MetadataSettings(ENUMProcessor(NETWORK_TYPE), setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wireless-address":                 MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str"),
        "wireless-broadcast":               MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str", deprecated=True),
        "wireless-netmask":                 MetadataSettings(netmask_proc, sdonly=True, network=True, setting_type="netmask"),
        "wireless-gateway":                 MetadataSettings(str_proc, sdonly=True, network=True, setting_type="str"),
        "wireless-nameservers":             MetadataSettings(str_proc, default = "8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),
        "wireless-country":                 MetadataSettings(ENUMProcessor(COUNTRY), default = "00", setting_type="country", sdonly=True, network=True),
        "allow-dhcp-duic":                  MetadataSettings(bool_proc, default=True, setting_type="bool", sdonly=True, network=True),
        "http-proxy-host":                  MetadataSettings(str_proc, network=True, setting_type="str"),
        "http-proxy-port":                  MetadataSettings(str_proc, network=True, setting_type="str"),
        "http-proxy-user":                  MetadataSettings(str_proc, network=True, setting_type="str"),
        "http-proxy-password":              MetadataSettings(str_proc, protect=True, network=True, setting_type="str"),
        "adept-serverhosts":                MetadataSettings(str_proc, default=["piaware.flightaware.com", "piaware.flightaware.com", 
        ["206.253.80.196", "206.253.80.197", "206.253.80.198", "206.253.80.199", "206.253.80.200", "206.253.80.201"], 
        ["206.253.84.193", "206.253.84.194", "206.253.84.195", "206.253.84.196", "206.253.84.197", "206.253.84.198"]], setting_type="str"),

        "adept-serverport":                 MetadataSettings(int_proc, setting_type="int", default=1200),
        "rfkill":                           MetadataSettings(bool_proc, setting_type="bool", default=False, sdonly=True),
        "receiver-type":                    MetadataSettings(ENUMProcessor(RECEIVER), setting_type="receiver", default="rtlsdr"),
        "rtlsdr-device-index":              MetadataSettings(str_proc, default=False, sdonly=True, setting_type="str"),
        "rtlsdr-ppm":                       MetadataSettings(int_proc, setting_type = "int", default = 0, sdonly=True),
        "rtlsdr-gain":                      MetadataSettings(gain_proc, setting_type = "gain", default = "max", sdonly=True),
        "beast-baudrate":                   MetadataSettings(int_proc, setting_type = "int", sdonly=True),
        "radarcape-host":                   MetadataSettings(str_proc, sdonly = True, setting_type="str"),
        "receiver-port":                    MetadataSettings(int_proc, setting_type = "int", default = 30005),
        "allow-modeac":                     MetadataSettings(bool_proc, setting_type = "bool", default = True, sdonly=True),
        "allow-mlat":                       MetadataSettings(bool_proc, setting_type = "bool", default = True),
        "mlat-results":                     MetadataSettings(bool_proc, setting_type = "bool", default = True),
        "mlat-results-anon":                MetadataSettings(bool_proc, setting_type = "bool", default = True),
        "mlat-results-format":              MetadataSettings(str_proc, default = "beast,connect,localhost:30104 beast,listen,30105 ext_basestation,listen,30106", setting_type="str"),
        "slow-cpu":                         MetadataSettings(ENUMProcessor(SLOW_CPU), default = "auto", sdonly = True, setting_type="slow_cpu"),
        "adaptive-dynamic-range":           MetadataSettings(bool_proc, setting_type="bool", default = True, sdonly=True),
        "adaptive-dynamic-range-target":    MetadataSettings(double_proc, setting_type="double", sdonly=True),
        "adaptive-burst":                   MetadataSettings(bool_proc, setting_type="bool", default=False, sdonly=True),
        "adaptive-min-gain":                MetadataSettings(double_proc, setting_type="double", sdonly=True),
        "adaptive-max-gain":                MetadataSettings(double_proc, setting_type="double", sdonly=True),
        "enable-firehose":                  MetadataSettings(bool_proc, setting_type="bool", default = False),
        "allow-ble-setup":                  MetadataSettings(str_proc, default = "auto", sdonly = True, setting_type="str"),
        "uat-receiver-type":                MetadataSettings(ENUMProcessor(UAT_RECEIVER), setting_type = "uat_receiver", default=None),
        "uat-receiver-host":                MetadataSettings(str_proc, setting_type="str"),
        "uat-receiver-port":                MetadataSettings(int_proc, setting_type = "int", default = 30978),
        "uat-sdr-gain":                     MetadataSettings(gain_proc, setting_type = "gain", default = "max", sdonly = True),
        "uat-sdr-ppm":                      MetadataSettings(double_proc, setting_type = "double", default = 0, sdonly = True),
        "uat-sdr-device":                   MetadataSettings(str_proc, default = "driver=rtlsdr", sdonly = True, setting_type="str"),
        "use-gpsd":                         MetadataSettings(bool_proc, setting_type="bool", default = True)
    }

    def get_setting(self, key: str) -> MetadataSettings:
        if key not in self.settings:
            raise ValueError(f"Getting {key}. Could not find {key} in settings")
        
        return self.settings[key]
    
    def parse_value(self, key: str, val: str) -> any:
        if key not in self.settings:
            raise ValueError(f"Parsing value {val} for setting {key}. Could not find {key} in settings")

        setting = self.settings[key]
        return setting.processor.parse(val)

    def validate_value(self, key: str, val: str) -> bool:
        if key not in self.settings:
            raise ValueError(f"Validating value {val} for setting {key}. Could not find {key} in settings")

        setting = self.settings[key]
        return setting.processor.validate(val)

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

    def get_config(self) -> list:
        if not os.path.isfile(self._filename):
            raise ValueError(f"{self._filename} does not exist.")

        return_value = []
        with open(self._filename, "r") as config:
            for line in config:
                return_value.append(line.strip())
        
        return return_value

    def read_config(self) -> None:
        config = self.get_config()
        for idx, line in enumerate(config):
            l = self.parse_line(line)
            if not l:
                continue
            
            key, val = l
            key = key.lower()
            setting = self._metadata.get_setting(key)
            if setting.deprecated:
                raise ValueError(f"{self._filename}:{idx}: option {key} is deprecated. Skipping...")
            if val != "":
                if not self._metadata.validate_value(key, val):
                    raise ValueError(f"{self._filename}:{idx}: invalid value for option {key}:{val}")

                if key in self.values:
                    raise ValueError(f"{self._filename}:{idx}: {key} with value {val} overrides an existing instance of {key}")
                self.values[key] = self._metadata.parse_value(key, val)
            else:
                self.values[key] = WHITEOUT
                        

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
            if val == WHITEOUT:
                break
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

