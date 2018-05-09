# -*- coding: utf-8 -*-

# Scrapy settings for tutorial project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'project_spider'

SPIDER_MODULES = ['project_spider.spiders']
NEWSPIDER_MODULE = ''

# Splash server address
SPLASH_URL = 'http://0.0.0.0:8050'
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'

#PROXY = """splash:on_request(function(request)
#    request:set_proxy{
#        host = http://us-wa.proxymesh.com,
#        port = 31280,
#        username = pattersoncharlesl,
#        password = KUtKehiWcRcorGgM2,
#    }
#    return splash:html()
#end)"""


# Local development database
#DATABASE = {
#    'drivername': 'postgres',
#    'host': 'localhost',
#    'port': '5432',
#    'username': 'Charlie',
#    'password': '',
#    'database': 'posts'
#}

# AWS RDS development database
DATABASE = {
    'drivername': 'postgres',
    'host': 'tigersandflies.c3rts6kx9sdz.us-east-1.rds.amazonaws.com',
    'port': '5432',
    'username': 'Charlie',
    'password': 'PkzBaDF8NstArBrRe',
    'database': 'tigersandflies'
}

# Use Delta-fetch so items are only crawled once
DELTAFETCH_ENABLED = True



# Stealth mode
#ROTATING_PROXY_LIST = [
#	'http://pattersoncharlesl:PASSWORD@us-wa.proxymesh.com:31280',
#]
# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
	'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
    'scrapy_deltafetch.DeltaFetch': 101,
#    'tutorial.middlewares.TutorialSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
	'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
    #'scrapy_crawl_once.CrawlOnceMiddleware': 50,
	#'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    #'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
	'scrapy_splash.SplashCookiesMiddleware': 723,
	'scrapy_splash.SplashMiddleware': 725,
	'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
#    'tutorial.middlewares.TutorialDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'scrapy.pipelines.files.FilesPipeline': 1,
    'project_spider.pipelines.PostsPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
