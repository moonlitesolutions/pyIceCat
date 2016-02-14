import time, os, base64

from threading import Thread
import requests
from time import time, sleep
from Queue import Queue
import logging


# based on http://stackoverflow.com/questions/3490173/how-can-i-speed-up-fetching-pages-with-urllib2-in-python
# 

# modified by k3i to limit number of simultanious connections with DeferredSemaphore


class fetchURLs(object):
    def __init__(self, log=None, 
                urls = [
                    'http://www.google.com/', 
                    'http://www.bing.com/', 
                    'http://www.yahoo.com/',
                    ],
                data_dir = '_data/product_xml/',
                auth=('goober@aol.com','password'),
                connections=5):

        self.urls = Queue()
        for i in urls:
            self.urls.put(i)

        self.data_dir = data_dir
        self.connections = connections
        if auth is not None:
            self.auth = auth
        if log:
            self.log = log
        else:
            self.log = logging.getLogger()
        
        logging.getLogger("requests").setLevel(logging.WARNING)
        # self.log.setLevel(logging.WARNING)

        self._download()

    def _worker(self):
        while True:
            url = self.urls.get()
            bn = os.path.basename(url)
            if not bn:
                file = self.data_dir + os.path.basename(os.path.dirname(url)) + '.index.html'
            else:
                file = self.data_dir + bn

            res = requests.get(url, auth=self.auth, stream=True)
            with open(file, 'wb') as f:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            if 200 <=res.status_code < 299:
                self.success_count += 1
                self.log.debug("Fetched {}".format(url))
            else:
                self.log.error("Bad status code: {} for url: {}".format(res.status_code, url))

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
        returns number of successfully fetched urls
        '''
        return self.success_count