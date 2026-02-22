# Quark

Quark is a lightweight Python script that automatically sorts GitHub notification emails in your Proton Mail account into per-repository folders. It runs on a Raspberry Pi (or any Linux machine) and creates new folders on the fly as emails from new repositories arrive.

```
📁 GitHub/
   📁 torvalds/
      📁 linux
   📁 your-username/
      📁 my-cool-project
      📁 another-repo
```

---

## How It Works

Quark connects to your Proton Mail account via [Proton Mail Bridge](https://proton.me/mail/bridge) using IMAP. It checks your inbox for unseen emails, identifies GitHub notification emails, extracts the repository owner and name, and moves each email into the appropriate folder — creating it first if it doesn't exist.

It runs on a schedule via cron, so everything stays sorted automatically.

---

## Prerequisites

- A Proton Mail **paid plan** (required for Bridge access)
- Proton Mail Bridge installed and running in headless mode on your Pi
- Python 3.7+

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/quark.git
cd quark
```

### 2. Install Proton Mail Bridge

Follow the guide in [`docs/bridge-setup.md`](docs/bridge-setup.md) to install and configure Bridge in headless/CLI mode on your Raspberry Pi.

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Configure Your Environment

```bash
cp .env.example .env
nano .env
```

Fill in your Proton Mail address and the Bridge password (shown by the `info` command in the Bridge CLI — this is different from your Proton login password).

### 5. Test the Script

Run it manually to verify everything is working:

```bash
python3 quark.py
```

Check `logs/quark.log` for output, or watch the terminal directly.

### 6. Schedule with Cron

To run Quark every 5 minutes automatically:

```bash
crontab -e
```

Add:

```
*/5 * * * * /usr/bin/python3 /home/pi/quark/quark.py
```

---

## Configuration

All configuration is done via the `.env` file. See `.env.example` for all available options.

| Variable | Default | Description |
|---|---|---|
| `IMAP_HOST` | `127.0.0.1` | Proton Bridge IMAP host |
| `IMAP_PORT` | `1143` | Proton Bridge IMAP port |
| `PROTON_USERNAME` | — | Your Proton Mail address |
| `PROTON_BRIDGE_PASSWORD` | — | Your Bridge password (not your Proton login) |
| `GITHUB_FOLDER_PREFIX` | `GitHub` | Top-level folder for sorted emails |

---

## Logs

Logs are written to `logs/quark.log`. The log file rotates automatically at 1 MB, keeping up to 4 files of history.

To watch logs in real time:

```bash
tail -f logs/quark.log
```

---

## Project Structure

```
quark/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── .env                  # Your local config (gitignored)
├── quark.py              # Main script
├── requirements.txt
├── logs/
│   └── .gitkeep
└── docs/
    └── bridge-setup.md   # Proton Bridge headless setup guide
```

---

## License

MIT
