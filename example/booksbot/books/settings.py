BOT_NAME = 'books'

SPIDER_MODULES = ['books.spiders']
NEWSPIDER_MODULE = 'books.spiders'

DOWNLOADER_MIDDLEWARES = {
    'scrapy_browser.middlewares.BrowserDownloaderMiddleware': 200,
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': None,
}

SPIDER_MIDDLEWARES = {
    'scrapy_browser.middlewares.BrowserSpiderMiddleware': 1,
}

DOWNLOAD_HANDLERS = {
    'browser+http': 'scrapy_browser.downloader.BrowserDownloadHandler',
    'browser+https': 'scrapy_browser.downloader.BrowserDownloadHandler',
}
