from IceCat import IceCat
import sys, os
import logging
import unittest


class ModTest(unittest.TestCase):


	
	#where to store various downloaded xml files
	data_dir = '_test_data/'

	logging.basicConfig(filename='test.log',level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	log = logging.getLogger()

	try:
		icat_user = os.environ['ICAT_USER']
		icat_passwd = os.environ['ICAT_PASSWD']
	except:
		icat_user = 'foo'
		icat_passwd = 'bar'

	auth = (icat_user, icat_passwd)

	def testCategoriesLocal(self):
		'''
		test categories parsng with a local xml file
		'''
		categories = IceCat.IceCatCategoryMapping(log=self.log, xml_file="_test_data/CategoriesList.test.xml", 
													data_dir=self.data_dir)
		self.assertEqual(categories.get_cat_byId("1648"), 'popcorn poppers')

	def testSupplierMaps(self):
		'''
		download live supplier reference file.  Verify parsing 7 = Acer
		this requires real IceCat user name and password
		'''
		suppliers = IceCat.IceCatSupplierMapping(log=self.log, auth=self.auth, data_dir=self.data_dir)
		self.assertEqual(suppliers.get_mfr_byId("7"),'Acer')

	def testIndexfile(self):
		'''
		load a small local index file and parse. no internet connections in this test
		this test check that data is parsed correctly to the dictionary
		no product details are loaded in this test
		'''
		categories = IceCat.IceCatCategoryMapping(log=self.log, xml_file="_test_data/CategoriesList.test.xml", 
													data_dir=self.data_dir)

		suppliers = IceCat.IceCatSupplierMapping(log=self.log, auth=self.auth, xml_file="_test_data/supplier_mapping.xml",
													data_dir=self.data_dir)
		self.assertEqual(categories.get_cat_byId("1648"), 'popcorn poppers')
		self.assertEqual(suppliers.get_mfr_byId("7"),'Acer')
		catalog = IceCat.IceCatCatalog(log=self.log, xml_file="_test_data/daily.index.test.xml", 
										suppliers=suppliers, categories=categories, data_dir=self.data_dir)
		
		# run data checks on product id, and supplier/category resolution
		self.assertEqual(catalog.get_data()[0]['prod_id'],u'91.42R29.002')
		self.assertEqual(catalog.get_data()[2]['supplier'],'Intel')
		self.assertEqual(catalog.get_data()[5]['category'],'Living Room Bookcases')



	def testIndexfileWithDetails(self):
		'''
		load a small local index file and parse. connect to IceCat and download detail data
		this test check that data is parsed correctly to the dictionary
		product details are tested
		'''
		categories = IceCat.IceCatCategoryMapping(log=self.log, xml_file="_test_data/CategoriesList.test.xml", 
													data_dir=self.data_dir)

		suppliers = IceCat.IceCatSupplierMapping(log=self.log, auth=self.auth, xml_file="_test_data/supplier_mapping.xml",
													data_dir=self.data_dir)
		self.assertEqual(categories.get_cat_byId("1648"), 'popcorn poppers')
		self.assertEqual(suppliers.get_mfr_byId("7"),'Acer')
		catalog = IceCat.IceCatCatalog(log=self.log, xml_file="_test_data/daily.index.test.xml", 
										suppliers=suppliers, categories=categories, 
										data_dir=self.data_dir,
										auth=self.auth)
		
		# run data checks on product id, and supplier/category resolution
		self.assertEqual(catalog.get_data()[0]['prod_id'],u'91.42R29.002')
		self.assertEqual(catalog.get_data()[2]['supplier'],'Intel')
		self.assertEqual(catalog.get_data()[5]['category'],'Living Room Bookcases')

		detail_keys=['ProductDescription[@LongDesc]',
					'ShortSummaryDescription',
					'LongSummaryDescription',
					'ProductDescription[@ShortDesc]']

		# test the single threaded method
		catalog.add_product_details(keys=detail_keys)
		self.assertEqual(catalog.get_data()[2]['shortdesc'],'64-bit Xeon Processor 2.80 GHz, 1M Cache, 800 MHz FSB')


	def testIndexfileParallel(self):
		'''
		load a small local index file and parse. connect to IceCat and download detail data
		this test check that data is parsed correctly to the dictionary
		product details are tested. parallel download tested
		'''
		categories = IceCat.IceCatCategoryMapping(log=self.log, xml_file="_test_data/CategoriesList.test.xml", 
													data_dir=self.data_dir)

		suppliers = IceCat.IceCatSupplierMapping(log=self.log, auth=self.auth, xml_file="_test_data/supplier_mapping.xml",
													data_dir=self.data_dir)
		self.assertEqual(categories.get_cat_byId("1648"), 'popcorn poppers')
		self.assertEqual(suppliers.get_mfr_byId("7"),'Acer')
		catalog = IceCat.IceCatCatalog(log=self.log, xml_file="_test_data/daily.index.test.xml", 
										suppliers=suppliers, categories=categories, 
										data_dir=self.data_dir,
										auth=self.auth)
		
		# run data checks on product id, and supplier/category resolution
		self.assertEqual(catalog.get_data()[0]['prod_id'],u'91.42R29.002')
		self.assertEqual(catalog.get_data()[2]['supplier'],'Intel')
		self.assertEqual(catalog.get_data()[5]['category'],'Living Room Bookcases')

		detail_keys=['ProductDescription[@LongDesc]',
					'ShortSummaryDescription',
					'LongSummaryDescription',
					'ProductDescription[@ShortDesc]']

		# test the multi threaded method
		catalog.add_product_details_parallel(keys=detail_keys,connections=50)
		self.assertEqual(catalog.get_data()[2]['shortdesc'],'64-bit Xeon Processor 2.80 GHz, 1M Cache, 800 MHz FSB')

		# test file dump
		file = 'test.small.json'
		if os.path.exists(file):
			os.remove(file)

		catalog.dump_to_file(file)
		self.assertEqual(os.path.isfile(file), True)



	def _testXDailyDownload(self):
		'''
		load all data files from Ice Cat. 
		this test check that data is parsed correctly to the dictionary
		product details are tested. parallel download tested
		it's normal for this test to run long, several minutes
		'''
		data_dir = '_daily_test_data/'

		categories = IceCat.IceCatCategoryMapping(log=self.log, data_dir=self.data_dir, auth=self.auth)
		suppliers = IceCat.IceCatSupplierMapping(log=self.log, auth=self.auth, data_dir=self.data_dir)

		self.assertEqual(categories.get_cat_byId("1648"), 'popcorn poppers')
		self.assertEqual(suppliers.get_mfr_byId("7"),'Acer')

		catalog = IceCat.IceCatCatalog(log=self.log,
										suppliers=suppliers, categories=categories, 
										data_dir=self.data_dir,
										auth=self.auth)
				
		detail_keys=['ProductDescription[@LongDesc]',
					'ShortSummaryDescription',
					'LongSummaryDescription',
					'ProductDescription[@ShortDesc]']

		# test the multi threaded method
		catalog.add_product_details_parallel(keys=detail_keys,connections=50)

		# test file dump
		file = 'test.large.json'
		if os.path.exists(file):
			os.remove(file)

		catalog.dump_to_file(file)
		self.assertEqual(os.path.isfile(file), True)

		
	


if __name__ == '__main__':    
	unittest.main()

# categories = IceCat.IceCatCategoryMapping(log=log, xml_file="_data/CategoriesList.xml")



if __name__ == '__main__':    
	unittest.main()

# categories = IceCat.IceCatCategoryMapping(log=log, xml_file="_data/CategoriesList.xml")
# # categories = IceCat.IceCatCategoryMapping(log=log)
# print categories.get_cat_byId("234")

# exclude_keys = ['Country_Markets']
# # catalog = IceCat.IceCatCatalog(log=log, xml_file="_data/daily.index.small.xml", suppliers=suppliers, categories=categories, exclude_keys=exclude_keys)
# # catalog = IceCat.IceCatCatalog(log=log, xml_file="_data/daily.index.xml", suppliers=suppliers, categories=categories, exclude_keys=exclude_keys)
# catalog = IceCat.IceCatCatalog(log=log, suppliers=suppliers, categories=categories, exclude_keys=exclude_keys)


# detail_keys=['ProductDescription[@LongDesc]', 'ProductDescription[@ShortDesc]', 'LongSummaryDescription', 'ShortSummaryDescription']
# # # detail_keys=['ProductDescription[@LongDesc]','ShortSummaryDescription','LongSummaryDescription','ProductDescription[@ShortDesc]']

# catalog.add_product_details_parallel(keys=detail_keys,connections=100)
# catalog.dump_to_file()
# catalog.dump_to_file('foo.small.json')


# urls=[
# 	'https://data.icecat.biz/export/freexml.int/EN/140206.xml',
# 	'https://data.icecat.biz/export/freexml.int/EN/140202.xml',
# 	'https://data.icecat.biz/export/freexml.int/EN/126442.xml',
# 	'https://data.icecat.biz/export/freexml.int/EN/108912.xml',
# 	'https://data.icecat.biz/export/freexml.int/EN/110722.xml',
# 	]

# auth = ('gokoyev@gmail.com','IceCat12')

# download = bulk_downloader.fetchURLs(log=log, urls=urls, auth=auth)


# if __name__ == '__main__':    
# 	catalog.add_product_details_parallel(keys=detail_keys)



# catalog = IceCat.IceCatCatalog(log=log, xml_file="_data/files.index.xml", suppliers=suppliers, categories=categories, exclude_keys=exclude_keys)
# # print catalog.full()