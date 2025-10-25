# Uninstalling DropSync

1. Stop and disable services:

   ```bash
   systemctl --user disable --now dropsync.service dropsync-organize.timer
   ```

2. Remove the pipx package:

   ```bash
   pipx uninstall dropsync
   ```

3. Optionally delete configuration and data:

   ```bash
   rm -rf ~/.config/dropsync
   rm -rf ~/Sync/Collect/.dropsync
   # Decide whether to keep captured data under ~/Sync/Collect
   ```

4. Remove systemd unit files if copied:

   ```bash
   rm ~/.config/systemd/user/dropsync.service
   rm ~/.config/systemd/user/dropsync-organize.service
   rm ~/.config/systemd/user/dropsync-organize.timer
   systemctl --user daemon-reload
   ```

5. (Optional) Clean Syncthing ignores or remote folders created for DropSync output.

To reinstall, simply rerun the steps in [`INSTALL.md`](INSTALL.md).
