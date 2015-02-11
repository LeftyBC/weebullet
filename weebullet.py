#!/usr/bin/env python

import json
import re
import urllib

import weechat as w

w.register('weebullet', 'Lefty', '0.3.0', 'BSD', 'weebullet pushes notifications from IRC to Pushbullet.', '', '')

w.hook_print("", "irc_privmsg", "", 1, "priv_msg_cb", "")
w.hook_command(
    "send_push_note", #command
    "send a push note", # description
    "[message]" # arguments description, 
    "", #argument
    "",
    "",
    "cmd_send_push_note", "")
w.hook_command(
    "weebullet", 
    "pushes notifications from IRC to Pushbullet",
    "[command]",
    "Available commands are:\n||listdevices : prints a list of all devices associated with your Pushbullet API key\n||help : prints config options and defaults",
    "",
    "cmd_help", "")

configs = {
    "api_key": "",
	"away_only": "1",
    "device_iden": "all"
}

for option, default_value in configs.items():
    if w.config_get_plugin(option) == "":
        if configs[option] == "":
            w.prnt("", w.prefix("error") + "pushbullet: Please set option: %s" % option)
            if type(default_value) == "str":
                w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s STRING" % option)
            elif type(default_value) == "int":
                w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s INT" % option)
            else:
                w.prnt("", "pushbullet: /set plugins.var.python.weebullet.%s VALUE" % option)
        else:
            w.config_set_plugin(option, configs[option])

def process_devicelist_cb(data, url, status, response, err):
    try:
        devices = json.loads(response)["devices"]
        w.prnt("", "Device List:")
        for device in devices:
            if device["pushable"]:
                if "nickname" in device:
                    w.prnt("", "---\n%s" % device["nickname"])
                else:
                    w.prnt("", "---\nUnnamed")
                w.prnt("", "%s" % device["iden"])
    except KeyError:
        w.prnt("", "[weebullet] Error accessing device list: %s" % response)
        return w.WEECHAT_RC_ERROR
    return w.WEECHAT_RC_OK

def cmd_help(data, buffer, args):
    if(args == "listdevices"):
        apikey = w.config_get_plugin("api_key")
        apiurl = "https://%s@api.pushbullet.com/v2/devices" % (apikey)
        w.hook_process("url:"+apiurl, 20000, "process_devicelist_cb", "")
    else:
        w.prnt("", """
Weebullet requires an API key from your Pushbullet account to work. Set your API key with:
    /set plugins.var.python.weebullet.api_key <KEY>

Weebullet will by default only send notifications when you are marked away on IRC. You can change this with:
    /set plugins.var.python.weebullet.away_only [0|1]

Weebullet will by default send to all devices associated with your Pushbullet account. You can change this with:
    /set plugins.var.python.weebullet.device_iden <ID>

You can get a list of your devices from the Pushbullet website, or by using
    /weebullet listdevices
""")
    return w.WEECHAT_RC_OK

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
    apiurl = "https://%s@api.pushbullet.com/v2/pushes" % (apikey)
    timeout = 20000 # FIXME - actually use config
    if len(title) is not 0 or len(body) is not 0:
        deviceiden = w.config_get_plugin("device_iden")
        if deviceiden == "all":
		    payload = urllib.urlencode({'type': 'note', 'title': title, 'body': body.encode('utf-8')})
        else:
		    payload = urllib.urlencode({'type': 'note', 'title': title, 'body': body.encode('utf-8'), 'device_iden':deviceiden})
        w.hook_process_hashtable("url:" + apiurl, { "postfields": payload, "header":"1" }, timeout, "process_pushbullet_cb", "")

def cmd_send_push_note(data, buffer, args):
    send_push(
            title="Manual Notification from weechat",
            body=args.decode('utf-8')
            )
    return w.WEECHAT_RC_OK

def priv_msg_cb(data, bufferp, uber_empty, tagsn, isdisplayed,
        ishilight, prefix, message):
    """Sends highlighted message to be printed on notification"""

    if w.config_get_plugin("away_only") == "1":
        am_away = w.buffer_get_string(bufferp, 'localvar_away')
    else:
        am_away = True

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
    elif (str(ishilight) == "1"):
        bufname = (w.buffer_get_string(bufferp, "short_name") or
                w.buffer_get_string(bufferp, "name"))
	send_push(
		title="Highlight in %s" % bufname.decode('utf-8'),
		body=notif_body
	)

    return w.WEECHAT_RC_OK
