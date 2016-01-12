#
# dump1090 configuration, invoked from configure-system.tcl
#

proc generate_dump1090_config {} {
	set dump1090config {
		{DECODER_OPTIONS="--max-range $MAX_RANGE"}
		{NET_OPTIONS="--net --net-heartbeat 60 --net-ro-size 1000 --net-ro-interval 1 --net-http-port 0 --net-ri-port 0 --net-ro-port 30002 --net-sbs-port 30003 --net-bi-port 30104"}
		{JSON_OPTIONS="--json-location-accuracy 2"}
	}

	switch -nocase [config_str receiver-type "rtlsdr"] {
		rtlsdr {
			set index [config_str rtlsdr-device-index 0]
			set gain [config_str rtlsdr-gain -10]
			set ppm [config_str rtlsdr-ppm 0]
			lappend dump1090config "RECEIVER_OPTIONS=\"--device-index $index --gain $gain --ppm $ppm --oversample --phase-enhance --net-bo-port 30005 --fix\""
		}

		beast - radarcape - other {
			lappend dump1090config "RECEIVER_OPTIONS=\"--net-only --net-bo-port 0\""
		}

		none {
			# no config at all
			return 0
		}

		default {
			warn "unrecognized receiver type '[config_str receiver-type]', not configuring dump1090"
			# no config
			return 0
		}
	}

	generate_file "/etc/default/dump1090-fa" $dump1090config
	return 1
}

