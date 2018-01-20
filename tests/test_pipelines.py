"""this module contains the tests for the pipelines of the ``bookscrape`` package"""

import os
import unittest
from unittest import mock

from bookscrape.crawl.pipelines import BookPipeline


class BookPipelineTestCase(unittest.TestCase):
    """Test case for the ``BookPipeline`` of the ``bookscrape`` package"""

    document_path = os.path.join(os.path.dirname(__file__), 'files')

    def test_open_spider_should_call_start_exporting(self):
        """Test that the ``open_spider`` method should start the export process"""

        pipeline = BookPipeline(images_path=self.document_path)
        spider = mock.MagicMock()
        spider.output_dir = self.document_path

        with mock.patch('bookscrape.crawl.exporters.PdfExporter.start_exporting') as mocked:
            pipeline.open_spider(spider)

        mocked.assert_called()

    def test_close_spider_should_call_finish_exporting(self):
        """Test that the ``close_spider`` method should finish the export process"""

        pipeline = BookPipeline(images_path=self.document_path)
        spider = mock.MagicMock()
        spider.output_dir = self.document_path

        pipeline.open_spider(spider)

        with mock.patch('bookscrape.crawl.exporters.PdfExporter.finish_exporting') as mocked:
            pipeline.close_spider(spider)

        mocked.assert_called()
