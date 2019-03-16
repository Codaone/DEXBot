import unittest
from dexbot.controllers.main_controller import MainController
from bitshares import BitShares
from dexbot.config import Config
from dexbot.views.errors import PyQtHandler
class test_MainController(unittest.TestCase):
	def setUp(self):
		self.config=Config()
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
		self.bitShares=BitShares(node_list)
		self.pyqt_handler=PyQtHandler()
		self.main_cantroller=MainController(self.bitShares,self.config)
	def test_init(self):
		self.assertIsInstance(self.main_cantroller,MainController,'class is not MainController!')
		self.assertIsInstance(self.pyqt_handler,PyQtHandler,'class is not PyQtHandler!')
	def test_set_info_handler(self):
		self.main_cantroller.set_info_handler(self.pyqt_handler)
	def test_start_worker(self):
		self.main_cantroller.start_worker('worder_name',self.config,None)
	def test_pause_worker(self):
		self.main_cantroller.pause_worker('worder_name',self.config)
	@unittest.skip('skip remove_worker test!')
	def test_remove_worker(self):
		self.main_cantroller.remove_worker('worder_name')
	def test_create_worker(self):
		MainController.create_worker('worder_name')
	def tearDown(self):
		pass
#-------------------------test------------------
def suite():
	suite=unittest.TestSuite()
	suite.addTest(test_MainController('test_init'))
	suite.addTest(test_MainController('test_set_info_handler'))
	suite.addTest(test_MainController('test_start_worker'))
	suite.addTest(test_MainController('test_pause_worker'))
	suite.addTest(test_MainController('test_remove_worker'))
	suite.addTest(test_MainController('test_create_worker'))
	return suite
if __name__=='__main__':
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())