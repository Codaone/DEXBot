"""
A module to provide an interactive process for stakemachine configuration
Requires a working dialog tool: so UNIX-like sytems only
"""


import dialog, importlib, os, os.path, sys, collections, re

ConfigElement = collections.namedtuple('ConfigElement','key type default description extra')
# bots need to specify there own configuration values
# I want this to be UI-agnostic so a future web or GUI interface can use it too
# so each bot can have a class attribute 'configuration' which is a list of ConfigElement
# named tuples
# key: the key in the bot config dictionary that gets saved back to config.yml
# type: one of "int", "float", "bool", "string", "choice"
# default: the default value. must be right type.
# description: comments to user, full sentences encouraged 
# extra: 
#       for int / float: a (min, max) tuple
#       for string: a regular expression, entries must match it, can be None which equivalent to .*
#       for bool, ignored
#       for choice: a list of choices, choices are in turn (tag, label) tuples. labels get presented to user, and tag is used
#       as the value

NODES=[("wss://openledger.hk/ws", "OpenLedger"),
       ("wss://dexnode.net/ws", "DEXNode"),
       ("wss://node.bitshares.eu/ws", "BitShares.EU"),
       ("wss://node.testnet.bitshares.eu","BitShares.EU testnet")]

STRATEGIES={'Echo':('stakemachine.strategies.echo','Echo'),
            'Liquidity Walls':('stakemachine.strategies.walls','Walls'),
            'Storage Demo':('stakemachine.strategies.storagedemo','StorageDemo')}

SYSTEMD_SERVICE_NAME=os.path.expanduser("~/.local/share/systemd/user/stakemachine.service")

SYSTEMD_SERVICE_FILE="""
[Unit]
Description=Stakemachine

[Service]
Type=notify
WorkingDirectory={homedir}
ExecStart={exe} --systemd run 
Environment=PYTHONUNBUFFERED=true
Environment=UNLOCK={passwd}

[Install]
WantedBy=default.target
"""

class QuitException(Exception): pass

def select_choice(current,choices):
    """for the radiolist, get us a list with the current value selected"""
    return [(tag,text,current == tag) for tag,text in choices]


def process_config_element(elem,d,config):
    """
    process an item of configuration metadata display a widget as approrpriate
    d: the Dialog object
    config: the config dctionary for this bot
    """
    if elem.type == "string":
        code, txt = d.inputbox(elem.description,init=config.get(elem.key,elem.default))
        if code != d.OK: raise QuitException()
        if elem.extra:
            while not re.match(elem.extra,txt):
                d.msgbox("The value is not valid")
                code, txt = d.inputbox(elem.description,init=config.get(elem.key,elem.default))
                if code != d.OK: raise QuitException()
        config[elem.key] = txt
    if elem.type == "int":
        code, val = d.rangebox(elem.description,init=config.get(elem.key,elem.default),min=elem.extra[0],max=elem.extra[1])
        if code != d.OK: raise QuitException()
        config[elem.key] = val
    if elem.type == "bool":
        code = d.yesno(elem.description)
        config[elem.key] = (code == d.OK)
    if elem.type == "float":
        code, txt = d.inputbox(elem.description,init=config.get(elem.key,str(elem.default)))
        if code != d.OK: raise QuitException()
        while True:
            try:
                val = float(txt)
                if val < elem.extra[0]:
                    d.msgbox("The value is too low")
                elif elem.extra[1] and val > elem.extra[1]:
                    d.msgbox("the value is too high")
                else:
                    break
            except ValueError:
                d.msgbox("Not a valid value")
            code, txt = d.inputbox(elem.description,init=config.get(elem.key,str(elem.default)))
            if code != d.OK: raise QuitException()
        config[elem.key] = val
    if elem.type == "choice":
        code, tag = d.radiolist(elem.description,choices=select_choice(config.get(elem.key,elem.default),elem.extra))
        if code != d.OK: raise QuitException()
        config[elem.key] = tag
        
def setup_systemd(d,config):
    if config.get("systemd_status","install") == "reject":
        return # don't nag user if previously said no
    if not os.path.exists("/etc/systemd"):
        return # no working systemd
    if os.path.exists(SYSTEMD_SERVICE_NAME):
        # stakemachine already installed
        # so just tell cli.py to quietly restart the daemon
        config["systemd_status"] = "installed"
        return
    if d.yesno("Do you want to install stakemachine as a background (daemon) process?") == d.OK:
        for i in ["~/.local","~/.local/share","~/.local/share/systemd","~/.local/share/systemd/user"]:
            j = os.path.expanduser(i)
            if not os.path.exists(j):
                os.mkdir(j)
        code, passwd = d.passwordbox("The wallet password entered with uptick\nNOTE: this will be saved on disc so the bot can run unattended. This means anyone with access to this computer's file can spend all your money",insecure=True)
        if code != d.OK: raise QuitException()
        fd = os.open(SYSTEMD_SERVICE_NAME, os.O_WRONLY|os.O_CREAT, 0o600) # because we hold password be restrictive
        with open(fd, "w") as fp:
            fp.write(SYSTEMD_SERVICE_FILE.format(exe=sys.argv[0],passwd=passwd,homedir=os.path.expanduser("~")))
        config['systemd_status'] = 'install' # signal cli.py to set the unit up after writing config file
    else:
        config['systemd_status'] = 'reject'
    

def configure_bot(d,bot):
    process_config_element(ConfigElement("account","string","","BitShares account name for the bot to operate with",""),d,bot)
    process_config_element(ConfigElement("market","string","USD:BTS","BitShares market to operate on, in the format ASSET:OTHERASSET, for example \"USD:BTS\"","[A-Z]+:[A-Z]+"),d,bot)
    if 'module' in bot:
        inv_map = {v:k for k,v in STRATEGIES.items()}
        strategy = inv_map[(bot['module'],bot['bot'])]
    else:
        strategy = None
    code, tag = d.radiolist("Choose a bot strategy",
                            choices=select_choice(strategy,[(i,i) for i in STRATEGIES]))
    if code != d.OK: raise QuitException()
    bot['module'], bot['bot'] = STRATEGIES[tag]
    # import the bot class but don't run it
    klass = getattr(
        importlib.import_module(bot["module"]),
        bot["bot"]
    )
    # check if a class attribute configure exists
    # if so use this as very basic metadata for per-bot configuration
    if hasattr(klass,"configure"):
        for c in klass.configure:
            process_config_element(c,d,bot)
    else:
        d.msgbox("This bot does not have configuration information. You will have to check the bot code and add configuration values if required")
    return bot

                            
    
def configure_stakemachine(config):
    d = dialog.Dialog(dialog="dialog",autowidgetsize=True)
    d.set_background_title("stakemachine configuration")
    code, tag = d.radiolist("Choose a Witness node to use",
                       choices=select_choice(config.get("node"),NODES))
    if code != d.OK: raise QuitException()
    config['node'] = tag
    bots = config.get('bots',{})
    if len(bots) == 0:
        code, txt = d.inputbox("Your name for the bot")
        if code != d.OK: raise QuitException()
        config['bots'] = {txt:configure_bot(d,{})}
    else:
        code, botname = d.menu("Select bot to edit",
               choices=[(i,i) for i in bots]+[('NEW','New bot')])
        if code != d.OK: raise QuitException()
        if botname == 'NEW':
            code, txt = d.inputbox("Your name for the bot")
            if code != d.OK: raise QuitException()
            config['bots'][txt] = configure_bot(d,{})
        else:
            config['bots'][botname] = configure_bot(d,config['bots'][botname])
    setup_systemd(d,config)
    return config

if __name__=='__main__':
    print(repr(configure({})))
    
    
