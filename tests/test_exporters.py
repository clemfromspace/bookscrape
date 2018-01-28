"""this module contains the tests for the exporters of the ``bookscrape`` package"""

import os
import unittest
from unittest import mock

from bookscrape.crawl.exporters import PdfExporter
from bookscrape.exceptions import BookScrapeException


class TestPdfExporter(unittest.TestCase):
    """Test case for the ``PdfExporter`` of the ``bookscrape`` package"""

    document_name = 'test'
    document_path = os.path.join(os.path.dirname(__file__), 'files')

    def test_finish_exporting_method_should_raise_if_no_images(self):
        """Test that the ``finish_exporting`` method should raise if no images"""

        # Initialize a new exporter
        pdf_exporter = PdfExporter(
            output_dir=self.document_path,
            images_path=self.document_path,
            file_name='test'
        )

        pdf_exporter.images = list()

        with self.assertRaises(BookScrapeException):
            pdf_exporter.finish_exporting()

    def test_finish_exporting_method_should_build_the_document(self):
        """Test that the ``finish_exporting`` method should build the document"""

        # Initialize a new exporter
        pdf_exporter = PdfExporter(
            output_dir=self.document_path,
            images_path=self.document_path,
            file_name='test'
        )

        # We need to add at least one item
        pdf_exporter.export_item(
            {
                'images': [
                    {
                        'path': 'test.png'
                    }
                ],
                'page_index': 0
            }
        )

        # We need to add at least one image
        pdf_exporter.images.append(
            (
                0,
                os.path.join(
                    self.document_path,
                    'test.png'
                ),
            )
        )

        with mock.patch('reportlab.platypus.SimpleDocTemplate.build') as mocked:
            pdf_exporter.finish_exporting()

        mocked.assert_called()

    def test_export_item_should_add_the_image_to_the_story(self):
        """Test that the ``export_item`` method should add a page item to the story"""

        # Initialize a new exporter
        pdf_exporter = PdfExporter(
            output_dir=self.document_path,
            images_path=self.document_path,
            file_name='test'
        )

        # At first, the images should be empty
        self.assertEqual(len(pdf_exporter.images), 0)

        pdf_exporter.export_item(
            {
                'page_index': 0,
                'images': [
                    {
                        'path': 'truc.png'
                    }
                ]
            }
        )

        # Now the images contains one element
        self.assertEqual(len(pdf_exporter.images), 1)
