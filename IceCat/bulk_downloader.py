from twisted.internet import defer, reactor
from twisted.web.client import getPage, downloadPage, HTTPConnectionPool
import time, os, base64

from twisted.internet.defer import DeferredSemaphore

# based on http://stackoverflow.com/questions/3490173/how-can-i-speed-up-fetching-pages-with-urllib2-in-python
# answered Aug 16 '10 at 3:20 by habnabit

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

        self.urls = urls
        self.data_dir = data_dir
        self.connections = connections
        if auth is not None:
            self.auth = auth
        if log:
            self.log = log
        else:
            import logging
            self.log = logging.getLogger()
        
        self._download()


    def _processPage(self, page, url):
        # do somewthing here.
        return url, len(page)

    def _printResults(self, result, url):
        for success, value in result:
            if not success:
                self.log.warning("Failure fetching {}: {}".format(url, value.getErrorMessage()))
            else:
                self.success_count += 1
                self.log.debug("Fetched {}".format(url))

    def _printDelta(self, _, start):
        delta = time.time() - start
        self.log.info('fetched {} URLs in %0.3fs'.format(len(self.urls)) % (delta,))
        return delta

    def _fetchURLs(self,auth,connections):
        headers={"Authorization": auth}
        callbacks = []
        sem = defer.DeferredSemaphore(connections)   
        for url in self.urls:
            bn = os.path.basename(url)
            if not bn:
                file = self.data_dir + os.path.basename(os.path.dirname(url)) + '.index.html'
            else:
                file = self.data_dir + bn
            d = sem.run(downloadPage, url, file, headers=headers)
            # d.addCallback(self._processPage, url)
            callbacks.append(d)

        callbacks = defer.DeferredList(callbacks)
        callbacks.addCallback(self._printResults, url)
        return callbacks

    @defer.inlineCallbacks
    def _main(self):
        # times = []
        # for x in xrange(5):
        basicAuth = base64.encodestring("%s:%s" % self.auth)
        authHeader = "Basic " + basicAuth.strip( )

        d = self._fetchURLs(auth=authHeader,connections=self.connections)
        d.addCallback(self._printDelta, time.time())
        yield d
            # times.append((yield d))
        # print 'avg time: %0.3fs' % (sum(times) / len(times),)
        if reactor.running:
            reactor.stop()

    def _download(self):
        # pool = HTTPConnectionPool(reactor, persistent=True)
        # pool.maxPersistentPerHost = self.connections
        self.success_count = 0
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        reactor.callWhenRunning(self._main)
        reactor.run()


    def get_count(self):
        '''
        returns number of successfully fetched urls
        '''
        return self.success_count