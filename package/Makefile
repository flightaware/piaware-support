PREFIX=/usr
LIB=$(PREFIX)/lib/fa_piaware_support
TCLSH=$(shell which tclsh || which tclsh8.6 || which tclsh8.5)

FILES=fa_config_generator.tcl

all: pkgIndex.tcl

install:
	$(MAKE) -C helpers install

pkgIndex.tcl: $(FILES)
	echo 'pkg_mkIndex .' | $(TCLSH)
