# Proton Mail Bridge — Headless Setup on Raspberry Pi

Quark requires Proton Mail Bridge to access your Proton Mail account via IMAP.
This guide walks through setting it up in headless (CLI) mode on a Raspberry Pi.

---

## Prerequisites

- Raspberry Pi running Raspberry Pi OS (64-bit recommended)
- A Proton Mail account (Free tier works, but Bridge requires a **paid plan**)
- SSH access to your Pi

---

## 1. Download Proton Bridge

Visit the official download page to get the latest ARM64 `.deb` package:

```
https://proton.me/mail/bridge
```

Look for the **Linux** download and select the ARM64 `.deb` version. Then on your Pi:

```bash
wget https://proton.me/download/bridge/proton-bridge_X.X.X_arm64.deb
sudo dpkg -i proton-bridge_*.deb
```

If you get dependency errors:

```bash
sudo apt-get install -f
```

---

## 2. Start Bridge in Headless Mode

```bash
proton-bridge --cli
```

You'll see a `>>>` prompt. Type `help` to see all available commands.

---

## 3. Log In

```bash
>>> login
```

Follow the prompts to enter your Proton Mail username and password.
If you have two-factor authentication enabled, you'll be asked for your 2FA code.

---

## 4. Get Your IMAP Credentials

Once logged in:

```bash
>>> info
```

This will display something like:

```
Configuration for your.email@proton.me
IMAP Settings
  Address:  127.0.0.1
  Port:     1143
  Username: your.email@proton.me
  Password: xxxxxxxxxxxxxxxxxxxx   <-- this is your Bridge password
  Security: STARTTLS
```

Copy the **Password** shown here — this is what goes in `.env` as `PROTON_BRIDGE_PASSWORD`.
It is different from your Proton Mail login password.

---

## 5. Keep Bridge Running

Bridge must be running for Quark to work. The simplest way to keep it alive is via a systemd service.

Create the service file:

```bash
sudo nano /etc/systemd/system/proton-bridge.service
```

Paste:

```ini
[Unit]
Description=Proton Mail Bridge
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/proton-bridge --cli --no-window
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable proton-bridge
sudo systemctl start proton-bridge
```

Check it's running:

```bash
sudo systemctl status proton-bridge
```

---

## 6. Verify the Connection

You can test that Bridge is reachable with:

```bash
python3 -c "
import imaplib
imap = imaplib.IMAP4('127.0.0.1', 1143)
print('Connected:', imap.welcome)
imap.logout()
"
```

If you see a welcome message, Bridge is running and Quark will be able to connect.

---

## Troubleshooting

**`dpkg` errors on install** — run `sudo apt-get install -f` to resolve missing dependencies.

**Bridge won't start** — check logs with `journalctl -u proton-bridge -f`.

**Wrong password error in Quark** — make sure you're using the Bridge password from `info`, not your Proton login password.

**Bridge loses login after reboot** — this can happen if the keyring isn't set up. Install `gnome-keyring` or `pass` and configure it as the secret store.
