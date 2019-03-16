import unittest
import os
def suite_dir():
	start_dir=os.path.join(os.getcwd())+'/DEXBot/test_dexbots'#vscode
	#start_dir=os.path.join(os.getcwd())#sublime
	# print(start_dir)
	discover=unittest.defaultTestLoader.discover(start_dir)
	return discover
if __name__=='__main__':
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite_dir())