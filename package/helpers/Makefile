PREFIX=/usr
LIB=$(PREFIX)/lib/piaware-support/helpers
FILES=piaware-restart-network

all:

install: $(FILES)
	install -d $(DESTDIR)$(PREFIX)/bin $(DESTDIR)$(LIB)
	install -m 0755 $(FILES) $(DESTDIR)$(PREFIX)/bin
	install $(FILES) $(DESTDIR)$(LIB)
