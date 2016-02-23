import sys
import logging
import unittest

import cProfile, pstats


from IceCat import bulk_downloader

class ModTest(unittest.TestCase):

	data_dir = '_test_data/'
	
	logging.basicConfig(filename='test.log',level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	log = logging.getLogger()

	def setUp(self):
		"""init each test"""
		# self.testtree = SplayTree (1000000)
		self.pr = cProfile.Profile()
		self.pr.enable()
		print("\n<<<---")

	def tearDown(self):
		"""finish any test"""
		p = pstats.Stats(self.pr)
		p.strip_dirs()
		p.sort_stats ('cumtime')
		p.print_stats ()
		print("\n--->>>")


	def testReactor(self):
		'''
		this verifies that basic Auth is working wit the downloader
		also tests SSL connction, and basic downloads.
		'''
		
		download = bulk_downloader.fetchURLs(log=self.log, 
											urls=['https://httpbin.org/basic-auth/icat/passwd',
												'http://www.google.com/', 
												'http://www.bing.com/', 
												'http://www.yahoo.com/',],
											data_dir=self.data_dir,
											auth=('icat', 'passwd'))
		# we should have downloaded 4 urls
		self.assertEqual(download.get_count(), 4)

	def testReactor2(self):
		'''
		this verifies that basic Auth is working wit the downloader
		also tests SSL connction, and basic downloads.
		'''
		
		download = bulk_downloader.fetchURLs(log=self.log, 
											urls=['https://httpbin.org/basic-auth/icat/passwd',
												'http://www.google.com/deadbeef', 
												'http://www.bing.com/', 
												'http://www.yahoo.com/',],
											data_dir=self.data_dir,
											auth=('icat', 'passwd'))
		# we should have downloaded 3 urls, faild for deadbeef
		self.assertEqual(download.get_count(), 3)




if __name__ == '__main__':    
	unittest.main()