import copy

from scrapy.http import Request
from scrapy.utils.python import to_native_str


class BrowserRequest(Request):
    def __init__(self,
                 url=None,
                 callback=None,
                 method='GET',
                 script=None,
                 args=None,
                 meta=None,
                 **kwargs):

        if url is None:
            url = 'about:blank'
        url = to_native_str(url)

        meta = copy.deepcopy(meta) or {}
        browser_meta = meta.setdefault('browser', {})

        _args = {
            'url': url,  # put URL to args in order to preserve #fragment
            'script': script if isinstance(script, list) else [],
        }
        _args.update(args or {})
        _args.update(browser_meta.get('args', {}))
        browser_meta['args'] = _args

        super(BrowserRequest, self).__init__(
            url,
            callback,
            method,
            meta=meta,
            **kwargs,
        )
