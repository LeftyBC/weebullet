#!/usr/bin/env python

import json
import re
import urllib

import weechat as w

w.register('weebullet', 'Lefty', '0.2.0', 'BSD', 'weebullet pushes notifications from IRC to Pushbullet.', '', '')

w.hook_print("", "irc_privmsg", "", 1, "priv_msg_cb", "")
w.hook_command(
    "send_push_note", #command
    "send a push note", # description
    "[message]" # arguments description, 
    "", #argument
    "",
    "",
    "cmd_send_push_note", "")

configs = {
#    "timeout": 20000,
    "api_key": ""
}

for option, default_value in configs.items():
    if w.config_get_plugin(option) == "":
        w.prnt("", w.prefix("error") + "pushbullet: Please set option: %s" % option)
        if type(default_value) == "str":
            w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s STRING" % option)
        elif type(default_value) == "int":
            w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s INT" % option)
        else:
            w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s VALUE" % option)


def process_pushbullet_cb(data, url, status, response, err):
    body = None
    headers = {}
    lines = response.rstrip().splitlines()
    status_code = int(lines.pop(0).split()[1])
    for line in lines:
        if body == "":
            body += line
            continue
        header_line = line.split(":", 2)
        if len(header_line) != 2:
            body = ""
            continue
        headers[header_line[0].strip()] = header_line[1].strip()


    # response is the string of http body
    if status == w.WEECHAT_HOOK_PROCESS_ERROR:
        w.prnt("", "[weebullet] Error sending to pushbullet: %s - %s" % (status, url))
        return w.WEECHAT_RC_ERROR

    if status_code is 401 or status_code is 403:
        w.prnt("", "[weebullet] Invalid API Token: %s" % (w.config_get_plugin("api_key")))
        return w.WEECHAT_RC_ERROR
    if status_code is not 200:
        w.prnt("", "[weebullet] Error sending to pushbullet: %s - %s - %s" % (url, status_code, body))
        return w.WEECHAT_RC_ERROR

    return w.WEECHAT_RC_OK

def send_push(title, body):
    apikey = w.config_get_plugin("api_key")
    apiurl = "https://%s:@api.pushbullet.com/api/pushes" % (apikey)
    timeout = 20000 # FIXME - actually use config
    payload = urllib.urlencode({'type': 'note', 'title': title, 'body': body})
    w.hook_process_hashtable("url:" + apiurl, { "postfields": payload, "header":"1" }, timeout, "process_pushbullet_cb", "")

def cmd_send_push_note(data, buffer, args):
    send_push(
            title="Manual Notification from weechat",
            body=args
            )
    return w.WEECHAT_RC_OK

def priv_msg_cb(data, bufferp, uber_empty, tagsn, isdisplayed,
        ishilight, prefix, message):
    """Sends highlighted message to be printed on notification"""

    am_away = w.buffer_get_string(bufferp, 'localvar_away')

    if not am_away:
	# TODO: make debug a configurable
	#w.prnt("", "[weebullet] Not away, skipping notification")
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
