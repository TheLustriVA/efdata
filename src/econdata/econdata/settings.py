# Scrapy settings for econdata project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "econdata"

SPIDER_MODULES = ["econdata.spiders"]
NEWSPIDER_MODULE = "econdata.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 4

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "econdata.middlewares.EcondataSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "econdata.middlewares.EcondataDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "econdata.pipelines.EcondataPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
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
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

import os
from dotenv import load_dotenv

load_dotenv('/home/websinthe/code/econcell/.env')


# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

XR_API_KEY = os.getenv("XR_API_KEY")
XR_BASE_CURRENCY = 'AUD'  # Or any other supported ISO code

# Database settings
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_USER = os.getenv("PSQL_USER")
DB_PASSWORD = os.getenv("PSQL_PW")

# Pipeline configuration - use __init__ for legacy pipelines to avoid package/module conflict
ITEM_PIPELINES = {
    'econdata.pipelines_module.PostgresPipeline': 300,
    'econdata.pipelines_enhanced.EnhancedRBACircularFlowPipeline': 400,
    # ABS Taxation pipelines
    'econdata.pipelines.abs_taxation_pipeline.ABSTaxationValidationPipeline': 250,
    'econdata.pipelines.abs_taxation_pipeline.ABSTaxationEnrichmentPipeline': 350,
    'econdata.pipelines.abs_taxation_pipeline.ABSTaxationPipeline': 450,
    # ABS Expenditure pipeline
    'econdata.pipelines.abs_expenditure_pipeline.ABSExpenditurePipeline': 460,
}

# Other settings (keep as before)
DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS = 16

# ABS-specific settings for large file downloads
DOWNLOAD_TIMEOUT = 180  # 3 minutes default, spiders can override
DOWNLOAD_MAXSIZE = 100 * 1024 * 1024  # 100MB max file size
DOWNLOAD_WARNSIZE = 50 * 1024 * 1024  # Warn at 50MB

# Retry configuration for ABS downloads
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# File download settings
FILES_STORE = 'downloads/'
FILES_EXPIRES = 30  # Keep downloaded files for 30 days

# Enable pandas for Excel file processing
PANDAS_ENABLED = True