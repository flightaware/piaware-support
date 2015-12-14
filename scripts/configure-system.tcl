#!/usr/bin/tclsh8.6

#
# Reads a short config file from /boot and generates system
# configuration to match. Runs early during boot.
#

package require cmdline

set scriptdir [file dirname [info script]]
source [file join $scriptdir "helpers.tcl"]
source [file join $scriptdir "network.tcl"]

proc update_system_config_files {} {
	if {![config_bool manage-config]} {
		log "manage-config is not set, nothing to do."
		return
	}

	set didSomething 0
	if {$::params(network)} {
		set didSomething 1
		generate_network_config
	}

	flush_generated_files

	if {!$didSomething} {
		log "No actions specified, nothing was done"
	}
}

proc main {{argv ""}} {
	set opts {
		{config.arg "/boot/piaware-config.txt" "specify the config file to read"}
		{network "generate network config"}
		{dryrun "just show the new file contents, don't try to install them"}
    }

    set usage ": $::argv0 ?-dryrun? ?-config configfile? -network"

    if {[catch {array set ::params [::cmdline::getoptions argv $opts $usage]} catchResult] == 1} {
        puts stderr $catchResult
        exit 1
    }

	try {
		set lines [read_file $::params(config)]
		if {[llength $lines] == 0} {
			log "Not updating system configuration, $::params(config) missing or empty"
			return
		}

		parse_config_file $lines
	} on error {result _options} {
		array set options $_options
		warn "Failed to read config file, not updating system configuration: $options(-errorinfo)"
		return
	}

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
