#
# dump1090 configuration, invoked from configure-system.tcl
#

proc generate_dump1090_config {} {
	set dump1090config {
		{DECODER_OPTIONS="--max-range 300"}
		{NET_OPTIONS="--net --net-heartbeat 60 --net-ro-size 1000 --net-ro-interval 1 --net-http-port 0 --net-ri-port 0 --net-ro-port 30002 --net-sbs-port 30003 --net-bi-port 30104"}
		{JSON_OPTIONS="--json-location-accuracy 2"}
	}

	switch -nocase [piawareConfig get receiver-type] {
		rtlsdr {
			set index [piawareConfig get rtlsdr-device-index]
			set gain [piawareConfig get rtlsdr-gain]
			set ppm [piawareConfig get rtlsdr-ppm]
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
			warn "unrecognized receiver type '[piawareConfig get receiver-type]', not configuring dump1090"
			# no config
			return 0
		}
	}

	generate_file "/etc/default/dump1090-fa" $dump1090config
	return 1
}

