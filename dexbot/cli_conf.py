"""
A module to provide an interactive text-based tool for dexbot configuration
The result is takemachine can be run without having to hand-edit config files.
If systemd is detected it will offer to install a user service unit (under ~/.local/share/systemd
This requires a per-user systemd process to be runnng

Requires the 'dialog' tool: so UNIX-like sytems only

Note there is some common cross-UI configuration stuff: look in basestrategy.py
It's expected GUI/web interfaces will be re-implementing code in this file, but they should
understand the common code so bot strategy writers can define their configuration once
for each strategy class.

"""


import dialog, importlib, os, os.path, sys, collections, re

from dexbot.bot import STRATEGIES


NODES=[("wss://openledger.hk/ws", "OpenLedger"),
       ("wss://dexnode.net/ws", "DEXNode"),
       ("wss://node.bitshares.eu/ws", "BitShares.EU")]


SYSTEMD_SERVICE_NAME=os.path.expanduser("~/.local/share/systemd/user/dexbot.service")

SYSTEMD_SERVICE_FILE="""
[Unit]
Description=Dexbot

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
        # dexbot already installed
        # so just tell cli.py to quietly restart the daemon
        config["systemd_status"] = "installed"
        return
    if d.yesno("Do you want to install dexbot as a background (daemon) process?") == d.OK:
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
    if 'module' in bot:
        inv_map = {v:k for k,v in STRATEGIES.items()}
        strategy = inv_map[(bot['module'],bot['bot'])]
    else:
        strategy = 'Echo'
    code, tag = d.radiolist("Choose a bot strategy",
                            choices=select_choice(strategy,[(i,i) for i in STRATEGIES]))
    if code != d.OK: raise QuitException()
    bot['module'], bot['bot'] = STRATEGIES[tag]
    # import the bot class but we don't __init__ it here
    klass = getattr(
        importlib.import_module(bot["module"]),
        bot["bot"]
    )
    # use class metadata for per-bot configuration
    configs = klass.configure()
    if configs:
        for c in configs:
            process_config_element(c,d,bot)
    else:
        d.msgbox("This bot type does not have configuration information. You will have to check the bot code and add configuration values to config.yml if required")
    return bot

                            
    
def configure_dexbot(config):
    d = dialog.Dialog(dialog="dialog",autowidgetsize=True)
    d.set_background_title("dexbot configuration")
    tag = ""
    while not tag:
        code, tag = d.radiolist("Choose a Witness node to use",
                       choices=select_choice(config.get("node"),NODES))
        if code != d.OK: raise QuitException()
        if not tag: d.msgbox("You need to choose a node")
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
    
    
