import itertools
import json
import logging

from scrapy.exceptions import IgnoreRequest
from scrapy.http.headers import Headers
from six.moves.urllib.parse import urljoin


logger = logging.getLogger(__name__)


class BrowserDownloaderMiddleware(object):
    default_adapter_url = 'http://127.0.0.1:8050'
    default_endpoint = "render.json"

    def __init__(self, crawler, browser_adapter_url):
        self.crawler = crawler
        self.browser_adapter_url = browser_adapter_url

    @classmethod
    def from_crawler(cls, crawler):
        browser_adapter_url = crawler.settings.get(
            'BROWSER_ADAPTER_URL',
            cls.default_adapter_url,
        )
        return cls(crawler, browser_adapter_url)

    def process_request(self, request, spider):
        if (
            'browser' not in request.meta or
            request.meta.get('_browser_processed')
        ):
            return

        request.meta['_browser_processed'] = True
        browser_options = request.meta['browser']

        endpoint = browser_options.setdefault(
            'endpoint',
            self.default_endpoint,
        )
        browser_base_url = browser_options.get(
            'browser_url',
            self.browser_adapter_url,
        )
        browser_url = urljoin(browser_base_url, endpoint)

        args = browser_options.setdefault('args', {})
        args.setdefault('url', request.url)

        return request.replace(
            url='browser+' + browser_url,
            method='POST',
            body=json.dumps(
                args,
                ensure_ascii=False,
                sort_keys=True,
            ),
            headers=Headers({
                'Content-Type': 'application/json',
            }),
        )

    def process_response(self, request, response, spider):
        if (
            request.meta.get('browser') and
            'no_more_content' in response.flags
        ):
            raise IgnoreRequest()

        return response


class BrowserSpiderMiddleware(object):
    def process_spider_output(self, response, result, spider):
        if (
            response.request and
            response.request.meta.get('browser') and
            'still_running' in response.flags
        ):
            request = response.request
            request.dont_filter = True
            return itertools.chain(result, [request])
        return result
