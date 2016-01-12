#
# piaware configuration, invoked from configure-system.tcl
#

proc generate_piaware_config {} {
	set piawareconfig [list \
						   [list autoUpdates [config_bool allow-auto-updates 1]] \
						   [list manualUpdates [config_bool allow-manual-updates 1]]]
	
	switch -nocase [config_str receiver-type "rtlsdr"] {
		rtlsdr {
			lappend piawareconfig [list receiverType "rtlsdr"]
		}

		beast {
			lappend piawareconfig [list receiverType "beast"]
		}

		radarcape {
			if {![have_config radarcape-host]} {
				warn "receiver-type is 'radarcape' but radarcape-host was not set; not configuring piaware's receiver settings"
			}
			lappend piawareconfig [list receiverType "radarcape"] [list receiverHost [config_str radarcape-host]] [list receiverPort 10003]
		}

		other {
			if {![have_config receiver-host]} {
				warn "receiver-type is 'other' but receiver-host was set; not configuring piaware's receiver settings"
			} else if {![have_config receiver-port]} {
				warn "receiver-type is 'other' but receiver-port was set; not configuring piaware's receiver settings"
			} else {
				lappend piawareconfig [list receiverType "other"] [list receiverHost [config_str receiver-host]] [list receiverPort [config_str receiver-port]]
			}
		}

		none {
			# no config at all
		}

		default {
			warn "unrecognized receiver type '[config_str receiver-type]', not configuring piaware's receiver settings"
		}
	}

	# FIXME this needs to move to /etc
	# FIXME the piaware parser needs to deal with comments
	generate_file "/root/.piaware" $piawareconfig 0600 0
	return 1
}

