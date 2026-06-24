# SimpleCord
---

Discord Token Manager

A small Tkinter desktop tool I built to juggle multiple Discord accounts from one window. You drop in your tokens, pick a server and a channel, and you can send messages or peek at the last 10 messages in that channel without opening the Discord client.

> Heads up: automating user accounts is against Discord's ToS. Use it on accounts you don't mind losing. I wrote this for personal testing, not for spamming.

Features

- Save and switch between multiple tokens
- Auto-fetches the servers (guilds) each token is in
- Lists the text channels of the selected server
- Sends messages as the selected account
- Shows the last 10 messages of the active channel (with author + timestamp)
- Manual "Reload" button so you don't hammer the API
- Auto-refreshes the history right after you send a message
- Fully in English, single-file script

Requirements

- Python 3.9+
- `requests` library

```bash
pip install requests
```

Tkinter ships with Python on Windows and macOS. On Linux you may need:

```bash
sudo apt install python3-tk
```

Running it

```bash
python discord_tool.py
```

(Use whatever you named the file.)

How to use

1. Add a token — `Server` menu → `Add Token`. Paste your user token and give it a label.
2. Pick an account — choose it from the token dropdown at the top.
3. Pick a server — the `Server` dropdown fills in automatically once the token loads.
4. Pick a channel — the `Channel` dropdown shows the text channels you have access to.
5. Read — the last 10 messages appear in the panel above the input box. Hit Reload to pull the latest.
6. Send — type into the message box at the bottom and hit `Send`. The history refreshes itself afterwards.

Getting your token

I'm not going to walk through this step by step — if you know what this tool is for, you already know where to find it (DevTools → Network → any authenticated request → `authorization` header). Don't share it with anyone, ever.

Notes

- The history is capped at 10 messages on purpose, to stay friendly with Discord's rate limits.
- If a token stops working, Discord probably invalidated it — re-login in the browser and grab a fresh one.
- Tokens are stored locally in plain text next to the script. Don't commit that file to git.

Disclaimer

This is a learning project. I'm not responsible for banned accounts, broken servers, or anything else that happens if you misuse it. Be smart.
