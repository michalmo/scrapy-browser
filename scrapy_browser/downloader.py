import base64
import collections
import json
import logging
from io import BytesIO
from urllib.parse import urldefrag

from twisted.internet import defer, reactor, protocol
from twisted.web.http_headers import Headers as TxHeaders
from twisted.internet.error import TimeoutError
from twisted.web.client import Agent, HTTPConnectionPool
try:
    from twisted.web.client import URI
except ImportError:
    from twisted.web.client import _URI as URI

from scrapy.responsetypes import responsetypes
from scrapy.core.downloader.tls import openssl_methods
from scrapy.core.downloader.handlers.http11 import _RequestBodyProducer
from scrapy.utils.misc import load_object
from scrapy.utils.python import to_bytes

logger = logging.getLogger(__name__)


class BrowserDownloadHandler(object):
    def __init__(self, settings):
        self._pool = HTTPConnectionPool(reactor, persistent=True)
        self._pool.maxPersistentPerHost = settings.getint('CONCURRENT_REQUESTS_PER_DOMAIN')
        self._pool._factory.noisy = False

        self._sslMethod = openssl_methods[settings.get('DOWNLOADER_CLIENT_TLS_METHOD')]
        self._contextFactoryClass = load_object(settings['DOWNLOADER_CLIENTCONTEXTFACTORY'])
        self._contextFactory = self._contextFactoryClass(method=self._sslMethod)
        self._disconnect_timeout = 1

    def download_request(self, request, spider):
        agent = BrowserAgent(contextFactory=self._contextFactory, pool=self._pool)
        return agent.download_request(request)

    def close(self):
        d = self._pool.closeCachedConnections()
        delayed_call = reactor.callLater(self._disconnect_timeout, d.callback, [])

        def cancel_delayed_call(result):
            if delayed_call.active():
                delayed_call.cancel()
            return result

        d.addBoth(cancel_delayed_call)
        return d


class BrowserAgent(object):
    _Agent = Agent

    def __init__(self, contextFactory=None, connectTimeout=10, bindAddress=None, pool=None):
        self._contextFactory = contextFactory
        self._connectTimeout = connectTimeout
        self._bindAddress = bindAddress
        self._pool = pool
        self._txresponse = None

    def _get_agent(self, request, timeout):
        bindaddress = request.meta.get('bindaddress') or self._bindAddress
        return self._Agent(reactor, contextFactory=self._contextFactory,
                           connectTimeout=timeout, bindAddress=bindaddress, pool=self._pool)

    def download_request(self, request):
        timeout = request.meta.get('download_timeout') or self._connectTimeout

        url = urldefrag(request.url[len('browser+'):])[0]
        method = to_bytes(request.method)
        headers = TxHeaders(request.headers)

        if '_browser_stream' in request.meta:
            d = defer.Deferred()
            request.meta['_browser_stream'].await_response(d)

        else:
            agent = self._get_agent(request, timeout)
            if request.body:
                bodyproducer = _RequestBodyProducer(request.body)
            else:
                bodyproducer = _RequestBodyProducer(b'')
            d = agent.request(
                method, to_bytes(url, encoding='ascii'), headers, bodyproducer)
            d.addCallback(self._cb_bodyready, request)

        d.addCallback(self._cb_bodydone)
        self._timeout_cl = reactor.callLater(timeout, d.cancel)
        d.addBoth(self._cb_timeout, url, timeout)
        return d

    def _cb_timeout(self, result, url, timeout):
        if self._timeout_cl.active():
            self._timeout_cl.cancel()
            return result
        # needed for HTTPS requests, otherwise _ResponseReader doesn't
        # receive connectionLost()
        if self._txresponse:
            self._txresponse._transport.stopProducing()

        raise TimeoutError("Getting %s took longer than %s seconds." % (url, timeout))

    def _cb_bodyready(self, txresponse, request):
        def _cancel(_):
            # Abort connection immediately.
            txresponse._transport._producer.abortConnection()

        d = defer.Deferred(_cancel)
        reader = _ResponseReader(request)
        reader.await_response(d)
        request.meta['_browser_stream'] = reader
        txresponse.deliverBody(reader)

        # save response for timeouts
        self._txresponse = txresponse

        return d

    def _cb_bodydone(self, result):
        url, status, headers, body, flags = result
        respcls = responsetypes.from_args(headers=headers, url=url, body=body)
        return respcls(url=url, status=status, headers=headers, body=body, flags=flags)


class _ResponseReader(protocol.Protocol):
    def __init__(self, request):
        self._request = request
        self._bodybuf = BytesIO()
        self._bytes_received = 0
        self._closed = False
        self._messages = collections.deque()
        self._awaiting = collections.deque()

    def dataReceived(self, bodyBytes):
        parts = bodyBytes.split(b'\n\n')
        for part in parts[:-1]:
            self._bodybuf.write(part)
            self._messages.append(self._bodybuf.getvalue())
            self._bodybuf.truncate(0)
        self._bodybuf.write(parts[-1])
        self._bytes_received += len(bodyBytes)
        self.resolve_responses()

    def connectionLost(self, reason):
        self._closed = True
        self.resolve_responses()

    def await_response(self, d):
        self._awaiting.append(d)
        self.resolve_responses()

    def resolve_responses(self):
        while self._messages and self._awaiting:
            d, message = self._awaiting.popleft(), self._messages.popleft()
            response = self.extract_response(message)
            d.callback((
                response['url'],
                response['status'],
                response['headers'],
                response['body'],
                ['still_running']
                if self._messages or not self._closed
                else None,
            ))

        if self._closed:
            while self._awaiting:
                d = self._awaiting.popleft()
                d.callback((
                    self._request.url,
                    204,
                    {},
                    b'',
                    ['no_more_content'],
                ))

    @staticmethod
    def extract_response(message):
        _, data_line = message.decode().split('\n', 1)
        _, json_data = data_line.split(': ', 1)
        data = json.loads(json_data)
        return {
            **data,
            'body': base64.decodebytes(data['body'].encode('ascii')),
        }
