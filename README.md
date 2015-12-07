# piaware-support
Support package for Piaware sdcard images

This builds a Debian package that manages the stuff specific to a Piaware sdcard image:

 * Installs a service that, on first boot, generates new ssh host keys
 * Installs a keyring and apt configuration to point at the Flightaware repository
