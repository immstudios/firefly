build:
	poetry run briefcase create
	poetry run briefcase build

install:
	cp firefly.desktop ~/.local/share/applications/firefly.desktop
	echo 'Path=$(CURDIR)' >> ~/.local/share/applications/firefly.desktop
	echo 'Icon=$(CURDIR)/images/icon.png' >> ~/.local/share/applications/firefly.desktop
