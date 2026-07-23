#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wumpusnuker — deletes your messages from a Discord channel or server.

WARNING: automating a user account violates Discord's Terms of Service
and can result in a ban. Use at your own risk.

x crypt0xf
"""

import os
import re
import sys
import json
import time
import getpass
import shutil
import threading
import itertools
from urllib import request as urlrequest
from urllib import parse as urlparse
from urllib.error import HTTPError, URLError

API = "https://discord.com/api/v10"
_SIG = "".join(chr(c) for c in (99, 114, 121, 112, 116, 48, 120, 102))

# Windows: enable UTF-8 + ANSI escape codes
if os.name == "nt":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

C = {
    "r": "\033[0m", "b": "\033[1m", "dim": "\033[2m", "it": "\033[3m",
    "red": "\033[38;5;203m", "grn": "\033[38;5;114m", "yel": "\033[38;5;221m",
    "cyn": "\033[38;5;80m", "mag": "\033[38;5;176m", "blu": "\033[38;5;111m",
    "gry": "\033[38;5;245m", "wht": "\033[38;5;255m",
    "hide": "\033[?25l", "show": "\033[?25h",
}
BOX = dict(tl="╭", tr="╮", bl="╰", br="╯", h="─", v="│", ml="├", mr="┤")


def col(txt, *cols):
    return "".join(C[x] for x in cols) + str(txt) + C["r"]


def term_w():
    return min(shutil.get_terminal_size((70, 24)).columns, 74)


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write(C["hide"]); sys.stdout.flush()


def show_cursor():
    sys.stdout.write(C["show"]); sys.stdout.flush()


# visible width ignoring ANSI codes (keeps boxes aligned)
def _vislen(s):
    return len(re.sub(r"\033\[[0-9;?]*[a-zA-Z]", "", s))


# ---------- UI ----------
def box_top(w, title=""):
    if title:
        t = f" {title} "
        fill = w - 2 - _vislen(t)
        return col(BOX["tl"] + BOX["h"] * 2, "cyn") + col(t, "b", "wht") + \
            col(BOX["h"] * (fill - 2) + BOX["tr"], "cyn")
    return col(BOX["tl"] + BOX["h"] * (w - 2) + BOX["tr"], "cyn")


def box_bot(w):
    return col(BOX["bl"] + BOX["h"] * (w - 2) + BOX["br"], "cyn")


def box_sep(w):
    return col(BOX["ml"] + BOX["h"] * (w - 2) + BOX["mr"], "cyn")


def box_line(w, content=""):
    pad = max(w - 2 - _vislen(content), 0)
    return col(BOX["v"], "cyn") + " " + content + " " * (pad - 1) + col(BOX["v"], "cyn")


# ---------- animations ----------
class Spinner:
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, text=""):
        self.text = text
        self._stop = threading.Event()
        self._th = None

    def _spin(self):
        for f in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                break
            sys.stdout.write(col(f"\r  {f} ", "cyn") + col(self.text, "gry") + "  ")
            sys.stdout.flush()
            time.sleep(0.08)

    def __enter__(self):
        hide_cursor()
        self._th = threading.Thread(target=self._spin, daemon=True)
        self._th.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        if self._th:
            self._th.join()
        sys.stdout.write("\r" + " " * term_w() + "\r")
        sys.stdout.flush()
        show_cursor()


def progress_bar(done, total, width=30, label=""):
    total = max(total, 1)
    ratio = min(done / total, 1.0)
    filled = int(ratio * width)
    bar = col("█" * filled, "grn") + col("░" * (width - filled), "gry")
    sys.stdout.write(f"\r  {bar} {col(f'{ratio*100:4.0f}%','wht')} {col(label,'gry')}   ")
    sys.stdout.flush()


def flash(msg, color, times=3):
    for _ in range(times):
        sys.stdout.write("\r  " + col(msg, color, "b") + "   ")
        sys.stdout.flush()
        time.sleep(0.18)
        sys.stdout.write("\r" + " " * term_w() + "\r")
        sys.stdout.flush()
        time.sleep(0.12)
    sys.stdout.write("\r  " + col(msg, color, "b") + "\n")


# ---------- API ----------
def clean_token(raw):
    t = raw.strip().strip('"').strip("'").strip()
    return re.sub(r"\s+", "", t)


class DiscordAPI:
    def __init__(self, token):
        self.token = clean_token(token)
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

    def _req(self, method, path, params=None, body=None):
        url = f"{API}{path}"
        if params:
            url += "?" + urlparse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urlrequest.Request(url, data=data, headers=self.headers, method=method)
        while True:
            try:
                with urlrequest.urlopen(req, timeout=30) as r:
                    raw = r.read()
                    return json.loads(raw) if raw else {}
            except HTTPError as e:
                if e.code == 429:
                    try:
                        wait = float(json.loads(e.read()).get("retry_after", 1)) + 0.3
                    except Exception:
                        wait = 2.0
                    sys.stdout.write(col(f"\r  ⏳ rate limited, waiting {wait:.1f}s   ", "yel"))
                    sys.stdout.flush()
                    time.sleep(wait)
                    continue
                if e.code >= 500:
                    time.sleep(2)
                    continue
                raise
            except URLError:
                time.sleep(2)
                continue

    def me(self):
        return self._req("GET", "/users/@me")

    def guild_channels(self, guild_id):
        chans = self._req("GET", f"/guilds/{guild_id}/channels")
        return [x for x in chans if x.get("type") in (0, 5)]  # text + announcements

    def get_messages(self, channel_id, before=None, limit=100):
        params = {"limit": limit}
        if before:
            params["before"] = before
        return self._req("GET", f"/channels/{channel_id}/messages", params=params)

    def delete_message(self, channel_id, message_id):
        return self._req("DELETE", f"/channels/{channel_id}/messages/{message_id}")


# ---------- screens ----------
def banner():
    clear()
    hide_cursor()
    w = term_w()
    print()
    print(col("  ◈ ", "mag") + col("wumpusnuker", "mag", "b") + col("  ·  discord message wiper", "dim"))
    print()
    print(box_top(w, "wumpusnuker"))
    print(box_line(w, col("deletes your messages from a channel or server", "gry", "it")))
    print(box_sep(w))
    print(box_line(w, col("⚠  ", "yel") + col("automating a user account violates Discord's ToS", "yel")))
    print(box_line(w, col("   and can result in a ", "yel") + col("BAN", "red", "b") + col(".", "yel")))
    print(box_line(w, col(f"by {_SIG}", "dim")))
    print(box_bot(w))
    show_cursor()
    print()


def ask(prompt, default=None):
    suffix = col(f" [{default}]", "dim") if default is not None else ""
    v = input(col("  ❯ ", "cyn") + col(prompt, "wht") + suffix + col("  ", "cyn")).strip()
    return v or (default or "")


def login():
    while True:
        print(col("  Paste the account token ", "gry") + col("(hidden input)", "dim"))
        print(col("  DevTools → Network → request to discord.com/api", "dim"))
        print(col("  → Headers → authorization", "dim"))
        raw = getpass.getpass(col("  🔑 token: ", "cyn"))
        if not raw.strip():
            flash("empty token.", "red", 2)
            continue
        api = DiscordAPI(raw)
        try:
            with Spinner("validating token…"):
                u = api.me()
            flash(f"✓ logged in as {u['username']}", "grn", 2)
            print(col(f"     id: {u['id']}\n", "dim"))
            return api, u["id"]
        except HTTPError as e:
            if e.code == 401:
                flash("✗ [401] invalid or expired token", "red", 3)
                print(col("     • changing password / re-login RESETS the token", "dim"))
                print(col("     • copy the exact value of 'authorization'", "dim"))
                print(col("     • a user token does NOT have a 'Bot ' prefix\n", "dim"))
            else:
                flash(f"✗ [HTTP {e.code}] login failed", "red", 3)
        except Exception as e:
            print(col(f"\n  error: {e}\n", "red"))
        if ask("try again? (y/n)", "y").lower() != "y":
            show_cursor()
            sys.exit(0)


def clean_channel(api, my_id, channel_id, delay, name=""):
    deleted = 0
    before = None
    hide_cursor()
    while True:
        try:
            batch = api.get_messages(channel_id, before=before, limit=100)
        except HTTPError as e:
            print(col(f"\n    fetch failed HTTP {e.code}", "red"))
            break
        if not batch:
            break
        before = batch[-1]["id"]
        mine = [m for m in batch
                if m["author"]["id"] == my_id and m.get("type") in (0, 19, None)]
        n = len(mine)
        for i, m in enumerate(mine, 1):
            try:
                api.delete_message(channel_id, m["id"])
                deleted += 1
            except HTTPError as e:
                if e.code == 403:
                    continue
                print(col(f"\n    delete HTTP {e.code}", "red"))
            progress_bar(i, n, label=f"{name} · {deleted} deleted")
            time.sleep(delay)
        if len(batch) < 100:
            break
    progress_bar(1, 1, label=f"{name} · {deleted} deleted · done")
    sys.stdout.write("\n")
    show_cursor()
    return deleted


def do_run(api, my_id):
    w = term_w()
    print(box_top(w, "Target"))
    print(box_line(w, col("1", "cyn", "b") + col("  Channel / DM    ", "wht") + col("(Channel ID)", "dim")))
    print(box_line(w, col("2", "cyn", "b") + col("  Entire server   ", "wht") + col("(Guild ID)", "dim")))
    print(box_bot(w))
    mode = ask("choose (1/2)", "1")

    target = ask("paste the target ID")
    if not target.isdigit():
        flash("invalid ID (digits only).", "red", 3)
        return 0

    try:
        delay = max(0.0, float(ask("delay between deletions (s)", "0.8")))
    except ValueError:
        delay = 0.8

    print()
    flash("⚠  THIS PERMANENTLY DELETES YOUR MESSAGES", "red", 3)
    if ask("confirm? (type YES)") != "YES":
        flash("cancelled.", "yel", 2)
        return 0

    print()
    t0 = time.time()
    total = 0
    try:
        if mode == "2":
            with Spinner("listing server channels…"):
                chans = api.guild_channels(target)
            print(col(f"  {len(chans)} text channels found\n", "cyn"))
            for i, ch in enumerate(chans, 1):
                nm = ch.get("name", "?")
                print(col(f"  ┌ [{i}/{len(chans)}] #{nm}", "mag", "b"))
                total += clean_channel(api, my_id, ch["id"], delay, name=f"#{nm}")
        else:
            total += clean_channel(api, my_id, target, delay, name="channel")
    except HTTPError as e:
        if e.code == 401:
            flash("[401] token died mid-run. re-login.", "red", 3)
        elif e.code in (403, 404):
            flash(f"[HTTP {e.code}] no access to target.", "red", 3)
        else:
            flash(f"[HTTP {e.code}]", "red", 3)
    except KeyboardInterrupt:
        show_cursor()
        print(col("\n  interrupted by user.", "yel"))

    dt = time.time() - t0
    print()
    print(box_top(w, "Done"))
    print(box_line(w, col("✓ ", "grn") + col("total deleted: ", "wht") + col(str(total), "grn", "b")))
    print(box_line(w, col(f"time: {dt:.0f}s", "gry")))
    print(box_bot(w))
    return total


def run():
    banner()
    api, my_id = login()

    grand_total = 0
    while True:
        grand_total += do_run(api, my_id)
        print()
        if ask("run another target? (y/n)", "n").lower() != "y":
            break
        print()

    print(col(f"\n  session ended · {grand_total} messages deleted in total", "grn"))
    print(col(f"  by {_SIG}\n", "dim"))


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print(col("\n  exiting.", "yel"))
    finally:
        show_cursor()
