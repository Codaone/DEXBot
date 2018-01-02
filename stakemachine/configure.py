"""
A module to provide an interactive process for stakemachine configuration
Requires a working dialog tool: so UNIX-like sytems only
"""


import dialog, importlib, os


NODES=[("wss://openledger.hk/ws", "OpenLedger"),
       ("wss://dexnode.net/ws", "DEXNode"),
       ("wss://node.bitshares.eu/ws", "BitShares.EU"),
       ("wss://node.testnet.bitshares.eu","BitShares.EU testnet")]

STRATEGIES={'Echo':('stakemachine.strategies.echo','Echo'),
            'Liquidity Walls':('stakemachine.strategies.walls','Walls'),
            'Storage Demo':('stakemachine.strategies.storagedemo','StorageDemo')}

class QuitException(Exception): pass

def select_choice(current,choices):
    return [(tag,text,current == tag) for tag,text in choices]

def configure_bot(d,bot):
    code, txt = d.inputbox("BitShares account name for the bot to operate with",init=bot.get("account",''))
    if code != d.OK: raise QuitException()
    bot['account'] = txt
    code, txt = d.inputbox("BitShares market to operate on, in the format ASSET:OTHERASSET, example \"USD:BTS\"",init=bot.get("market",''))
    if code != d.OK: raise QuitException()
    bot['market'] = txt
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
    # check if a classmethod configure() exists and run it
    # pass in the bot config dict, and the Dialog object
    # configure should make its own dialog calls for own config values
    if hasattr(klass,"configure"):
        klass.configure(bot,d)
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
    os.system("clear")
    return config

if __name__=='__main__':
    print(repr(configure({})))
    
    
