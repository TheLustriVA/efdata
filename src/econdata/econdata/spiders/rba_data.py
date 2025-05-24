import scrapy
from pathlib import Path
import os

class RBASpider(scrapy.Spider):
    name = "rba_tables"
    start_urls = [
        "https://www.rba.gov.au/statistics/tables/"
    ]

    def parse(self, response):
        # Extract all CSV file URLs
        csv_urls = response.xpath("//a[contains(@href, '.csv')]/@href").getall()

        for csv_url in csv_urls:
            # Create an absolute URL
            absolute_url = response.urljoin(csv_url)
            # Create a request for each CSV file
            yield scrapy.Request(url=absolute_url, callback=self.save_csv)

    def save_csv(self, response):
        # Extract the file name from the URL
        file_name = os.path.basename(response.url)
        # Define the path to save the file
        save_path = Path(f"downloads/{file_name}")
        # Ensure the downloads directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # Save the content of the response to a file
        save_path.write_bytes(response.body)
        self.log(f"Saved file {file_name}")