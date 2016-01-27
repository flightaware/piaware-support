#!/usr/bin/tclsh8.6

#
# Reads a short config file from /boot and generates system
# configuration to match. Runs early during boot.
#

package require cmdline
package require fa_piaware_config

set scriptdir [file dirname [info script]]
source [file join $scriptdir "helpers.tcl"]
source [file join $scriptdir "network.tcl"]
source [file join $scriptdir "dump1090.tcl"]

proc update_system_config_files {} {
	if {![piawareConfig get manage-config]} {
		log "manage-config is not set, nothing to do."
		return
	}

	set didSomething 0
	if {$::params(network) && [generate_network_config]} {
		set didSomething 1
	}

	if {$::params(dump1090) && [generate_dump1090_config]} {
		set didSomething 1		
	}

	flush_generated_files

	if {!$didSomething} {
		log "No config files generated"
	}
}

proc main {{argv ""}} {
	set opts {
		{network "generate network config"}
		{dump1090 "generate dump1090 config"}
		{dryrun "just show the new file contents, don't try to install them"}
    }

    set usage ": $::argv0 ?-dryrun? ?-config configfile? -network"

    if {[catch {array set ::params [::cmdline::getoptions argv $opts $usage]} catchResult] == 1} {
        puts stderr $catchResult
        exit 1
    }

	::fa_piaware_config::new_combined_config piawareConfig
	piawareConfig read_config

	try {
		update_system_config_files
	} on error {result _options} {
		array set options $_options
		warn "Failed to update system config files: $options(-errorinfo)"
		return
	}
}

if {!$tcl_interactive} {
	main $argv
}
