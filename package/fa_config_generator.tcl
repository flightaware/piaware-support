package require cmdline
package require fa_piaware_config
catch {package require fa_flightfeeder_config}

namespace eval ::fa_config_generator {
	proc logger {msg} {
		puts stderr $msg
	}

	proc replace_file {path mode lines {dryrun 0}} {
		if {$dryrun} {
			logger "Dryrun: new contents of $path (mode $mode):"
			logger "==============================================="
			foreach line $lines {
				logger $line
			}
			logger "==============================================="
			return
		}

		logger "Updating $path .."

		set backup ${path}.old
		set tmp ${path}.new

		set f [open $tmp "w" $mode]
		try {
			chan configure $f -encoding ascii -translation lf
			foreach line $lines {
				puts $f $line
			}
		} finally {
			close $f
		}

		if {[file exists $path]} {
			file copy -force $path $backup
		}

		file rename -force $tmp $path
	}

	proc generate_file {path text {mode 0644} {comment "#"}} {
		if {$comment ne ""} {
			lappend ::newfiletext($path) "$comment Generated automatically by fa_config_generator"
			lappend ::newfiletext($path) "$comment This file will be overwritten on reboot."
		}
		lappend ::newfiletext($path) {*}$text
		set ::newfilemode($path) $mode
    }

	proc generate_file_part {path text {mode 0644} {comment "#"}} {
		if {![info exists ::newfiletext($path)]} {
			generate_file $path $text $mode $comment
		} else {
			lappend ::newfiletext($path) "" {*}$text
		}
	}

	proc flush_generated_files {{dryrun 0}} {
		foreach path [array names ::newfiletext] {
			replace_file $path $::newfilemode($path) $::newfiletext($path) $dryrun
		}
	}

	proc snapshot {} {
		return [list [array get ::newfiletext] [array get ::newfilemode]]
	}

	proc restore_snapshot {ss} {
		lassign $ss texts modes
		array unset ::newfiletext
		array unset ::newfilemode
		array set ::newfiletext $texts
		array set ::newfilemode $modes
	}

	proc generate_from_argv {command argv} {
		set opts {
			{dryrun "just show the new file contents, don't try to install them"}
		}

		set usage ": $::argv0 ?-dryrun?"

		if {[catch {array set params [::cmdline::getoptions argv $opts $usage]} catchResult] == 1} {
			logger $catchResult
			return
		}

		set config [::fa_piaware_config::new_combined_config #auto]
		$config read_config

		if {![$config get manage-config]} {
			logger "manage-config is not set, nothing to do."
			return
		}

		try {
			{*}$command $config
			flush_generated_files $params(dryrun)
		} on error {result _options} {
			array set options $_options
			logger "Failed to update system config files: $options(-errorinfo)"
			return
		}
	}		
}

package provide fa_config_generator 0.1
