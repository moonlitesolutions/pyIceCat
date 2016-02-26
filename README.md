[![Build Status](https://travis-ci.org/moonlitesolutions/pyIceCat.svg?branch=master)](https://travis-ci.org/moonlitesolutions/pyIceCat)
[![Documentation Status](https://readthedocs.org/projects/pyicecat/badge/)](http://pyicecat.readthedocs.org/en/)

IceCat
------
IceCat module pulls down a local copy of data from the http://icecat.biz/ open catalog.  The module requires login credentials to the IceCat website.  The basic catalog version if free with 500k products.  The full catalog contains ~3mln products and distrubuted with a paid subscription.

Requirements
* python 3.3 or above, (64-bit for full catalog import)
* requests, urlib3, xml2dict,  progressbar2 libraries.
* see requirements.txt in the source distribution for details


Features
* For each product category id, manufacturer id are resolved to their actual names.
* Product detail data can be added to the daily and full index, with flexible data fields
* English language data import
* The output is a flat JSON file (nested lists are flattened)
* Fast parallel download of the product xml files with threads
* Source data files are preserved in the filesystem for reference
* Flexible XML field mapping 
* Tested against live IceCat web API


Basic usage:

	from IceCat import IceCat

	# setup temp data directory, output file name, auth info
	data_dir = '_daily_test_data/'
	auth = ('icat_user', 'icat_passwd')
	output_file = 'daily.json'

	# specify additional product detail keys
	detail_keys=['ProductDescription[@LongDesc]',
				'ShortSummaryDescription',
				'LongSummaryDescription',
				'ProductDescription[@ShortDesc]']

	# create the catalog instance. 
	# this will pull reference files, and the daily produc index file
	catalog = IceCat.IceCatCatalog(data_dir=data_dir, auth=auth)

	# add product details
	# this will download and parse individual product XML for 
	# every item listed in the daily file
	catalog.add_product_details_parallel(keys=detail_keys,connections=100)

	# save the results to a JSON file
	catalog.dump_to_file(output_file)
