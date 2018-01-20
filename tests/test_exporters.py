"""this module contains the tests for the exporters of the ``bookscrape`` package"""

import os
import unittest
from unittest import mock

from bookscrape.crawl.exporters import PdfExporter


class TestPdfExporter(unittest.TestCase):
    """Test case for the ``PdfExporter`` of the ``bookscrape`` package"""

    document_name = 'test'
    document_path = os.path.join(os.path.dirname(__file__), 'files')

    def test_finish_exporting_method_should_build_the_document(self):
        """Test that the ``finish_exporting`` method should build the document"""

        # Initialize a new exporter
        pdf_exporter = PdfExporter(
            output_dir=self.document_path,
            images_path=None,
            file_name='test'
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

        # At first, the story should be empty
        self.assertEqual(len(pdf_exporter.story), 0)

        pdf_exporter.export_item({
            'images': [
                {
                    'path': 'truc.png'
                }
            ]
        })

        # Now the story contains two element (the image + a page break)
        self.assertEqual(len(pdf_exporter.story), 2)
