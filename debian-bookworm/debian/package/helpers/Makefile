PREFIX=/usr
BIN=$(PREFIX)/bin
FILES=piaware-restart-network piaware-restart-receiver

all:

install: $(FILES)
	install -d $(DESTDIR)$(BIN)
	install -m 0755 $(FILES) $(DESTDIR)$(BIN)
