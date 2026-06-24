import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import requests


class TokenSaver:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    def guilds(self):
        url = "https://discord.com/api/v9/users/@me/guilds"
        r = requests.get(url, headers=self.headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"error": f"Connection failed. Status: {r.status_code}",
                "message": r.text}

    def channels(self, guild_id):
        url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
        r = requests.get(url, headers=self.headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"error": f"Connection failed. Status: {r.status_code}",
                "message": r.text}

    def messages(self, channel_id, limit=10):
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        r = requests.get(url, headers=self.headers,
                         params={"limit": limit}, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"error": f"Fetch failed. Status: {r.status_code}",
                "message": r.text}

    def send_message(self, channel_id, content):
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        r = requests.post(url, headers=self.headers,
                          json={"content": content}, timeout=15)
        if r.status_code in (200, 201):
            return r.json()
        return {"error": f"Send failed. Status: {r.status_code}",
                "message": r.text}


BG       = "#1e1e1e"
BG_ALT   = "#2a2a2a"
BG_INPUT = "#333333"
FG       = "#e6e6e6"
FG_MUTED = "#9a9a9a"
ACCENT   = "#5865f2"
BORDER   = "#3a3a3a"


TEXTABLE_TYPES = {0, 5, 10, 11, 12, 15}


class OpSecApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpSec Client")
        self.geometry("860x720")
        self.configure(bg=BG)
        self.minsize(640, 560)

        self.token: str | None = None
        self.client: TokenSaver | None = None
        self.guild_map: dict[str, dict] = {}
        self.channel_map: dict[str, dict] = {}
        self.selected_server = tk.StringVar(value="(no server picked)")
        self.selected_channel = tk.StringVar(value="(no channel picked)")

        self._build_style()
        self._build_menubar()
        self._build_topbar()
        self._build_body()
        self._build_statusbar()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=FG_MUTED)

        style.configure("TButton", background=BG_INPUT, foreground=FG,
                        borderwidth=0, focusthickness=0, padding=(12, 6))
        style.map("TButton",
                  background=[("active", BORDER), ("pressed", ACCENT)],
                  foreground=[("active", FG)])

        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                        borderwidth=0, padding=(14, 7))
        style.map("Accent.TButton", background=[("active", "#4752c4")])

        style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT,
                        foreground=FG, arrowcolor=FG, borderwidth=0)
        self.option_add("*TCombobox*Listbox*Background", BG_INPUT)
        self.option_add("*TCombobox*Listbox*Foreground", FG)
        self.option_add("*TCombobox*Listbox*selectBackground", ACCENT)

    def _build_menubar(self):
        menubar = tk.Menu(self, bg=BG_ALT, fg=FG, activebackground=ACCENT,
                          activeforeground="#ffffff", borderwidth=0)

        server_menu = tk.Menu(menubar, tearoff=0, bg=BG_ALT, fg=FG,
                              activebackground=ACCENT, activeforeground="#ffffff")
        server_menu.add_command(label="Set Token...", command=self.set_token_dialog)
        server_menu.add_command(label="Refresh Servers", command=self.refresh_servers)
        server_menu.add_command(label="Refresh Channels", command=self.refresh_channels)
        server_menu.add_separator()
        server_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="Server", menu=server_menu)

        msg_menu = tk.Menu(menubar, tearoff=0, bg=BG_ALT, fg=FG,
                           activebackground=ACCENT, activeforeground="#ffffff")
        msg_menu.add_command(label="Send Message", command=self.send_message)
        msg_menu.add_command(label="Refresh Last 10", command=self.refresh_history)
        msg_menu.add_command(label="Clear Input", command=self.clear_message)
        menubar.add_cascade(label="Message", menu=msg_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=BG_ALT, fg=FG,
                            activebackground=ACCENT, activeforeground="#ffffff")
        help_menu.add_command(label="About",
            command=lambda: messagebox.showinfo("About", "OpSec Client v0.4"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG_ALT, height=88)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        row1 = tk.Frame(bar, bg=BG_ALT)
        row1.pack(fill="x", pady=(8, 2))
        tk.Label(row1, text="Server:", bg=BG_ALT, fg=FG_MUTED,
                 width=8, anchor="e").pack(side="left", padx=(12, 6))
        self.server_combo = ttk.Combobox(row1, state="readonly", width=36, values=[])
        self.server_combo.pack(side="left", padx=4)
        self.server_combo.bind("<<ComboboxSelected>>", self._on_server_selected)
        ttk.Button(row1, text="Refresh", command=self.refresh_servers).pack(side="left", padx=6)
        ttk.Button(row1, text="Token", command=self.set_token_dialog).pack(side="left", padx=2)
        tk.Label(row1, textvariable=self.selected_server,
                 bg=BG_ALT, fg=FG).pack(side="right", padx=12)

        row2 = tk.Frame(bar, bg=BG_ALT)
        row2.pack(fill="x", pady=(2, 8))
        tk.Label(row2, text="Channel:", bg=BG_ALT, fg=FG_MUTED,
                 width=8, anchor="e").pack(side="left", padx=(12, 6))
        self.channel_combo = ttk.Combobox(row2, state="readonly", width=36, values=[])
        self.channel_combo.pack(side="left", padx=4)
        self.channel_combo.bind("<<ComboboxSelected>>", self._on_channel_selected)
        ttk.Button(row2, text="Refresh", command=self.refresh_channels).pack(side="left", padx=6)
        tk.Label(row2, textvariable=self.selected_channel,
                 bg=BG_ALT, fg=FG).pack(side="right", padx=12)

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=12)

        
        header = tk.Frame(body, bg=BG)
        header.pack(fill="x")
        ttk.Label(header, text="Last 10 messages", style="Muted.TLabel").pack(side="left")
        ttk.Button(header, text="Reload", command=self.refresh_history).pack(side="right")

        hist_wrap = tk.Frame(body, bg=BORDER)
        hist_wrap.pack(fill="both", expand=True, pady=(4, 10))

        self.history = tk.Text(hist_wrap, bg=BG_INPUT, fg=FG, insertbackground=FG,
                               relief="flat", padx=10, pady=10, wrap="word",
                               state="disabled", height=12,
                               font=("Segoe UI", 10))
        self.history.pack(fill="both", expand=True, padx=1, pady=1)
        
        self.history.tag_configure("author", foreground=ACCENT,
                                   font=("Segoe UI", 10, "bold"))
        self.history.tag_configure("time", foreground=FG_MUTED,
                                   font=("Segoe UI", 9))

        ttk.Label(body, text="Message", style="Muted.TLabel").pack(anchor="w")

        text_wrap = tk.Frame(body, bg=BORDER)
        text_wrap.pack(fill="x", pady=(4, 10))

        self.message = tk.Text(text_wrap, bg=BG_INPUT, fg=FG, insertbackground=FG,
                               relief="flat", padx=10, pady=10, wrap="word",
                               undo=True, height=5, font=("Segoe UI", 10))
        self.message.pack(fill="x", padx=1, pady=1)

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")
        ttk.Button(actions, text="Clear", command=self.clear_message).pack(side="left")
        ttk.Button(actions, text="Send", style="Accent.TButton",
                   command=self.send_message).pack(side="right")

    def _build_statusbar(self):
        self.status = tk.StringVar(value="No token set.")
        bar = tk.Frame(self, bg=BG_ALT, height=24)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status, bg=BG_ALT,
                 fg=FG_MUTED, anchor="w").pack(side="left", padx=12)

    def set_token_dialog(self):
        token = simpledialog.askstring("Discord Token", "Paste token:",
                                       parent=self, show="*")
        if not token:
            return
        self.token = token.strip()
        self.client = TokenSaver(self.token)
        self.status.set("Token set. Pulling servers...")
        self.refresh_servers()

    def refresh_servers(self):
        if not self.client:
            messagebox.showwarning("No token", "Set a token first.")
            return
        self.status.set("Loading servers...")
        threading.Thread(target=self._load_guilds_worker, daemon=True).start()

    def _load_guilds_worker(self):
        try:
            data = self.client.guilds()
        except Exception as e:  
            self.after(0, lambda: self._error(f"Server error: {e}"))
            return
        self.after(0, lambda: self._on_guilds_loaded(data))

    def _on_guilds_loaded(self, data):
        if isinstance(data, dict) and data.get("error"):
            self._error(f"{data.get('error')} — {data.get('message','')}")
            return
        if not isinstance(data, list):
            self._error("Unexpected response shape.")
            return

        self.guild_map = {}
        names = []
        for g in data:
            name = g.get("name") or f"(unnamed {g.get('id','?')})"
            label = name if name not in self.guild_map else f"{name}  [{g.get('id')}]"
            self.guild_map[label] = g
            names.append(label)

        names.sort(key=str.casefold)
        self.server_combo["values"] = names
        if names:
            self.server_combo.current(0)
            self._on_server_selected()
            self.status.set(f"{len(names)} servers loaded.")
        else:
            self.selected_server.set("(no servers)")
            self.status.set("No servers on this account.")

    def _on_server_selected(self, _event=None):
        label = self.server_combo.get()
        if not label:
            return
        guild = self.guild_map.get(label, {})
        gid = guild.get("id", "?")
        self.selected_server.set(f"{label}  ({gid})")
        self.status.set(f"Picked: {label} — loading channels...")
        self.channel_map = {}
        self.channel_combo.set("")
        self.channel_combo["values"] = []
        self.selected_channel.set("(no channel picked)")
        self._set_history_text("(pick a channel)")
        self.refresh_channels()

    def selected_guild(self) -> dict | None:
        return self.guild_map.get(self.server_combo.get())

    def refresh_channels(self):
        if not self.client:
            messagebox.showwarning("No token", "Set a token first.")
            return
        guild = self.selected_guild()
        if not guild:
            self.status.set("Pick a server first.")
            return
        gid = guild.get("id")
        threading.Thread(target=self._load_channels_worker,
                         args=(gid,), daemon=True).start()

    def _load_channels_worker(self, gid):
        try:
            data = self.client.channels(gid)
        except Exception as e: 
            self.after(0, lambda: self._error(f"Channel error: {e}"))
            return
        self.after(0, lambda: self._on_channels_loaded(data))

    def _on_channels_loaded(self, data):
        if isinstance(data, dict) and data.get("error"):
            self._error(f"{data.get('error')} — {data.get('message','')}")
            return
        if not isinstance(data, list):
            self._error("Unexpected channel response.")
            return

        chans = [c for c in data if c.get("type") in TEXTABLE_TYPES]
        chans.sort(key=lambda c: (c.get("position", 0), c.get("name", "")))

        self.channel_map = {}
        labels = []
        for c in chans:
            name = c.get("name") or c.get("id", "?")
            label = f"#{name}"
            if label in self.channel_map:
                label = f"#{name}  [{c.get('id')}]"
            self.channel_map[label] = c
            labels.append(label)

        self.channel_combo["values"] = labels
        if labels:
            self.channel_combo.current(0)
            self._on_channel_selected()
            self.status.set(f"{len(labels)} channels loaded.")
        else:
            self.selected_channel.set("(no writable channels)")
            self.status.set("No writable channels here.")

    def _on_channel_selected(self, _event=None):
        label = self.channel_combo.get()
        if not label:
            return
        ch = self.channel_map.get(label, {})
        cid = ch.get("id", "?")
        self.selected_channel.set(f"{label}  ({cid})")
        
        self.refresh_history()

    def selected_channel_obj(self) -> dict | None:
        return self.channel_map.get(self.channel_combo.get())


    def refresh_history(self):
        if not self.client:
            return
        ch = self.selected_channel_obj()
        if not ch:
            return
        cid = ch.get("id")
        self._set_history_text("Loading...")
        threading.Thread(target=self._load_history_worker,
                         args=(cid,), daemon=True).start()

    def _load_history_worker(self, cid):
        try:
            data = self.client.messages(cid, limit=10)
        except Exception as e:  # noqa: BLE001
            self.after(0, lambda: self._set_history_text(f"History error: {e}"))
            return
        self.after(0, lambda: self._on_history_loaded(data))

    def _on_history_loaded(self, data):
        if isinstance(data, dict) and data.get("error"):

            self._set_history_text(
                f"{data.get('error')}\n{data.get('message','')}")
            return
        if not isinstance(data, list):
            self._set_history_text("Unexpected history response.")
            return
        if not data:
            self._set_history_text("(no messages here yet)")
            return

        data = list(reversed(data))
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        for m in data:
            author = (m.get("author") or {}).get("username", "?")
            ts = (m.get("timestamp") or "")[:19].replace("T", " ")
            content = m.get("content") or ""
            if not content:

                if m.get("attachments"):
                    content = f"[{len(m['attachments'])} attachment(s)]"
                elif m.get("embeds"):
                    content = f"[{len(m['embeds'])} embed(s)]"
                else:
                    content = "(empty)"
            self.history.insert("end", author, "author")
            self.history.insert("end", f"  {ts}\n", "time")
            self.history.insert("end", content + "\n\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def _set_history_text(self, text: str):
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.insert("end", text)
        self.history.configure(state="disabled")

    def send_message(self):
        if not self.client:
            messagebox.showwarning("No token", "Set a token first.")
            return
        ch = self.selected_channel_obj()
        if not ch:
            self.status.set("Pick a channel first.")
            return
        content = self.message.get("1.0", "end").strip()
        if not content:
            self.status.set("Empty message, skipped.")
            return

        cid = ch.get("id")
        self.status.set(f"Sending -> #{ch.get('name')} ...")
        threading.Thread(target=self._send_worker,
                         args=(cid, content), daemon=True).start()

    def _send_worker(self, cid, content):
        try:
            res = self.client.send_message(cid, content)
        except Exception as e: 
            self.after(0, lambda: self._error(f"Send error: {e}"))
            return
        self.after(0, lambda: self._on_sent(res))

    def _on_sent(self, res):
        if isinstance(res, dict) and res.get("error"):
            self._error(f"{res.get('error')} — {res.get('message','')}")
            return
        self.status.set("Message sent.")
        self.message.delete("1.0", "end")

        self.refresh_history()

    def clear_message(self):
        self.message.delete("1.0", "end")
        self.status.set("Input cleared.")

    def _error(self, msg: str):
        self.status.set(f"Error: {msg}")
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    OpSecApp().mainloop()
