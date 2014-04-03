#!/usr/bin/env python

import requests
import json
import re

import weechat as w

w.register('weebullet', 'Lefty', '0.0.1', 'BSD', 'weebullet pushes notifications from IRC to Pushbullet.', '', '')

w.hook_print("", "irc_privmsg", "", 1, "priv_msg_cb", "")

credentials = {
    "api_key": ""
}

for option, default_value in credentials.items():
    if w.config_get_plugin(option) == "":
        w.prnt("", w.prefix("error") + "pushbullet: Please set option: %s" % option)
        w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s STRING" % option)

def send_push(title, body):

    apiurl = 'https://api.pushbullet.com/api/pushes'
    apikey = w.config_get_plugin("api_key")

    payload = {'type': 'note', 'title': title, 'body': body}

    r = requests.post(apiurl, data=payload, auth=(apikey, ''))

    if r.status_code is not 200:
	return False
    return True


def priv_msg_cb(data, bufferp, uber_empty, tagsn, isdisplayed,
        ishilight, prefix, message):
    """Sends highlighted message to be printed on notification"""

    am_away = w.buffer_get_string(bufferp, 'localvar_away')

    if not am_away:
	w.prnt("", "[weebullet] Not away, skipping notification")
	return w.WEECHAT_RC_OK

    notif_body = u"<%s> %s" % (
        prefix.decode('utf-8'),
	message.decode('utf-8')
    )

    # Check that it's in a "/q" buffer and that I'm not the one writing the msg
    is_pm = w.buffer_get_string(bufferp, "localvar_type") == "private"
    is_notify_private = re.search(r'(^|,)notify_private(,|$)', tagsn) is not None
    # PM (query)
    if (is_pm and is_notify_private):
	send_push(
		title="Privmsg from %s" % prefix.decode('utf-8'),
		body=notif_body
	)

    # Highlight (your nick is quoted)
    elif (ishilight == "1"):
        bufname = (w.buffer_get_string(bufferp, "short_name") or
                w.buffer_get_string(bufferp, "name"))
	send_push(
		title="Highlight in %s" % bufname.decode('utf-8'),
		body=notif_body
	)

    return w.WEECHAT_RC_OK
