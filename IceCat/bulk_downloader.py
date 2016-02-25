import os, time, datetime, sys

from threading import Thread
import requests
from time import time, sleep
import queue
import logging
import progressbar



class fetchURLs(object):
    '''     
    Download and save a list of URLs
    using parallel connections.  A separate session is maintained for each
    download thread.     If throttling is detected (broken connections)
    the thread is terminated in order to reduce the load on the web serve.
    If a local file already exists for a given URL, that URL is skipped.
    There is no check currently if remote document is     newer than the
    local file.     If the URL does not end with a file name fetchURLs
    will generate a default filename in the format <website>.index.html

    :param urls: A list of absolute URLs to fetch
    :param data_dir:  Directory to save files in
    :param connections: Number of simultanious download threads
    :param auth: Username and password touple, if needed for website authentication
    :param log: An optional logging.getLogger() instance

    This class is usually called from IceCat

    '''
    def __init__(self, 
                log=None,
                urls = [
                    'http://www.google.com/', 
                    'http://www.bing.com/', 
                    'http://www.yahoo.com/',
                    ],
                data_dir = '_data/product_xml/',
                auth=('goober@aol.com','password'),
                connections=5):

        self.urls = queue.Queue()

        for i in urls:
            self.urls.put(i)

        self.data_dir = data_dir
        self.connections = connections
        self.auth = auth
        self.log = log
        if not log:
            self.log = logging.getLogger()
        
        logging.getLogger("requests").setLevel(logging.WARNING)
        # self.log.setLevel(logging.WARNING)

        print("Downloading product details:")
        with progressbar.ProgressBar(max_value=len(urls)) as self.bar:
            self._download()

    def _worker(self):
        s = requests.Session()
        s.auth = self.auth

        while True:
            url = self.urls.get()
            self.bar.update(self.success_count)
            bn = os.path.basename(url)
            if not bn:
                file = self.data_dir + os.path.basename(os.path.dirname(url)) + '.index.html'
            else:
                file = self.data_dir + bn

            if os.path.isfile(file):
                modified = os.path.getmtime(file)
                # headers = {'If-Modified-Since': }  # do this later
                # self.log.warning("Skipping {} - file exists".format(url))
                self.urls.task_done()  
                self.success_count += 1
                continue

            try:
                res = s.get(url)
            except:
                self.log.warning("Bad request {} for url: {}".format(sys.exc_info(), url))
                #put item back into queue
                self.urls.put(url)
                self.urls.task_done()  
                # this could be due to throttling, exit thread  
                break


            
            if 200 <=res.status_code < 299:
                self.success_count += 1
                self.log.debug("Fetched {}".format(url))
            else:
                self.log.warning("Bad status code: {} for url: {}".format(res.status_code, url))
                self.urls.task_done()    
                continue

            with open(file, 'wb') as f:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            

            self.urls.task_done()    
    
    def _download(self):
        self.success_count = 0
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        start = time()
        for i in range(self.connections):
            t = Thread(target=self._worker)
            t.daemon = True
            t.start()
        self.urls.join()
        self.log.info('fetched {} URLs in %0.3fs'.format(self.success_count) % (time()-start))

    def get_count(self):
        '''
        Returns the number of successfully fetched urls
        '''
        return self.success_count