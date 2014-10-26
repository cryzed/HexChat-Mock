# coding: UTF-8

from __future__ import print_function

import atexit
import functools
import types


__version__ = (1, 0)

PRI_HIGHEST = 127
PRI_HIGH = 64
PRI_NORM = 0
PRI_LOW = -64
PRI_LOWEST = -128
_PRIORITIES = (PRI_HIGHEST, PRI_HIGH, PRI_NORM, PRI_LOW, PRI_LOWEST)

EAT_ALL = 3
EAT_PLUGIN = 2
EAT_HEXCHAT = 1
EAT_NONE = 0
_CALLBACK_RETURN_VALUES = (EAT_ALL, EAT_PLUGIN, EAT_HEXCHAT, EAT_NONE, None)

# Missing event_text NAME here, it is manually checked in get_info()
_INFO_TYPES = (
    'away', 'channel', 'charset', 'configdir', 'gtkwin_ptr', 'host',
    'inputbox', 'network', 'nick', 'nickserv' 'modes', 'server', 'topic',
    'win_status', 'version')

_PRINT_EVENT_NAMES = (
    'Add Notify', 'Ban List', 'Banned', 'Beep', 'Capability Acknowledgement',
    'Capability List', 'Capability Request', 'Change Nick', 'Channel Action',
    'Channel Action Hilight', 'Channel Ban', 'Channel Creation',
    'Channel DeHalfOp', 'Channel DeOp', 'Channel DeVoice', 'Channel Exempt',
    'Channel Half-Operator', 'Channel INVITE', 'Channel List',
    'Channel Message', 'Channel Mode Generic', 'Channel Modes',
    'Channel Msg Hilight', 'Channel Notice', 'Channel Operator',
    'Channel Quiet', 'Channel Remove Exempt', 'Channel Remove Invite',
    'Channel Remove Keyword', 'Channel Remove Limit', 'Channel Set Key',
    'Channel Set Limit', 'Channel UnBan', 'Channel UnQuiet', 'Channel Url',
    'Channel Voice', 'Connected', 'Connecting', 'Connection Failed',
    'CTCP Generic', 'CTCP Generic to Channel', 'CTCP Send', 'CTCP Sound',
    'CTCP Sound to Channel', 'DCC CHAT Abort', 'DCC CHAT Connect',
    'DCC CHAT Failed', 'DCC CHAT Offer', 'DCC CHAT Offering',
    'DCC CHAT Reoffer', 'DCC Conection Failed', 'DCC Generic Offer',
    'DCC Header', 'DCC Malformed', 'DCC Offer', 'DCC Offer Not Valid',
    'DCC RECV Abort', 'DCC RECV Complete', 'DCC RECV Connect',
    'DCC RECV Failed', 'DCC RECV File Open Error', 'DCC Rename',
    'DCC RESUME Request', 'DCC SEND Abort', 'DCC SEND Complete',
    'DCC SEND Connect', 'DCC SEND Failed', 'DCC SEND Offer', 'DCC Stall',
    'DCC Timeout', 'Delete Notify', 'Disconnected', 'Found IP',
    'Generic Message', 'Ignore Add', 'Ignore Changed', 'Ignore Footer',
    'Ignore Header', 'Ignore Remove', 'Ignorelist Empty', 'Invite', 'Invited',
    'Join', 'Keyword', 'Kick', 'Killed', 'Message Send', 'Motd',
    'MOTD Skipped', 'Nick Clash', 'Nick Erroneous', 'Nick Failed', 'No DCC',
    'No Running Process', 'Notice', 'Notice Send', 'Notify Away',
    'Notify Back', 'Notify Empty', 'Notify Header', 'Notify Number',
    'Notify Offline', 'Notify Online', 'Open Dialog', 'Part',
    'Part with Reason', 'Ping Reply', 'Ping Timeout', 'Private Action',
    'Private Action to Dialog', 'Private Message', 'Private Message to Dialog',
    'Process Already Running', 'Quit', 'Raw Modes', 'Receive Wallops',
    'Resolving User', 'SASL Authenticating', 'SASL Response',
    'Server Connected', 'Server Error', 'Server Lookup', 'Server Notice',
    'Server Text', 'SSL Message', 'Stop Connection', 'Topic', 'Topic Change',
    'Topic Creation', 'Unknown Host', 'User Limit', 'Users On Channel',
    'WhoIs Authenticated', 'WhoIs Away Line', 'WhoIs Channel/Oper Line',
    'WhoIs End', 'WhoIs Identified', 'WhoIs Idle Line',
    'WhoIs Idle Line with Signon', 'WhoIs Name Line', 'WhoIs Real Host',
    'WhoIs Server Line', 'WhoIs Special', 'You Join', 'You Kicked', 'You Part',
    'You Part with Reason', 'Your Action', 'Your Invitation', 'Your Message',
    'Your Nick Changing')

_hook_handlers = []
_unload_hook_handlers = []
_find_context_cache = {}


class _Channel(object):

    def __init__(self):
        self.channel = ''
        self.channelkey = ''
        self.chantypes = ''
        self.context = Context()
        self.flags = 0
        self.id = 0
        self.lag = 0
        self.maxmodes = 0
        self.network = ''
        self.nickprefixes = ''
        self.nickmodes = ''
        self.queue = 0
        self.server = ''
        self.type = 0
        self.users = 0


class _DCC(object):

    def __init__(self):
        self.address32 = 0
        self.cps = 0
        self.destfile = ''
        self.file = ''
        self.nick = ''
        self.port = 0
        self.pos = 0
        self.poshigh = 0
        self.resume = 0
        self.resumehigh = 0
        self.size = 0
        self.sizehigh = 0
        self.status = 0
        self.type = 0


class _User(object):

    def __init__(self):
        self.account = ''
        self.away = 0
        self.lasttalk = 0
        self.nick = ''
        self.host = ''
        self.prefix = ''
        self.realname = ''
        self.selected = 0


class _Ignore(object):

    def __init__(self):
        self.mask = ''
        self.flags = 0


class _Notify(object):

    def __init__(self):
        self.networks = ''
        self.nick = ''
        self.flags = 0
        self.on = 0
        self.off = 0
        self.seen = 0


class _HookHandler(object):

    def __init__(self, callback, userdata):
        self.callback = callback
        self.userdata = userdata

    def handle(self):
        self.callback(self.userdata)


class _Attributes(object):

    def __init__(self):
        self.time = 0


_LIST_TYPES = {
    'channels': _Channel, 'dcc': _DCC, 'users': _User, 'ignore': _Ignore,
    'notify': _Notify}


# Make sure to actually call unload-hook handlers at the end of the script
@atexit.register
def _unload_hooks():
    for hook_handler in _unload_hook_handlers:
        hook_handler.handle()


def _print_function_call(function):
    @functools.wraps(function)
    def wrapped_function(*args, **kwargs):
        print('%s(%s%s)' % (
            function.__name__,
            ', '.join((repr(arg) for arg in args)),
            ', '.join(('%s=%s' % (key, repr(value))
                       for key, value in kwargs.items()))))
        return function(*args, **kwargs)

    return wrapped_function


class Context(object):

    @_print_function_call
    def set(self):
        """
        Changes the current context to be the one represented by this context object.
        """
        global _context
        _context = self

    @_print_function_call
    def prnt(self, string):
        """
        Does the same as the :func:`prnt` function but in the given context.
        """
        assert isinstance(string, basestring)

    @_print_function_call
    def emit_print(self, event_name, *args):
        """
        Does the same as the :func:`emit_print` function but in the given context.
        """
        assert event_name in _PRINT_EVENT_NAMES

    @_print_function_call
    def command(self, string):
        """
        Does the same as the :func:`command` function but in the given context
        """
        assert isinstance(string, basestring)

    @_print_function_call
    def get_info(self, type):
        """
        Does the same as the :func:`get_info` function but in the given context.
        """
        if not type in _INFO_TYPES:
            parts = type.split()
            if not len(parts) == 2 or not parts[0] == 'event_text' or not len(parts[1]) > 0:
                raise ValueError('invalid type')

        return ''

    @_print_function_call
    def get_list(self, type):
        """
        Does the same as the :func:`get_list` function but in the given context.
        """
        return (_LIST_TYPES(type)(),)


_context = Context()


@_print_function_call
def prnt(string):
    """
    This function will print string in the current context. It's mainly
    useful as a parameter to pass to some other function, since the usual
    print statement will have the same results. You have a usage example
    above.

    This function is badly named because ``"print"`` is a reserved keyword
    of the Python language.
    """
    assert isinstance(string, basestring)


@_print_function_call
def emit_print(event_name, *args):
    """
    This function will generate a *print event* with the given arguments. To
    check which events are available, and the number and meaning of
    arguments, have a look at the :menuselection:`Settings --> Text Events` window.
    Here is one example:

    .. code-block:: python

        hexchat.emit_print("Channel Message", "John", "Hi there", "@")

    With plugin version 1.0+ this function takes Keywords for certain `Attributes` such as *time*
    """
    assert event_name in _PRINT_EVENT_NAMES


@_print_function_call
def command(string):
    """
    Execute the given command in the current `context`. This has the same
    results as executing a command in the HexChat window, but notice that
    the ``/`` prefix is not used. Here is an example:

    .. code-block:: python

       hexchat.command("server irc.openprojects.net")
    """
    assert isinstance(string, basestring)


@_print_function_call
def nickcmp(s1, s2):
    """
    This function will do an RFC1459 compliant string comparison
    and is useful to compare channels and nicknames.

    :returns: Returns 0 if they match and less than or greater than 0 if s1 is less than or greather than s2

    .. code-block:: python

       if hexchat.nickcmp(nick, "mynick") == 0:
           print("They are the same!")
    """
    assert isinstance(s1, basestring)
    assert isinstance(s2, basestring)
    return 0 if s1.lower() == s2.lower() else 1


@_print_function_call
def strip(text, length=-1, flags=3):
    """
    This function can strip colors and attributes from text.

    :param length: -1 for entire string
    :param flags:
        1: Strip Colors
        2: Strip Attributes
        3: Strip All
    :returns: Stripped String

    .. code-block:: python

        text = '\00304\002test' # Bold red text
        print(text)
        print(hexchat.strip(text, len(text), 1)) # Bold uncolored text
    """
    assert isinstance(text, basestring)
    assert isinstance(length, int)
    assert isinstance(flags, int)
    return text


@_print_function_call
def get_info(type):
    """
    Retrieve the information specified by the ``type`` string in the current
    context. At the moment of this writing, the following information types
    are available to be queried:

    -  **away:** Away reason or None if you are not away.
    -  **channel:** Channel name of the current context.
    -  **charset:** Charset in current context.
    -  **configdir:** HexChat config directory e.g.: "~/.config/hexchat".
    -  **event\_text NAME:** Returns text event string for requested event.
    -  **gtkwin\_ptr:** Returns hex representation of the pointer to the current Gtk window.
    -  **host:** Real hostname of the server you connected to.
    -  **inputbox:** Contents of inputbox.
    -  **network:** Current network name or None.
    -  **nick:** Your current nick name.
    -  **nickserv:** Current networks nickserv password or None.
    -  **modes:** Current channel modes or None.
    -  **server:** Current server name (what the server claims to be) or
       None if you are not connected.
    -  **topic:** Current channel topic.
    -  **win\_status:** Returns status of window: 'active', 'hidden', or
       'normal'.
    -  **version:** HexChat version number.

    Example:

    .. code-block:: python

       if hexchat.get_info("server") == 'freenode':
           hexchat.prnt('connected!')

    You can also get the format of Text Events by using *event_text* and the event:

    .. code-block:: python

       print(hexchat.get_info("event_text Channel Message"))
    """
    assert type in _INFO_TYPES
    return ''


@_print_function_call
def get_prefs(name):
    """
    Retrieve the HexChat setting information specified by the ``name``
    string, as available by the ``/set`` command.

    .. code-block:: python

       print("Current preferred nick: " + hexchat.get_prefs("irc_nick1"))

    And on top of that there are a few special preferences:

    - id (unique server id)
    - state_cursor (location of cursor in input box)
    """
    return ''


@_print_function_call
def get_list(type):
    """
    With this function you may retrieve a list containing the selected
    information from the current context, like a DCC list, a channel list, a
    user list, etc. Each list item will have its attributes set dynamically
    depending on the information provided by the list type.

    The example below is a rewrite of the example provided with HexChat's
    plugin API documentation. It prints a list of every DCC transfer
    happening at the moment. Notice how similar the interface is to the C
    API provided by HexChat.

    .. code-block:: python

       list = hexchat.get_list("dcc")
       if list:
           print("--- DCC LIST ------------------")
           print("File  To/From   KB/s   Position")
           for i in list:
               print("%6s %10s %.2f  %d" % (i.file, i.nick, i.cps/1024, i.pos))

    Below you will find what each list type has to offer.
    """
    return (_LIST_TYPES[type](),)


@_print_function_call
def hook_command(name, callback, userdata=None, priority=PRI_NORM, help=None):
    """
    This function allows you to hook into the name HexChat command. It means
    that everytime you type ``/name ...``, ``callback`` will be called.
    Parameters ``userdata`` and ``priority`` have their meanings explained
    above, and the parameter help, if given, allows you to pass a help text
    which will be shown when ``/help name`` is executed.

    You may also hook an empty string to capture every message a user sends,
    either when they hit enter or use ``/say``.

    :returns: New Hook Handler

    .. code-block:: python

       def onotice_cb(word, word_eol, userdata):
           if len(word) < 2:
               print("Second arg must be the message!")
           else:
               hexchat.command("NOTICE @{} {}".format(hexchat.get_info("channel"), word_eol[1]))
           return hexchat.EAT_ALL

       hexchat.hook_command("ONOTICE", onotice_cb, help="/ONOTICE <message> Sends a notice to all ops")

    You may return one of ``EAT_*`` constants in the callback, to control
    HexChat's behavior, as explained above.
    """
    assert isinstance(name, basestring)
    assert priority in _PRIORITIES
    assert callback(('',), ('',), userdata) in _CALLBACK_RETURN_VALUES
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_print(name, callback, userdata=None, priority=PRI_NORM):
    """
    This function allows you to register a callback to trap any print
    events. The event names are available in the :menuselection:`Settings --> Text Events` window.
    Parameters ``userdata`` and ``priority`` have their meanings explained
    above.

    :param name: event name (see :menuselection:`Settings --> Text Events`)
    :returns: New Hook Handler

    .. code-block:: python

       def youpart_cb(word, word_eol, userdata):
           print("You have left channel " + word[2])
           return hexchat.EAT_HEXCHAT # Don't let HexChat do its normal printing

       hexchat.hook_print("You Part", youpart_cb)

    Along with Text Events there are a handfull of *special* events you can hook with this:

    - **Open Context**: Called when a new context is created.
    - **Close Context**: Called when a context is closed.
    - **Focus Tab**: Called when a tab is brought to front.
    - **Focus Window**: Called a toplevel window is focused, or the main tab-window is focused by the window manager.
    - **DCC Chat Text**: Called when some text from a DCC Chat arrives. It provides these elements in the word list:

      - Address
      - Port
      - Nick
      - Message

    - **Key Press**: Called when some keys are pressed in the input box. It provides these elements in the word list:

      - Key Value
      - State Bitfield (shift, capslock, alt)
      - String version of the key
      - Length of the string (may be 0 for unprintable keys)
    """
    assert name in _PRINT_EVENT_NAMES
    assert priority in _PRIORITIES
    assert callback(('',), ('',), userdata) in _CALLBACK_RETURN_VALUES
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_print_attrs(name, callback, userdata=None, priority=PRI_NORM):
    """
    This function is the same as :func:`hook_print` except its callback will have a new
    `Attribute` argument.

    :returns: New Hook Handler

    .. versionadded:: 1.0

    .. code-block:: python

        def youpart_cb(word, word_eol, userdata, attributes):
            if attributes.time: # Time may be 0 if server-time is not enabled.
                print("You have left channel {} at {}".format(word[2], attributes.time))
                return hexchat.EAT_HEXCHAT

        hexchat.hook_print_attrs("You Part", youpart_cb)
    """
    assert name in _PRINT_EVENT_NAMES
    assert priority in _PRIORITIES
    assert callback(('',), ('',), userdata, _Attributes()) in _CALLBACK_RETURN_VALUES
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_server(name, callback, userdata=None, priority=PRI_NORM):
    """
    This function allows you to register a callback to be called when a
    certain server event occurs. You can use this to trap ``PRIVMSG``,
    ``NOTICE``, ``PART``, a server numeric, etc. Parameters ``userdata`` and
    ``priority`` have their meanings explained above.

    :returns: New Hook Handler

    .. code-block:: python

        def kick_cb(word, word_eol, userdata):
            print('{} was kicked from {} ({})'.format(word[3], word[2], word_eol[4]))
            # Don't eat this event, let other plugins and HexChat see it too
            return hexchat.EAT_NONE

       hexchat.hook_server("KICK", kick_cb)
    """
    assert isinstance(name, basestring)
    assert priority in _PRIORITIES
    assert callback(('',), ('',), userdata) in _CALLBACK_RETURN_VALUES
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_server_attrs(name, callback, userdata=None, priority=PRI_NORM):
    """
    This function is the same as :func:`hook_server` Except its callback will have a new
    `Attribute` argument.

    :returns: New Hook Handler

    .. versionadded:: 1.0

    .. code-block:: python

        def kick_cb(word, word_eol, userdata, attributes):
            if attributes.time: # Time may be 0 if server-time is not enabled.
                print('He was kicked at {}'.format(attributes.time))
                return hexchat.EAT_NONE

       hexchat.hook_server_attrs("KICK", kick_cb)
    """
    assert isinstance(name, basestring)
    assert priority in _PRIORITIES
    assert callback(('',), ('',), userdata, _Attributes()) in _CALLBACK_RETURN_VALUES
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_timer(timeout, callback, userdata=None):
    """
    This function allows you to register a callback to be called every
    timeout milliseconds. Parameters userdata and priority have their
    meanings explained above.

    :returns: New Hook Handler

    .. code-block:: python

       myhook = None

       def stop_cb(word, word_eol, userdata):
           global myhook
           if myhook is not None:
               hexchat.unhook(myhook)
               myhook = None
               print("Timeout removed!")

       def timeout_cb(userdata):
           print("Annoying message every 5 seconds! Type /STOP to stop it.")
           return 1 # Keep the timeout going

       myhook = hexchat.hook_timer(5000, timeout_cb)
       hexchat.hook_command("STOP", stop_cb)

    If you return a true value from the callback, the timer will be keeped,
    otherwise it is removed.
    """
    assert isinstance(timeout, int)
    callback(userdata)
    hook_handler = _HookHandler(callback, userdata)
    _hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def hook_unload(callback, userdata=None):
    """
    This function allows you to register a callback to be called when the
    plugin is going to be unloaded. Parameters ``userdata`` and ``priority``
    have their meanings explained above.

    :returns: New Hook Handler

    .. code-block:: python

       def unload_cb(userdata):
           print("We're being unloaded!")

       hexchat.hook_unload(unload_cb)
    """
    hook_handler = _HookHandler(callback, userdata)
    _unload_hook_handlers.append(hook_handler)
    return hook_handler


@_print_function_call
def unhook(handler):
    """
    Unhooks any hook registered with the hook functions above.

    :param handler: Handler returned from :func:`hook_print`, :func:`hook_command`, :func:`hook_server` or :func:`hook_timer`

    As of version 1.0 of the plugin hooks from :func:`hook_print` and :func:`hook_command` can be unhooked by their names.
    """

    # Simply fail if the hook handler is not contained in the "regular" hook
    # handlers and try removing it from the unload-hook handlers. Let the
    # exception bubble up if it doesn't exist there either
    try:
        _hook_handlers.remove(handler)
    except ValueError:
        _unload_hook_handlers.remove(handler)


@_print_function_call
def set_pluginpref(name, value):
    """
    Stores settings in addon\_python.conf in the config dir.

    :returns:
        - False: Failure
        - True: Success

    .. versionadded:: 0.9

    .. Note:: Until the plugin uses different a config file per script it's
              recommened to use 'scriptname_settingname' to avoid conflicts.
    """
    assert isinstance(name, basestring)
    return True


@_print_function_call
def get_pluginpref(name):
    """
    This will return the value of the variable of that name. If there is
    none by this name it will return ``None``.

    :returns: String or Integer of stored setting or None if it does not exist.

    .. Note:: Strings of numbers are always returned as Integers.

    .. versionadded:: 0.9
    """
    assert isinstance(name, basestring)
    return ''


@_print_function_call
def del_pluginpref(name):
    """
    Deletes the specified variable.

    :returns:
        - False: Failure
        - True: Success (or never existing),

    .. versionadded:: 0.9
    """
    assert isinstance(name, basestring)
    return True


@_print_function_call
def list_pluginpref():
    """
    Returns a list of all currently set preferences.

    :rtype: List of Strings

    .. versionadded:: 0.9
    """

    # Make sure to at least return a list of one string, so a loop can at least
    # run once
    return ('',)


@_print_function_call
def get_context():
    """
    :rtype: `context`
    """
    return _context


@_print_function_call
def find_context(server=None, channel=None):
    """
    Finds a context based on a channel and servername.

    :keyword server: if None only looks for channel name
    :keyword channel: if None looks for front context of given server
    :rtype: `context`

    .. code-block:: python

       cnc = hexchat.find_context(channel='#conectiva')
       cnc.command('whois niemeyer')
    """
    key = server, channel
    if key in _find_context_cache:
        return _find_context_cache[key]

    assert isinstance(server, (types.NoneType, basestring))
    assert isinstance(channel, (types.NoneType, basestring))

    context = Context()
    _find_context_cache[key] = context
    return context
