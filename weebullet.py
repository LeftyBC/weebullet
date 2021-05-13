#!/usr/bin/env python3

import json
import re
import urllib.request, urllib.parse, urllib.error
import time

import weechat as w


description = "weebullet pushes notifications from weechat to pushbullet"

help_text = """
commands:
    /weebullet ignore           adds to the list of ignored channels
    /weebullet unignore         removes from the list of ignored channels
    /weebullet subscribe        adds to the list of subscribed channels
    /weebullet unsubscribe      removes from the list of subscribed channels
    /weebullet listignored      list ignored channels
    /weebullet listsubscribed   list subscribed channels
    /weebullet listdevices      list devices associated with your pushbullet API key
    /weebullet test             send a test notification to the devices in notify_devices
    /weebullet help             prints this help message

examples:
    /weebullet ignore #foo,#bar,#baz
    /weebullet subscribe #foo,#bar
    /weebullet listignored
    /weebullet listdevices

settings: (prefix with plugins.var.python.weebullet.<setting>)
    api_key               your pushbullet API key (required)
    away_only             send only when marked as away
                          value: [0|1], default: 1
    inactive_only         send only when the message is in an inactive buffer
                          value: [0|1], default: 0
    ignore_on_relay       ignore notifications when a relay is connected
                          value: [0|1], default: 0
    notify_devices        list of device identifiers to notify
                          value: comma separated device identifiers, default: all
    min_notify_interval   minimum number of seconds to wait before another notification
                          value: integer number of seconds, default: 60
    api_timeout           number of seconds to api request timeout
                          value: integer number of seconds, default: 20
"""


configs = {                      # some sane defaults
    'api_key': '_required',      
    'ignored_channels': '',      # no ignored channels
    'subscribed_channels': '',   # no subscribed channels
    'away_only': '1',            # send only when away
    'inactive_only': '0',        # send even if buffer is active
    'ignore_on_relay': '0',      # send even if relay is connected
    'notify_devices': 'all',     # send to all devices
    'min_notify_interval': '60', # send notifications at least a minute apart
    'api_timeout': '20',         # 20 seconds ought to be enough
    'debug': '0',                # enable debugging
}


last_notification = 0


def debug(msg):
    if str(w.config_get_plugin('debug')) != '0':
        w.prnt('', '[weebullet] debug: {}'.format(str(msg)))


def register():
    w.register('weebullet', 'Lefty', '0.6', 'BSD', description, '', '')


def load_settings():
    for (option, default_value) in list(configs.items()):
        if w.config_get_plugin(option) == '':
            if configs[option] == '_required':
                w.prnt('', 'missing plugins.var.python.weebullet.{}'.format(option))
            else:
                w.config_set_plugin(option, configs[option])


def setup_hooks():
    global description
    global help_text

    w.hook_print('', '', '', 1, 'message_hook', '')
    w.hook_command('weebullet', description, '[command]', help_text, '', 'process_command', '')


def process_devicelist_cb(
    data,
    url,
    status,
    response,
    err,
):
    try:
        devices = json.loads(response)['devices']
        w.prnt('', 'devices:')
        for device in devices:
            if device['pushable']:
                if 'nickname' in device:
                    device_name = device['nickname']
                else:
                    device_name = '<unnamed>'
                w.prnt('', '    {}: {}'.format(device_name, device['iden']))
    except KeyError:
        w.prnt('', '[weebullet] error accessing devices: {}'.format(response))
        return w.WEECHAT_RC_ERROR

    return w.WEECHAT_RC_OK


def get_api_key():
    return w.string_eval_expression(w.config_get_plugin('api_key'), {}, {}, {})


def get_devices():
    api_key = get_api_key()
    apiurl = 'https://{}@api.pushbullet.com/v2/devices'.format(api_key)
    w.hook_process(
        'url:' + apiurl,
        int(w.config_get_plugin('api_timeout'))*1000,
        'process_devicelist_cb',
        '',
    )

    return ""


def get_channels(kind):
    channels = w.config_get_plugin('{}_channels'.format(kind))
    if channels == '':
        return set([])
    else:
        return set([channel.strip() for channel in channels.split(' ')])


def process_command(data, buffer, args):
    # process the following commands:
    #   /weebullet ignore CHANNELS
    #   /weebullet subscribe CHANNELS
    for kind in ['ignore', 'subscribe']:
        channels = get_channels(kind + "d")

        action_commands = {
            kind: lambda channel: channels.add(channel),
            'un{}'.format(kind): lambda channel: channels.remove(channel),
        }

        for command in action_commands:
            command_regex = re.match('^' + command + '\s+(.+)', args)
            if command_regex is not None:
                new_channels = command_regex.group(1).split(' ')
                for new_channel in new_channels:
                    try:
                        action_commands[command](new_channel)
                    except Exception as e:
                        pass

                w.config_set_plugin('{}_channels'.format(kind + "d"), ' '.join(channels))

                return w.WEECHAT_RC_OK

    # process the following commands:
    #   /weebullet listignored
    #   /weebullet listsubscribed
    #   /weebullet listdevices
    list_commands = {
        'listignored': lambda: 'Ignored: {}'.format(w.config_get_plugin('ignored_channels')),
        'listsubscribed': lambda: 'Subscribed: {}'.format(w.config_get_plugin('subscribed_channels')),
        'listdevices': lambda: get_devices(),
    }

    for command in list_commands:
        if args == command:
            result = list_commands[command]()
            if result:
                w.prnt( '', result)

            return w.WEECHAT_RC_OK

    # process the following commands:
    #   /weebullet test
    if args == 'test':
        send_push(
            title='Test push notification',
            body='Test push notification from weebullet',
        )

        return w.WEECHAT_RC_OK

    # process the following:
    #   /weebullet help
    #   /weebullet <any uncaught command>
    w.prnt('', help_text)

    return w.WEECHAT_RC_OK


def process_pushbullet_cb(
    data,
    url,
    status,
    response,
    err,
):
    body = None
    headers = {}
    lines = response.rstrip().splitlines()
    status_code = int(lines.pop(0).split()[1])
    for line in lines:
        if body == '':
            body += line
            continue
        header_line = line.split(':', 2)
        if len(header_line) != 2:
            body = ''
            continue
        headers[header_line[0].strip()] = header_line[1].strip()

    # response is the string of http body
    if status == w.WEECHAT_HOOK_PROCESS_ERROR:
        w.prnt(
            '',
            '[weebullet] error sending to pushbullet: {} - {}'.format(
                status,
                url,
            ),
        )
        return w.WEECHAT_RC_ERROR

    if status_code == 401 or status_code == 403:
        w.prnt(
            '',
            '[weebullet] invalid API key: {}'.format(get_api_key()),
        )
        return w.WEECHAT_RC_ERROR

    if status_code != 200:
        w.prnt(
            '',
            '[weebullet] Error sending to pushbullet: {} - {} - {}'.format(
                url,
                status_code,
                body,
            ),
        )
        return w.WEECHAT_RC_ERROR

    return w.WEECHAT_RC_OK


def away_only_check(bufferp):
    if w.config_get_plugin('away_only') != '1':
        return False

    return not w.buffer_get_string(bufferp, 'localvar_away')


def inactive_only_check(bufferp):
    if w.config_get_plugin('inactive_only') != '1':
        return False

    return w.current_buffer() == bufferp


def interval_limit_check():
    interval = w.config_get_plugin('min_notify_interval')

    if interval is None or interval == '':
        return False

    try:
        interval = int(interval)
    except ValueError:
        w.prnt('', '[weebullet] min_notify_interval not an integer')
        return False

    global last_notification

    earliest_allowed = last_notification + interval

    return time.time() < earliest_allowed


def relay_check():
    check_relays = w.config_string_to_boolean(w.config_get_plugin('ignore_on_relay'))

    if not check_relays:
        return False

    infolist = w.infolist_get('relay', '', '')
    if infolist:
        while w.infolist_next(infolist):
            status = w.infolist_string(infolist, 'status_string')
            if status == 'connected':
                return True
        w.infolist_free(infolist)

    return False


def get_buf_name(bufferp):
    short_name = w.buffer_get_string(bufferp, 'short_name')
    name = w.buffer_get_string(bufferp, 'name')
    return (short_name or name)


def is_ignored(bufferp):
    buf_name = get_buf_name(bufferp)
    return buf_name in get_channels('ignored')


def is_subscribed(bufferp):
    buf_name = get_buf_name(bufferp)
    return buf_name in get_channels('subscribed')


def message_hook(
    data,
    bufferp,
    uber_empty,
    tagsn,
    is_displayed,
    is_highlighted,
    prefix,
    message,
):
    is_pm = w.buffer_get_string(bufferp, 'localvar_type') == 'private'
    regular_channel = not is_subscribed(bufferp) and not is_pm

    skip = False
    skip = skip or away_only_check(bufferp)
    skip = skip or inactive_only_check(bufferp)
    skip = skip or interval_limit_check()
    skip = skip or relay_check()
    skip = skip or (is_ignored(bufferp) and regular_channel)
    skip = skip or (not is_displayed)
    skip = skip or (not is_highlighted and regular_channel)
    
    if skip:
        return w.WEECHAT_RC_OK

    if is_pm:
        title = 'PM from {}'.format(prefix)
    else:
        title = 'Message on {} from {}'.format(get_buf_name(bufferp), prefix)

    send_push(title=title, body=message)

    return w.WEECHAT_RC_OK


def send_push(title, body):
    global last_notification
    api_key = get_api_key()
    apiurl = 'https://{}@api.pushbullet.com/v2/pushes'.format(api_key)
    timeout = int(w.config_get_plugin('api_timeout')) * 1000
    if len(title) != 0 or len(body) != 0:
        deviceiden = w.config_get_plugin('devices')
        last_notification = time.time()
        if deviceiden == 'all':
            payload = urllib.parse.urlencode({
                'type': 'note',
                'title': title,
                'body': body.encode('utf-8')
            })
        else:
            payload = urllib.parse.urlencode({
                'type': 'note',
                'title': title,
                'body': body.encode('utf-8'),
                'devices': deviceiden,
            })

        w.hook_process_hashtable(
            'url:' + apiurl,
            {
                'postfields': payload,
                'header': '1',
            },
            timeout,
            'process_pushbullet_cb',
            '',
        )


def main():
    register()
    load_settings()
    setup_hooks()


main()
