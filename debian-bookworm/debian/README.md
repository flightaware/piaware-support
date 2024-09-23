# piaware-support
Support package for Piaware sdcard images

This builds a Debian package that manages the stuff specific to a Piaware
sdcard image:

 * apt configuration for the FlightAware repository
 * Boot splashscreen
 * First-boot generation of ssh host keys
 * Applying network and receiver configuration from piaware-config.txt
   settings
 * Text-mode status display on the first virtual console
 * initramfs support
 * Management of /boot/config.txt when kernels or initramfs are updated
 * Warns about default passwords when ssh is enabled
