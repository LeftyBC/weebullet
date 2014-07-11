# weebullet

Weechat script to push notifications to Pushbullet.

Requires an API key from http://pushbullet.com and a recentish version of Weechat with Python support enabled.

### Setup
- Place `weebullet.py` in `~/.weechat/python`
- `/script load weebullet.py` (or `/python load weebullet.py` for newer weechats)
- `/set plugins.var.python.weebullet.api_key YOUR_API_KEY`
- Enjoy!

### Additional commands
`/send_push_note`  - sends a push manually from weechat
