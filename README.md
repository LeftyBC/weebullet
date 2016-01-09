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

`/weebullet` - without arguments, prints a help message

`/weebullet listdevices` - retrieves a list of your pushable devices and their nicknames

`/weebullet listignores` - retrieves a list of ignored channels

`/weebullet ignore` - ignores a given channel or channels

`/weebullet unignore` - unignores a given channel or channels

### Optional settings
`/set plugins.var.python.weebullet.away_only [0|1]` set to `0` if you wish to always receive notifications, or only when you are marked away (default `1`)

`/set plugins.var.python.weebullet.device_iden [DEVICE_ID|all]` if you wish to be notified only on a specific device, or on all devices (default `all`)

`/set plugins.var.python.weebullet.ignored_channels [#channel1[, #channel2[, #channel3[, ...]]]]` if you wish to set ignored channels manually (default blank)

`/set plugins.var.python.weebullet.min_notify_interval [0|NUMBER]` to set a minimum interval in seconds between notifications (default 0, disabled)

`/set plugins.var.python.weebullet.ignore_on_relay [0|1]` set to 1 if you want to suppress push notifications when a client is connected to your weechat via weechat-relay (default `0`)
