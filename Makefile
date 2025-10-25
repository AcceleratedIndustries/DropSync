.PHONY: pipx install-arch install-debian install-macos service run organize lint fmt test publish clean

pipx:
	pipx install --force .

install-arch:
	./scripts/install_arch.sh

install-debian:
	./scripts/install_debian.sh

install-macos:
	./scripts/install_macos.sh

service:
	mkdir -p ~/.config/systemd/user
	cp systemd/dropsync.service ~/.config/systemd/user/
	cp systemd/dropsync-organize.service ~/.config/systemd/user/
	cp systemd/dropsync-organize.timer ~/.config/systemd/user/
	systemctl --user daemon-reload
	systemctl --user enable --now dropsync.service
	systemctl --user enable --now dropsync-organize.timer

run:
	dropsync run

organize:
	dropsync organize

lint:
	ruff check .
	black --check .
	mypy dropsync

fmt:
	ruff check --fix .
	ruff format .
	black .

test:
	pytest

publish:
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		git remote add origin git@github.com:WilliamAppleton/DropSync.git || git remote add origin https://github.com/WilliamAppleton/DropSync.git; \
	fi
	git push -u origin main
	@if command -v gh >/dev/null 2>&1; then \
		gh release create v0.1.0 --draft --notes-file RELEASE_TEMPLATE.md || true; \
	fi

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
