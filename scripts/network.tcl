#
# Network configuration, invoked from configure-system.tcl
#

proc configure_wireless {} {
	if {![valid_network_config wireless]} {
		return
	}

	if {![have_config wireless-ssid]} {
		warn "wireless-network was set, but no wireless-ssid was given, no wireless network has been configured"
		return
	}

	# the physical interface config fragment
	# (this interface is brought up on boot and stays up
	# even while there is no AP association; wpa_supplicant
	# is started when the interface is brought up)
	generate_file_part "/etc/network/interfaces" {
		{auto wlan0}
		{allow-hotplug wlan0}
		{iface wlan0 inet manual}
		{wireless-power off}
		{wpa-roam /etc/wpa_supplicant/wpa-roam.conf}
	}

	# the wpasupplicant config file
	# this configures the actual association details
	# and contains the PSK/passphrase in plaintext
	# so we lock down the permissions
	set supplicant [list]
	lappend supplicant "network={"
	lappend supplicant "  ssid=\"[config_str wireless-ssid]\""
	lappend supplicant "  id_str=\"wireless\""
	if {[have_config wireless-password]} {
		lappend supplicant "  psk=\"[config_str wireless-password]\""
	}
	lappend supplicant "}"
	generate_file "/etc/wpa_supplicant/wpa-roam.conf" $supplicant 0600

	# the logical interface config fragment
	# this interface is brought up or down when wpa_supplicant notices
	# that the wireless is associated/disconnected; DHCP etc triggers
	# at that point. it is named matching the "id_str" parameter above
	add_network_interface wireless wireless

	incr ::networkInterfaces
}

proc configure_wired {} {
	if {![valid_network_config wired]} {
		return
	}

	# the physical interface config fragment
	add_network_interface wired eth0 {
		{auto eth0}
		{allow-hotplug eth0}
	}

	# override the ifplugd config
	generate_file "/etc/default/ifplugd" {
		{INTERFACES=""}
		{HOTPLUG_INTERFACES=""}
		{ARGS="-q -f -u0 -d10 -w -I"}
		{SUSPEND_ACTION="stop"}
	}

	incr ::networkInterfaces
}

proc valid_network_config {net} {
	if {![config_bool ${net}-network]} {
		return 0
	}

	if {![have_config ${net}-type]} {
		warn "Missing ${net}-type setting, not configuring the ${net} network"
		return 0
	}

	set type [config_str ${net}-type]
	switch -nocase $type {
		dhcp {
			return 1
		}

		static {
			if {![have_config ${net}-address]} {
				warn "Missing ${net}-address setting, not configuring the ${net} network"
				return 0
			}
			return 1
		}

		default {
			warn "${net}-type is set to '$type', which I don't understand (it should be dhcp or static)"
			return 0
		}
	}
}

proc add_network_interface {net iface {prefix ""} {suffix ""}} {
	set out $prefix

	set type [config_str ${net}-type]
	switch -nocase $type {
		dhcp {
			lappend out "iface $iface inet dhcp"
		}

		static {
			lappend out "iface $iface inet static"
			lappend out "  address [config_str ${net}-address]"
			if {[have_config ${net}-netmask]} {
				lappend out "  netmask [config_str ${net}-netmask]"
			}
			if {[have_config ${net}-broadcast]} {
				lappend out "  broadcast [config_str ${net}-broadcast]"
			}
			if {[have_config ${net}-gateway]} {
				lappend out "  gateway [config_str ${net}-gateway]"
			}
		}

		default {
			error "add_network_interface called with an invalid config (type $type)"
		}
	}

	lappend out {*}$suffix
	generate_file_part "/etc/network/interfaces" $out
}

proc generate_network_config {} {
	set ss [snapshot]

	# /etc/network/interfaces header
	generate_file "/etc/network/interfaces" {
		{auto lo}
		{iface lo inet loopback}
	}

	# default ifplugd config, unless overridden
	generate_file "/etc/default/ifplugd" {
		{INTERFACES=""}
		{HOTPLUG_INTERFACES=""}
		{ARGS="-q -f -u0 -d10 -w -I"}
		{SUSPEND_ACTION="stop"}
	}

	set ::networkInterfaces 0
	configure_wireless
	configure_wired

	if {$::networkInterfaces == 0} {
		warn "No network interfaces were configured; not updating system network config"
		restore_snapshot $ss
	}
}
