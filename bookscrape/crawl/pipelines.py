"""This module contains the pipelines for the ``pybook`` package"""

from bookscrape.crawl.exporters import PdfExporter


class BookPipeline:
    def __init__(self, images_path):
        # Storing output folder of the images
        self.images_path = images_path

    @classmethod
    def from_crawler(cls, crawler):
        # getting the value of IMAGES_STORE field from settings.py
        images_path = crawler.settings.get('IMAGES_STORE')

        return cls(images_path)

    def open_spider(self, spider):
        self.exporter = PdfExporter(
            spider.output_dir,
            self.images_path,
            '%s_%d' % (spider.book_slug, spider.volume,)
        )
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
