PREFIX = $(DESTDIR)/usr

.PHONY : dist debian mac

debian: sdist
	debuild -us -uc -b

mac:
	python setup.py py2app

sdist:
	python setup.py sdist

clean:
	rm -f src/*.pyc
	rm -f MANIFEST
	rm -rf build dist
	if [ -f "/etc/debian_version" ]; then dh_clean; fi

install: sdist
	python setup.py install

uninstall:
	rm -rf $(PREFIX)/share/derp
	rm -f $(PREFIX)/bin/derp
