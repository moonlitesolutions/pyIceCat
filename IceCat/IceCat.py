# use C implementation for speed
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import json
import xmltodict

import requests
import gzip
import os, sys
import collections

from multiprocessing import Process, Queue

from IceCat import bulk_downloader

# English only
langid = "1"


class IceCat(object):
    '''
    Base Class for all Ice Cat Mappings
    '''
    def __init__(self, log=None, xml_file=None, auth=('user','passwd'), data_dir='_data/'):
        if log:
            self.log = log
        else:
            import logging
            self.log = logging.getLogger()

        self.auth = auth
        self.data_dir = data_dir

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if xml_file is None:
            xml_file = self._download()

        if os.path.isfile(xml_file):
            self._parse(xml_file)
        else:
            self.log.error("File does not exist {}".format(xml_file))
            return False

    def _download(self):

        self.log.info("Downloading {} from {}".format(self.TYPE,self.baseurl + self.FILENAME))
        
        # save the response in the data dir before parsing
        self.local_file = self.data_dir + os.path.basename(self.FILENAME)
        res = requests.get(self.baseurl + self.FILENAME, auth=self.auth, stream=True)
        with open(self.local_file, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
            f.closed
        self.log.debug("Got headers: {}".format(res.headers))
        

        if 200 <=res.status_code < 299:
            # handle gzipped files
            return self.local_file
            # if self.local_file.endswith('.gz'):
            #     with gzip.open(self.local_file, 'rb') as f:
            #         return ET.parse(f).getroot()
            # else:
            #         return ET.parse(self.local_file).getroot()
        else:
            self.log.error("Did not receive good status code: {}".format(res.status_code))
            return False

    def get_data(self):
        return self.data_map

    

class IceCatSupplierMapping(IceCat):
    baseurl = 'https://data.icecat.biz/export/freeurls/'
    FILENAME='supplier_mapping.xml'
    TYPE = 'Supplier Mapping'

    def _parse(self, xml_file):

        if xml_file:
            data = ET.parse(xml_file).getroot()
        else:
            self.log.error("Failed to retrieve suppliers")
            return False

        '''
        Data is an XML ElementTree Object
        '''
        self.id_map = {}
        self.catid = ''
        self.catname = ''

        for elem in data.iter('SupplierMapping'):
            self.mfrid = elem.attrib['supplier_id']
            self.mfrname = elem.attrib['name']
            if not self.mfrname:
                self.mfrname = "Unknown"
            self.id_map[self.mfrid] = self.mfrname
        self.log.info("Parsed {} Manufacturers from IceCat Supplier Map".format(str(len(self.id_map.keys()))))

    def get_mfr_byId(self, mfr_id):
        if mfr_id in self.id_map:
            return self.id_map[mfr_id]
        return False

class IceCatCategoryMapping(IceCat):
    baseurl = 'https://data.icecat.biz/export/freexml/refs/'
    FILENAME='CategoriesList.xml.gz'
    TYPE = 'Categories List'

    def _parse(self, xml_file):
        if xml_file.endswith('.gz'):
            with gzip.open(xml_file, 'rb') as f:
                data = ET.parse(f).getroot()
        else:
             data = ET.parse(xml_file).getroot()

        '''
        Data is an XML ElementTree Object
        '''
        self.id_map = {}
        self.catid = ''
        self.catname = ''
        self.findpath = 'Name[@langid="' + langid + '"]'
        for elem in data.iter('Category'):
            self.catid = elem.attrib['ID']
            for name in elem.iterfind(self.findpath):
                self.catname = name.attrib['Value']
                # only need one match
                break
            if not self.catname:
                self.catname = "Unknown"
            self.id_map[self.catid] = self.catname

        self.log.info("Parsed {} Categories from IceCat CategoriesList".format(str(len(self.id_map.keys()))))
    
    def get_cat_byId(self, cat_id):
        if cat_id in self.id_map:
            return self.id_map[cat_id]
        return False


class IceCatProductDetails(IceCat):
    def __init__(self,  keys, cleanup_data_files=True, filename=None, *args, **kwargs): 
        self.keys = keys
        self.FILENAME = filename
        self.cleanup_data_files = cleanup_data_files
        super(IceCatProductDetails, self).__init__(*args, **kwargs)

    baseurl = 'https://data.icecat.biz/'
    TYPE = 'Product details'

    o = {}


    def _parse(self, xml_file):
        self.xml_file = xml_file
        data = ET.parse(xml_file).getroot()
        
        # for elem in data.iter('Product'):
        for attribute in self.keys:
            if '@' in attribute:
                attr = attribute[attribute.index("@") + 1:attribute.rindex("]")]
                q = data.find('./*'+attribute)
                if q is not None:
                    self.o.update({attr.lower():q.attrib[attr]})
            else:
                for name in data.iter(attribute):
                    if name.text:
                        self.o.update({attribute.lower():name.text})
                    else:
                        for i in name.attrib:
                            self.o.update({i.lower():name.attrib[i]})


        self.log.debug("Parsed product details for {}".format(xml_file))
        if self.cleanup_data_files:
            try:
                os.remove(xml_file)
            except:
                self.log.warning("Unable to delete temp file {}".format(xml_file))

    def get_data(self):
        return self.o




class IceCatCatalog(IceCat):
    def __init__(self, suppliers, categories, exclude_keys=['Country_Markets'], fullcatalog=False, *args, **kwargs): 
        self.suppliers = suppliers
        self.categories = categories
        self.exclude_keys = exclude_keys
        if fullcatalog:
            self.FILENAME='files.index.xml'
        else:
            self.FILENAME='daily.index.xml'
        super(IceCatCatalog, self).__init__(*args, **kwargs)


    baseurl = 'https://data.icecat.biz/export/freexml/EN/'
    TYPE = 'Catalog Index'


    '''
     special handling of the input data. Based on IceCAT OCI Revision date: April 24, 2015, Version 2.46 
     - resolve supplier ID, and Category ID to their english names
     - unroll ean_upcs nested structure to flat value, or list
     - convert attribute names according to the table (to lower case)
     - drop keys in the exclude_list, default ['Country_Markets']
     - discard parent layers above 'file' key
    '''

    _namespaces = {
        'Product_ID': 'product_id',
        'Updated': 'updated',
        'Quality': 'quality',
        'Supplier_id': 'supplier_id',
        'Prod_ID': 'prod_id',
        'Catid': 'catid',
        'On_Market': 'on_market',
        'Model_Name': 'model_name',
        'Product_View': 'product_view',
        'HighPic': 'highpic',
        'HighPicSize': 'highpicsize',
        'HighPicWidth': 'highpicwidth',
        'HighPicHeight': 'highpicheight',
        'Date_Added': 'date_added',
    }

    def _postprocessor(self, path, key, value):
        if key == "file":
            '''
            Look up supplier id and category
            '''
            try:
                value.update({'supplier' : self.suppliers.get_mfr_byId(value['supplier_id'])})
            except:
                self.log.warning("Unable to find supplier for supplier_id: {}".format(value['supplier_id']))

            try:
                value.update({'category' : self.categories.get_cat_byId(value['catid']).title()})
            except:
                self.log.warning("Unable to find category for catid: {}".format(value['catid']))

            
            '''
            unroll ean_upcs. sometimes this is a list of single value dicts, other times it's a string.
            '''
            if 'ean_upcs' in value:
                try:
                    value['ean_upcs'] =[value['ean_upcs']['ean_upc']['Value']]
                except TypeError:
                    upcs = []
                    for item in value['ean_upcs']['ean_upc']:
                         upcs.append(list(item.values())[0])
                    value['ean_upcs'] = upcs
                except:
                    # something bad happened with upcs
                    self.log.warning("Unable to unroll ean_upcs {} for product_id: {}".format(sys.exc_info(), value['product_id']))


        # skip keys we are not interested in.
        elif key in self.exclude_keys:
            return None


        return key.lower(), value


    #used to flatten a nested structure if needed
    def _flatten(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self._flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _parse(self, xml_file):
        self.xml_file = xml_file
        with open(self.xml_file, 'rb') as f:
            self.o = xmltodict.parse(f, attr_prefix='', postprocessor=self._postprocessor,
                namespace_separator='', process_namespaces=True, namespaces=self._namespaces)
        f.closed

        # peel down to file key
        self.o = self.o['icecat-interface']['files.index']['file']
        self.log.info("Parsed {} products from IceCat catalog".format(str(len(self.o))))
        return len(self.o)


    def add_product_details_parallel(self,keys=['ProductDescription'],connections=5):
        self.keys = keys
        self.connections = connections
        baseurl = 'https://data.icecat.biz/'
        TYPE = 'Product details'
        urls=[]

        xml_dir = self.data_dir + 'product_xml/'

        if not os.path.exists(xml_dir):
            os.makedirs(xml_dir)

        for item in self.o: 
            urls.append(baseurl + item['path'].encode('latin-1').decode())
        self.log.info("Downloading detail data with {} connections".format(self.connections))

        download = bulk_downloader.fetchURLs(log=self.log, urls=urls, auth=self.auth, 
                                            connections=self.connections,
                                            data_dir=xml_dir)


        for item in self.o:
            xml_file = xml_dir + os.path.basename(item['path'])
            try:
                product_detais = IceCatProductDetails(xml_file=xml_file, keys=self.keys, 
                    auth=self.auth, data_dir=xml_dir, log=self.log,cleanup_data_files=False)
                item.update(product_detais.get_data())
            except:
                self.log.error("Could not obtain product details from IceCat for product_id {}".format(item['path']))
    
    def add_product_details(self, keys=['ProductDescription']):
        self.keys = keys
        for item in self.o:
            try:
                product_detais = IceCatProductDetails(filename=item['path'], keys=self.keys, 
                    auth=self.auth, data_dir=self.data_dir, log=self.log)
                item.update(product_detais.get_data())
            except:
                self.log.error("Could not obtain product details from IceCat for product_id {}".format(item['path']))

        

    def get_data(self):
        return self.o

    def dump_to_file(self, filename=None):
        if filename:
            self.json_file = filename
        else:
            # change extension for the JSON output
            self.json_file = os.path.splitext(self.xml_file)[0]+'.json'
        
        with open(self.json_file, 'w') as f:
            f.write(json.dumps(self.o,indent=2))
        self.log.info("JSON output written to {}".format(self.json_file))
        f.closed


    
    