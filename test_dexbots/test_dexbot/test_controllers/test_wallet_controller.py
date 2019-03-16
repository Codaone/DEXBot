import unittest
from bitshares import BitShares
from dexbot.controllers.wallet_controller import WalletController
class test_WalletController(unittest.TestCase):
	def setUp(self):
		node_list=[      "wss://eu.openledger.info/ws",
            "wss://bitshares.openledger.info/ws",
            "wss://dexnode.net/ws",
            "wss://japan.bitshares.apasia.tech/ws",
            "wss://bitshares-api.wancloud.io/ws",
            "wss://openledger.hk/ws",
            "wss://bitshares.apasia.tech/ws",
            "wss://bitshares.crypto.fans/ws",
            "wss://kc-us-dex.xeldal.com/ws",
            "wss://api.bts.blckchnd.com",
            "wss://btsza.co.za:8091/ws",
            "wss://bitshares.dacplay.org/ws",
            "wss://bit.btsabc.org/ws",
            "wss://bts.ai.la/ws",
            "wss://ws.gdex.top",
            "wss://na.openledger.info/ws",
            "wss://node.btscharts.com/ws",
            "wss://status200.bitshares.apasia.tech/ws",
            "wss://new-york.bitshares.apasia.tech/ws",
            "wss://dallas.bitshares.apasia.tech/ws",
            "wss://chicago.bitshares.apasia.tech/ws",
            "wss://atlanta.bitshares.apasia.tech/ws",
            "wss://us-la.bitshares.apasia.tech/ws",
            "wss://seattle.bitshares.apasia.tech/ws",
            "wss://miami.bitshares.apasia.tech/ws",
            "wss://valley.bitshares.apasia.tech/ws",
            "wss://canada6.daostreet.com",
            "wss://bitshares.nu/ws",
            "wss://api.open-asset.tech/ws",
            "wss://france.bitshares.apasia.tech/ws",
            "wss://england.bitshares.apasia.tech/ws",
            "wss://netherlands.bitshares.apasia.tech/ws",
            "wss://australia.bitshares.apasia.tech/ws",
            "wss://dex.rnglab.org",
            "wss://la.dexnode.net/ws",
            "wss://api-ru.bts.blckchnd.com",
            "wss://node.market.rudex.org",
            "wss://api.bitsharesdex.com",
            "wss://api.fr.bitsharesdex.com",
            "wss://blockzms.xyz/ws",
            "wss://eu.nodes.bitshares.ws",
            "wss://us.nodes.bitshares.ws",
            "wss://sg.nodes.bitshares.ws",
            "wss://ws.winex.pro",
            "wss://api.bts.mobi/ws",
            "wss://api.btsxchng.com",
            "wss://api.bts.network/",
            "wss://btsws.roelandp.nl/ws",
            "wss://api.bitshares.bhuz.info/ws",
            "wss://bts-api.lafona.net/ws",
            "wss://kimziv.com/ws",
            "wss://api.btsgo.net/ws",
            "wss://bts.proxyhosts.info/wss",
            "wss://bts.open.icowallet.net/ws",
            "wss://de.bts.dcn.cx/ws",
            "wss://fi.bts.dcn.cx/ws",
            "wss://crazybit.online",
            "wss://freedom.bts123.cc:15138/",
            "wss://bitshares.bts123.cc:15138/",
            "wss://api.bts.ai",
            "wss://ws.hellobts.com",
            "wss://bitshares.cyberit.io",
            "wss://bts-seoul.clockwork.gr",
            "wss://bts.liuye.tech:4443/ws",
            "wss://btsfullnode.bangzi.info/ws",
            "wss://api.dex.trading/",
            "wss://citadel.li/node"
        ]
		bitshares=BitShares(node_list)
		self.WalletController=WalletController(bitshares)
	@unittest.skip('skip wallet_created test!')
	def test_wallet_created(self):
		self.WalletController.wallet_created('111','12')@unittest.skip('skip wallet_created test!')
	@unittest.skip('skip create_wallet test!')
	def test_create_wallet(self):
		self.WalletController.create_wallet('111','12')
	@unittest.skip('skip unlock_wallet test!')
	def test_unlock_wallet(self):
		self.WalletController.unlock_wallet('111')
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_WalletController('test_wallet_created'))
		suite.addTest(test_WalletController('test_create_wallet'))
		suite.addTest(test_WalletController('test_unlock_wallet'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())