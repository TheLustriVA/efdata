import scrapy

class XrapiCurrenciesSpider(scrapy.Spider):
    name = 'xrapi-currencies'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # Get settings via crawler to ensure they're properly initialized
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.api_key = crawler.settings.get('XR_API_KEY')
        spider.base_currency = crawler.settings.get('XR_BASE_CURRENCY', 'AUD')
        spider.start_urls = [
            f'https://v6.exchangerate-api.com/v6/{spider.api_key}/latest/{spider.base_currency}'
        ]
        return spider

    def parse(self, response):
        data = response.json()
        
        if data.get('result') == 'success':
            base = data['base_code']
            last_updated_unix = data['time_last_update_unix']
            last_updated_utc = data['time_last_update_utc']
            conversion_rates = data['conversion_rates']

            for target_currency, rate in conversion_rates.items():
                yield {
                    'base_currency': base,
                    'target_currency': target_currency,
                    'exchange_rate': rate,
                    'last_updated_unix': last_updated_unix,
                    'last_updated_utc': last_updated_utc
                }

        else:
            error_type = data.get('error-type', 'unknown')
            self.logger.error(
                f"API Error ({error_type}): {response.url} - {data.get('message', '')}"
            )