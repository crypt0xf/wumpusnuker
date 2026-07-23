# wumpusnuker

TUI to delete **your own messages** from a Discord channel, DM, or entire server.
Pure Python, no dependencies.

## ⚠ Warning

Using a user token to automate an account ("self-bot") **violates Discord's ToS**
and can get it **permanently banned**. Use a throwaway account. **Never share your
token.**

## Requirements

Python 3.8+, a terminal with UTF-8/ANSI support (e.g. Windows Terminal).

## Usage

```bash
python wumpusnuker.py
```

1. Paste your token (hidden input).
2. Pick a target: channel/DM or whole server (by ID).
3. Set the delay between deletions.
4. Confirm by typing `YES`.

**Get an ID:** enable Developer Mode (Settings → Advanced), then right-click the
channel/server → Copy ID.

**Get your token:** in Discord web, F12 → Network → any request to
`discord.com/api` → Headers → `authorization`.

## Notes

- Only deletes your own messages, unless the token has *Manage Messages*.
- No bulk-delete for messages older than 14 days — goes one by one, so large
  servers take time.
- Default delay `0.8s` avoids rate limits (429).
