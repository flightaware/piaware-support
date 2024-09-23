#
# piaware-support top-level Makefile
#

all:
	$(MAKE) -C package

# Generating the splashscreen has a heavyweight set of dependencies
# so this target is not called automatically during the build process.
# (you should install imagemagick / ghostscript if you need to run
# this target)
splash:
	splashscreen/make-splashscreen.sh $(shell dpkg-parsechangelog -S Version) plymouth/splash.png
