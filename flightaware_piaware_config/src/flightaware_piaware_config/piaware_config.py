"""
    This file is a re-write of https://github.com/flightaware/piaware/blob/master/package/fa_piaware_config.tcl.
    It reads from the three default config files to obtain various settings for the piaware machine.
"""

from uuid import UUID, uuid4
import re
import os
import sys
import io
from ipaddress import IPv4Network, NetmaskValueError
from typing import Callable

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
    RECEIVER: ["rtlsdr", "sdr", "bladerf", "beast", "relay", "radarcape", "radarcape-local", "pg2sdr", "other", "none"],
    UAT_RECEIVER: ["sdr", "stratuxv3", "other", "none"],
    NETWORK_TYPE: ["static", "dhcp"],
    SLOW_CPU: ["yes", "no", "auto"],
    NETWORK_CONFIG_STYLE: ["default", "buster", "jessie"]
}
PIAWARE_IMAGE_CONF = "/usr/share/piaware-support/piaware-image-config.txt"
PIAWARE_CONF = "/etc/piaware.conf"
BOOT_PIAWARE_CONF = "/boot/firmware/piaware-config.txt"
WHITEOUT = object()

class EnumProcessor():
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
    @staticmethod
    def validate(val) -> bool:
        # Regular string values should be 7-bit ASCII only
        try:
            val.encode('us-ascii', errors='strict')
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def parse(val) -> str:
        return val

class BytesProcessor:
    @staticmethod
    def validate(val: str) -> bool:
        # Anything outside U+0000 .. U+00FF isn't valid here
        # (Should never happen with a well-behaved caller, but..)
        try:
            val.encode('iso-8859-1', errors='strict')
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def parse(val: str) -> bytes:
        # Intermediate strings are always effectively
        # limited to U+0000 .. U+00FF, which has a
        # 1:1 mapping to ISO-8859-1. Just re-encode
        # as ISO-8859-1 to recover the original bytes.
        return val.encode('iso-8859-1', errors='strict')

class IntegerProcessor():
    @staticmethod
    def validate(val) -> bool:
        try: 
            int(val)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def parse(val) -> int:
        return int(val)

class DoubleProcessor():
    @staticmethod
    def validate(val) -> bool:
        try: 
            float(val)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def parse(val) -> float:
        return float(val)

class BoolProcessor():
    @staticmethod
    def validate(val) -> bool:
        val = val.lower()
        return val == "yes" or val == "no"

    @staticmethod
    def parse(val) -> bool:
        if val.lower() == "yes":
            return True
        else:
            return False

class MACProcessor():
    @staticmethod
    def validate(val) -> bool:
        val = val.lower()
        m = re.fullmatch("^[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}$", val)
        if m is None:
            return False
        return True

    @staticmethod
    def parse(val) -> str:
        return val

class UUIDProcessor():
    @staticmethod
    def validate(val, version=4) -> bool:
        try:
            uuid_obj = UUID(val, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == val

    @staticmethod
    def parse(val, version=4) -> uuid4:
        return UUID(val, version=version)


class GainProcessor():

    @staticmethod
    def validate(val: str) -> bool:
        return DoubleProcessor.validate(val) or (isinstance(val, str) and val == "max")

    @staticmethod
    def parse(val) -> str | float:
        val = val.lower()
        if (isinstance(val, str) and val == "max") or (IntegerProcessor.validate(val) and int(val) <= -10):
            return "max"
        elif IntegerProcessor.validate(val):
            return int(val)
        else:
            return float(val)

class NetmaskProcessor():
    @staticmethod
    def validate(val: str) -> bool:
        try: 
            IPv4Network(f"0.0.0.0/{val}")
            return True
        except NetmaskValueError:
            return False

    @staticmethod
    def parse(val: str) -> str:
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
    _settings: MetadataSettings = {
        "priority":                         MetadataSettings(IntegerProcessor),
        "image-type":                       MetadataSettings(StrProcessor),
        "manage-config":                    MetadataSettings(BoolProcessor, setting_type="bool", default=False),
        "feeder-id":                        MetadataSettings(UUIDProcessor, setting_type="UUID",),
        "force-macaddress":                 MetadataSettings(MACProcessor, setting_type="MAC"),
        "allow-auto-updates":               MetadataSettings(BoolProcessor, setting_type="bool", default=False),
        "allow-manual-updates":             MetadataSettings(BoolProcessor, setting_type="bool", default=False),
        "network-config-style":             MetadataSettings(EnumProcessor(NETWORK_CONFIG_STYLE), setting_type="network_config_style", default="default", sdonly=True, network=True),
        "wired-network":                    MetadataSettings(BoolProcessor, setting_type="bool", default=True, sdonly=True, network=True),
        "wired-type":                       MetadataSettings(EnumProcessor(NETWORK_TYPE), setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wired-address":                    MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str"),
        "wired-netmask":                    MetadataSettings(NetmaskProcessor, sdonly=True, network=True, setting_type="netmask"),
        # Setting broadcast address directly through boot/firmare/piaware-config.txt has been deprecated.
        "wired-broadcast":                  MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str", deprecated=True),
        "wired-gateway":                    MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str"),

        "wired-nameservers":                MetadataSettings(StrProcessor, default="8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),

        "wireless-network":                 MetadataSettings(BoolProcessor, setting_type="bool", default=False, sdonly=True, network=True),
        "wireless-ssid":                    MetadataSettings(BytesProcessor, sdonly=True, network=True, setting_type="bytes"),
        "wireless-password":                MetadataSettings(StrProcessor, protect=True, sdonly=True, network=True, setting_type="str"),
        "wireless-type":                    MetadataSettings(EnumProcessor(NETWORK_TYPE), setting_type="network_type", default="dhcp", sdonly=True, network=True),
        "wireless-address":                 MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str"),
        "wireless-broadcast":               MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str", deprecated=True),
        "wireless-netmask":                 MetadataSettings(NetmaskProcessor, sdonly=True, network=True, setting_type="netmask"),
        "wireless-gateway":                 MetadataSettings(StrProcessor, sdonly=True, network=True, setting_type="str"),
        "wireless-nameservers":             MetadataSettings(StrProcessor, default = "8.8.8.8 8.8.4.4", sdonly=True, network=True, setting_type="str"),
        "wireless-country":                 MetadataSettings(EnumProcessor(COUNTRY), default = "00", setting_type="country", sdonly=True, network=True),
        "allow-dhcp-duic":                  MetadataSettings(BoolProcessor, default=True, setting_type="bool", sdonly=True, network=True),
        "http-proxy-host":                  MetadataSettings(StrProcessor, network=True, setting_type="str"),
        "http-proxy-port":                  MetadataSettings(StrProcessor, network=True, setting_type="str"),
        "http-proxy-user":                  MetadataSettings(StrProcessor, network=True, setting_type="str"),
        "http-proxy-password":              MetadataSettings(StrProcessor, protect=True, network=True, setting_type="str"),
        "adept-serverhosts":                MetadataSettings(StrProcessor, default=["piaware.flightaware.com", "piaware.flightaware.com", 
        ["206.253.80.196", "206.253.80.197", "206.253.80.198", "206.253.80.199", "206.253.80.200", "206.253.80.201"], 
        ["206.253.84.193", "206.253.84.194", "206.253.84.195", "206.253.84.196", "206.253.84.197", "206.253.84.198"]], setting_type="str"),

        "adept-serverport":                 MetadataSettings(IntegerProcessor, setting_type="int", default=1200),
        "rfkill":                           MetadataSettings(BoolProcessor, setting_type="bool", default=False, sdonly=True),
        "receiver-type":                    MetadataSettings(EnumProcessor(RECEIVER), setting_type="receiver", default="rtlsdr"),
        "rtlsdr-device-index":              MetadataSettings(StrProcessor, default=False, sdonly=True, setting_type="str"),
        "rtlsdr-ppm":                       MetadataSettings(IntegerProcessor, setting_type = "int", default = 0, sdonly=True),
        "rtlsdr-gain":                      MetadataSettings(GainProcessor, setting_type = "gain", default = "max", sdonly=True),
        "beast-baudrate":                   MetadataSettings(IntegerProcessor, setting_type = "int", sdonly=True),
        "radarcape-host":                   MetadataSettings(StrProcessor, sdonly = True, setting_type="str"),
        "receiver-port":                    MetadataSettings(IntegerProcessor, setting_type = "int", default = 30005),
        "allow-modeac":                     MetadataSettings(BoolProcessor, setting_type = "bool", default = True, sdonly=True),
        "allow-mlat":                       MetadataSettings(BoolProcessor, setting_type = "bool", default = True),
        "mlat-results":                     MetadataSettings(BoolProcessor, setting_type = "bool", default = True),
        "mlat-results-anon":                MetadataSettings(BoolProcessor, setting_type = "bool", default = True),
        "mlat-results-format":              MetadataSettings(StrProcessor, default = "beast,connect,localhost:30104 beast,listen,30105 ext_basestation,listen,30106", setting_type="str"),
        "slow-cpu":                         MetadataSettings(EnumProcessor(SLOW_CPU), default = "auto", sdonly = True, setting_type="slow_cpu"),
        "adaptive-dynamic-range":           MetadataSettings(BoolProcessor, setting_type="bool", default = True, sdonly=True),
        "adaptive-dynamic-range-target":    MetadataSettings(DoubleProcessor, setting_type="double", sdonly=True),
        "adaptive-burst":                   MetadataSettings(BoolProcessor, setting_type="bool", default=False, sdonly=True),
        "adaptive-min-gain":                MetadataSettings(DoubleProcessor, setting_type="double", sdonly=True),
        "adaptive-max-gain":                MetadataSettings(DoubleProcessor, setting_type="double", sdonly=True),
        "enable-firehose":                  MetadataSettings(BoolProcessor, setting_type="bool", default = False),
        "allow-ble-setup":                  MetadataSettings(StrProcessor, default = "auto", sdonly = True, setting_type="str"),
        "uat-receiver-type":                MetadataSettings(EnumProcessor(UAT_RECEIVER), setting_type = "uat_receiver", default=None),
        "uat-receiver-host":                MetadataSettings(StrProcessor, setting_type="str"),
        "uat-receiver-port":                MetadataSettings(IntegerProcessor, setting_type = "int", default = 30978),
        "uat-sdr-gain":                     MetadataSettings(GainProcessor, setting_type = "gain", default = "max", sdonly = True),
        "uat-sdr-ppm":                      MetadataSettings(DoubleProcessor, setting_type = "double", default = 0, sdonly = True),
        "uat-sdr-device":                   MetadataSettings(StrProcessor, default = "driver=rtlsdr", sdonly = True, setting_type="str"),
        "use-gpsd":                         MetadataSettings(BoolProcessor, setting_type="bool", default = True)
    }

    def get_setting(self, key: str) -> MetadataSettings:
        return self._settings[key]     # might raise KeyError
    
    def parse_value(self, key: str, val: str) -> any:
        setting = self._settings[key]  # might raise KeyError
        return setting.processor.parse(val)

    def validate_value(self, key: str, val: str) -> bool:
        setting = self._settings[key]  # might raise KeyError
        return setting.processor.validate(val)

    
def parse_config_line(line: str, warn: Callable[[str],None]) -> tuple[str,str] | None:
    # Line is empty except for comment
    if re.search(r"^\s*#.*", line):
        return None

    # Line has key but no value. Plus optional comment
    option_line = re.search(r"^\s*([a-zA-Z0-9_-]+)\s*(?:#.*)?$", line)
    if option_line:
        return (option_line.group(1), "")

    # Line has key + value. Plus optional comment.
    option_line = re.search(r"^\s*([a-zA-Z0-9_-]+)\s+(.+)$", line)
    if option_line:
        key = option_line.group(1)
        value = option_line.group(2)
        return (key, parse_config_value(value, warn))

    return None


def parse_config_value(value: str, warn: Callable[[str],None]) -> str:
    value = value.strip()

    if not value:
        return ''

    if value[0] != '"' and value[0] != "'":
        # Unquoted value
        comment_index = value.find("#")
        if comment_index != -1:
            value = value[:comment_index]
        return value.strip()

    # Quoted value with escape processing
    result = ''
    terminating_char = value[0]

    i = 1
    char = None
    while i < len(value):
        char = value[i]
        i += 1

        match char:
            case '\\':
                count, unescaped = parse_escape(value[i:], warn)
                result += unescaped
                i += count

            case '"' | "'":
                if char == terminating_char:
                    break
                result += char

            case _:
                result += char

    residual = value[i:].strip()
    if len(residual) > 0 and residual[0] != '#':
        warn(f'extra trailing data after closing quote ignored (did you need to backslash-escape that quote?)')
    if char != terminating_char:
        warn('no closing quote found in quoted value')

    return result

def parse_escape(esc: str, warn:Callable[[str],None]) -> (int, str):
    # Parse an escape sequence 'esc', where esc[0] is the first character
    # following the backslash.
    #
    # Return (count, unescaped) where 'count' is the length of the escape
    # sequence to consume (excluding the backslash) and 'unescaped' is
    # the result of interpreting the escape sequence.
    #
    # If the escape sequence is not recognized, parse_escape calls
    # warn() with a suitable warning message and returns (0, '\\')
    # i.e.  the caller should emit the backslash unchanged and not
    # skip over any further characters.

    if not esc:
        warn('trailing backslash not interpreted as a line continuation')
        return (0, '\\')

    match esc[0]:
        case 'x':
            # \xNN -> literal byte with hex value NN (only really
            # useful in byte-oriented config values like
            # wireless-ssid).  We're exclusively using U+0000 ..
            # U+00FF in our strings so these just map 1:1 to that
            # range.
            try:
                hexdigits = esc[1:3]
                hexval = int(hexdigits, 16)
                if hexval < 0 or hexval > 255:  # >255 should be impossible, but anyway..
                    raise ValueError()
                return (3, chr(hexval))
            except ValueError as e:
                warn(f'unrecognized escape \\x{hexdigits}')
                return (0, '\\')

        case '\\' | '"' | "'":
            # \\ -> \
            # \" -> "
            # \' -> '
            return (1, esc[0])

        case _:
            warn(f'unrecognized escape \\{esc[0]}')
            return (0, '\\')

class ConfigFile():
    def __init__(self, filename: str, metadata: Metadata = None, priority: int =0, readonly: bool = True) -> None:
        self._metadata = metadata
        self._priority = priority
        self._readonly = readonly
        self._filename = filename
        self.values = {}

    def _open(self):
        # Open and return the underlying file in binary mode.
        # This is broken out to let unit tests directly provide
        # a BinaryIO, rather than needing to mock builtins.open
        # or put a file on disk

        # (this could be handled better with some restructuring of
        # how/when the class acquires the file object, but this
        # will do for now I guess)
        return open(self._filename, 'rb')

    def get(self, setting_key: str) -> any:
        return self.values.get(setting_key, None)

    def warn(self, lineno: int, msg: str) -> None:
        print(f'{self._filename}:{lineno}: warning: {msg}', file=sys.stderr)

    def load_config_from_file(self) -> None:
        config = self.read_config_into_list()
        self.parse_config_from_list(config)

    def read_config_into_list(self) -> list:
        return_value = []

        # We read the config file using an ISO-8859-1 encoding,
        # which will produce a 1:1 mapping between bytes and
        # unicode codepoints in the range U+0000 .. U+00FF.
        #
        # Later, after processing any escapes, we either:
        #  * reject anything not in the U+0000 .. U+00FF range,
        #    for values that are meant to be regular strings; or
        #  * re-encode the string using ISO-8859-1 to recover
        #    the original bytes, for values that are meant to be
        #    raw bytes (currently only wireless-ssid)
        #
        # This is a middle ground between "require only 7-bit
        # ASCII" and "specify a particular encoding". Bytes-
        # oriented values will follow whatever encoding was
        # actually used in the config file, be it UTF-8 or
        # whatever -- no transcoding is done.
        with io.TextIOWrapper(self._open(), encoding='iso-8859-1') as config:
            for line in config:
                return_value.append(line.strip())
        
        return return_value

    def parse_config_from_list(self, config) -> None:
        for lineno, line in enumerate(config, start=1):
            warn = lambda msg: self.warn(lineno, msg)

            l = parse_config_line(line, warn)
            if not l:
                continue
            
            key, val = l
            key = key.lower()
            try:
                setting = self._metadata.get_setting(key)
            except KeyError:
                warn(f"unknown option {key} ignored")
                continue

            if setting.deprecated:
                warn(f"option {key} is deprecated")
            if key in self.values:
                warn("duplicated option {key}")

            if val == "":
                # Whiteout entry (force use of default)
                self.values[key] = WHITEOUT
                continue

            if not self._metadata.validate_value(key, val):
                warn(f"invalid value for option {key}:{val}, option ignored")
                continue

            self.values[key] = self._metadata.parse_value(key, val)

class ConfigGroup():
    files: list[ConfigFile]
    _metadata: Metadata

    def __init__(self, metadata: Metadata = None, files: list[ConfigFile] = None) -> None:
        if files is None:
            self.files = []
        else:
            self.files = files
        self._metadata = metadata

        self.files = sorted(self.files, key=lambda x: x._priority, reverse=True)

    def load_configs(self):
        for file in self.files:
            file.load_config_from_file()

    def get(self, setting_key: str) -> any:
        for config_file in self.files:
            val = config_file.get(setting_key)
            if val is None:
                # no setting for that key in this file, continue search
                continue

            if val is WHITEOUT:
                # explicit whiteout, use default
                break

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
    cg.load_configs()
    return cg
