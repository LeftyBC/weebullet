# weebullet

Weechat script to push notifications to Pushbullet.

Requires an API key from http://pushbullet.com and a recentish version of Weechat with Python support enabled.

### Setup

- Place `weebullet.py` in `~/.weechat/python`
- `/script load weebullet.py` (or `/python load weebullet.py` for newer weechats)
- `/set plugins.var.python.weebullet.api_key YOUR_API_KEY`
- Enjoy!

### Commands

| Command                     | Description |
|---|---|
| `/weebullet ignore`         | adds to the list of ignored channels |
| `/weebullet unignore`       | removes from the list of ignored channels |
| `/weebullet subscribe`      | adds to the list of subscribed channels |
| `/weebullet unsubscribe`    | removes from the list of subscribed channels |
| `/weebullet listignored`    | list ignored channels |
| `/weebullet listsubscribed` | list subscribed channels |
| `/weebullet listdevices`    | list devices associated with your pushbullet API key |
| `/weebullet test`           | send a test notification to the devices in notify_devices |
| `/weebullet help`           | prints this help message |

### Settings

| Setting             | Description |
|---|---|
| `api_key`             | your pushbullet API key **(required)** |
| `away_only`           | send only when marked as away<br>values: `0` or `1`; default: `1` |
| `inactive_only`       | send only when the message is in an inactive buffer<br>values: `0` or `1`; default: `0` |
| `ignore_on_relay`     | ignore notifications when a relay is connected<br>values: `0` or `1`; default: `0` |
| `notify_devices`      | list of device identifiers to notify<br>value: comma separated device identifiers, default: `all` |
| `min_notify_interval` | minimum number of seconds to wait before another notification<br>value: integer number of seconds, default: `60` |
| `api_timeout`         | number of seconds to api request timeout<br>value: integer number of seconds, default: `20` |
