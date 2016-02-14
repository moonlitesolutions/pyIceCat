import sys
import logging
import unittest

from IceCat import bulk_downloader

class ModTest(unittest.TestCase):

	data_dir = '_test_data/'
	
	logging.basicConfig(filename='test.log',level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	log = logging.getLogger()

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

		'''
		do not add additional bulk_downloader.fetchURLs tests to this file
		the twisted reactor is not restartable and additional tests will fail.
		'''


if __name__ == '__main__':    
	unittest.main()