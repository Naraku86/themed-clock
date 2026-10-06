.DEFAULT_GOAL := test
PREFIX ?= $(HOME)/.local

.PHONY: test install previews

test:
	python3 tests/test_clock.py

install:
	install -Dm755 clock.py "$(DESTDIR)$(PREFIX)/bin/themed-clock"
	install -Dm644 config.ini.example "$(DESTDIR)$(PREFIX)/share/themed-clock/config.ini.example"

previews:
	python3 scripts/render_previews.py
