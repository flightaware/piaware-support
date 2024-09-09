
from uuid import UUID


class MetadataSettings():
    def __init__(self, default: Any = None, setting_type: str = None, protect: str = None, sdonly: bool = None, network: str = None) -> None:
		self.default = default
		self.setting_type = setting_type
		self.protect = protect
		self.sdonly = sdonly
		self.network = network

class Metadata():
    settings: MetadataSettings = {}

    def __init__(self, **kwargs):
        self.priority = MetadataSettings(setting_type="int")
        self.image_type = MetadataSettings(setting_type="str")
        self.manage_config = MetadataSettings(setting_type="bool", default=False)
        self.feeder_id = MetadataSettings(setting_type="UUID")
        self.force_mac_address = MetadataSettings(setting_type="MAC")
        self.allow_auto_updates = MetadataSettings(setting_type="bool", default=False)
        self.allow_manual_updates = MetadataSettings(setting_type="bool", default=False)
		self.network_config_style = MetadataSettings(setting_type="network_config_style", default="buster", sdonly=True, network=True)
        
		self.wired_network = MetadataSettings(setting_type="bool", default=True, sdonly=True, network=True)
		self.wired_type = MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True)
		self.wired_address = MetadataSettings(sdonly=True, network=True)
		self.wired_netmask = MetadataSettings(sdonly=True, network=True)
		self.wired_broadcast = MetadataSettings(sdonly=True, network=True)
		self.wired_gateway = MetadataSettings(sdonly=True, network=True)
		self.wired_nameservers = MetadataSettings(default= ["8.8.8.8", "8.8.4.4"], sdonly=True, network=True)

		self.wireless_network = MetadataSettings(setting_type="bool", default=False, sdonly=True, network=True)


		self.wireless_ssid = MetadataSettings(sdonly=True, network=True)
		self.wireless_password = MetadataSettings(protect=True, sdonly=True, network=True)
		self.wireless_type = MetadataSettings(setting_type="network_type", default="dhcp", sdonly=True, network=True)
		self.wireless_address = MetadataSettings(sdonly=True, network=True)
		self.wireless_broadcast = MetadataSettings(sdonly=True, network=True)
		self.wireless_netmask = MetadataSettings(sdonly=True, network=True)
		self.wireless_gateway =  MetadataSettings(sdonly=True, network=True)

		self.wireless_nameserver = MetadataSettings(default = ["8.8.8.8", "8.8.4.4"], sdonly=True, network=True)
		self.wireless_country = MetadataSettings(default = 00, type="country" sdonly=True, sdonly=True)

		self.allow_dhcp_duic = MetadataSettings(default=True, setting_type="bool", sdonly=True, network=True)

		self.http_proxy_host = MetadataSettings(network=True)
		self.http_proxy_port = MetadataSettings(network=True)
		self.http_proxy_user = MetadataSettings(network=True)
		self.http_proxy_password = MetadataSettings(protect=True, network=True)


		self.adept_serverhosts = MetadataSettings() # Come back to this
		self.adept_serverport = MetadataSettings(setting_type="int", default=1200)

		self.rfkill = MetadataSettings(setting_type="bool", default=False, sdonly=True)
		self.receiver_type = MetadataSettings(setting_type="receiver", default="rtlsdr")

		self.rtlsdr_device_index = MetadataSettings(default=False, sdonly=True)

		self.rtlsdr_ppm = MetadataSettings(setting_type = "int", default = 0, sdonly=True)
		self.rtlsdr_gain = MetadataSettings(setting_type = "gain", default = "max", sdonly=True)

		self.beast_baudrate = MetadataSettings(setting_type = "int", sdonly=True)
		self.radarcape_host = MetadataSettings(sdonly = True)

		self.receiver_port = MetadataSettings(setting_type = "int", default = 30005)
		self.allow_mode_ac = MetadataSettings(setting_type = "bool", default = True, sdonly=True)
		self.allow_mlat = MetadataSettings(setting_type = "bool", default = True)
		self.mlat_results = MetadataSettings(setting_type = "bool", default = True)
		self.mlat_results_anon =  MetadataSettings(setting_type = "bool", default = True)

		self.mlat_results_format =  MetadataSettings(default = "beast,connect,localhost:30104 beast,listen,30105 ext_basestation,listen,30106")
		self.slow_cpu = MetadataSettings(default = "auto", sdonly = True)

		self.adaptive_dynamic_range = MetadataSettings(setting_type="bool", default = True, sdonly=True)
		self.adaptive_dynamic_range_target = MetadataSettings(setting_type="double", sdonly=True)

		self.adaptive_burst = MetadataSettings(setting_type="bool", default=False, sdonly=True)
		self.adaptive_min_gain = MetadataSettings(setting_type="double", sdonly=True)
		self.adaptive_max_gain = MetadataSettings(setting_type="double", sdonly=True)

		self.enable_firehose = MetadataSettings(setting_type="bool", default = False)
		self.allow_ble_setup = MetadataSettings(default = "auto", sdonly = True)

		self.uat_receiver_type = MetadataSettings(setting_type = "uat_receiver", default=None)
		self.uat_receiver_host = None
		self.uat_receiver_port = MetadataSettings(setting_type = "int", default = 30978)
		self.uat_sdr_gain = MetadataSettings(setting_type = "gain", default = "max", sdonly = True)
		self.uat_sdr_ppm = MetadataSettings(setting_type = "double", default = 0, sdonly = True)
		self.uat_sdr_device = MetadataSettings(default = "driver=rtlsdr", sdonly = True)

		self.use_gpsd = MetadataSettings(setting_type="bool", default = True)


class ConfigFile():
    def __init__(self, filename: str, metadata: Metadata = None, priority: int =0, readonly: bool = True) -> None:
        self._metadata = metadata
        self._priority = priority
        self._readonly = readonly
        self._filename = filename

class ConfigGroup():
    files: list[ConfigFile]
    metadata: Metadata

    def __init__(self, metadata: Metadata = None, files: list[ConfigFile] = None) -> None:
        if files is None:
            self.files = []
        else:
            self.files = files
        self.metadata = metadata
    

def create_standard_piaware_config(extra_file_path: str = None) -> ConfigGroup:
    files = []
    f = ConfigFile(filename="/usr/share/piaware-support/piaware-image-config.txt", priority=30)
    files.append(f)

    if extra_file_path is not None:
        f = ConfigFile(filename=extra_file_path, priority=100)
        files.append(f)
    else:
        f1 = ConfigFile(filename="/etc/piaware.conf", priority=40 )
        f2 = ConfigFile(filename="/boot/piaware-config.txt", priority=50)

        files.append(f1)
        files.append(f2)
    
    return ConfigGroup(files=files)
