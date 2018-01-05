from dexbot.basestrategy import BaseStrategy


class StorageDemo(BaseStrategy):

    configure = [] # don't need extra config
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ontick += self.tick

    def tick(self, i):
        print("previous block: %s" % self["block"])
        print("new block: %s" % i)
        self["block"] = i
