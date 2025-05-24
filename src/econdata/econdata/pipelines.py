import psycopg2
from itemadapter import ItemAdapter

class PostgresPipeline:
    def __init__(self):
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        """Properly initialize the pipeline with crawler access"""
        pipeline = cls()
        pipeline.crawler = crawler  # Required for settings access
        return pipeline

    def open_spider(self, spider):
        """Connect to PostgreSQL when spider starts"""
        self.connection = psycopg2.connect(
            host=self.crawler.settings.get('DB_HOST', 'localhost'),
            port=self.crawler.settings.get('DB_PORT', 5432),
            database=self.crawler.settings.get('DB_NAME'),
            user=self.crawler.settings.get('DB_USER'),
            password=self.crawler.settings.get('DB_PASSWORD')
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        """Close database connection when spider closes"""
        if self.connection:
            self.connection.close()

    def process_item(self, item, spider):
        """Insert item into database"""
        insert_query = """
        INSERT INTO exchange_rates (
            base_currency,
            target_currency,
            exchange_rate,
            last_updated_unix,
            last_updated_utc
        ) VALUES (
            %s, %s, %s, %s, %s
        ) ON CONFLICT DO NOTHING;
        """
        data = (
            item['base_currency'],
            item['target_currency'],
            item['exchange_rate'],
            item['last_updated_unix'],
            item['last_updated_utc']
        )
        self.cursor.execute(insert_query, data)
        self.connection.commit()
        return item