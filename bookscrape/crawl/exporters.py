"""This module contains the exporters for the ``pybook`` package"""

import os
from operator import itemgetter

from scrapy.exporters import BaseItemExporter

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.lib.units import inch

from bookscrape.exceptions import BookScrapeException
from bookscrape.loggers import logger


class PdfExporter(BaseItemExporter):
    """Exporter to export the crawled items images as a pdf file"""

    IMAGE_WIDTH = 7 * inch
    IMAGE_HEIGHT = 9.5 * inch

    output_dir = None
    images_path = None
    file_name = None
    images = None

    def __init__(self, output_dir, images_path, file_name, **kwargs):
        self._configure(kwargs, dont_fail=True)

        self.output_dir = output_dir
        self.images_path = images_path
        self.file_name = file_name
        self.images = list()

    def _clean_images(self):
        # Remove the downloaded images
        for image in self.images:
            try:
                os.remove(image[2])
            except FileNotFoundError:
                pass

    def _get_document(self) -> SimpleDocTemplate:
        return SimpleDocTemplate(
            os.path.join(
                self.output_dir,
                self.file_name
            ),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

    def finish_exporting(self):
        """Build the document and clean the downloaded images"""

        if not self.images:  # No images were found :(
            raise BookScrapeException('Found no images to export :(')

        document = self._get_document()
        story = list()

        for image in sorted(self.images, key=itemgetter(0, 1)):
            story.append(
                Image(
                    image[2],
                    self.IMAGE_WIDTH,
                    self.IMAGE_HEIGHT
                )
            )
            story.append(PageBreak())

        document.build(story)
        self._clean_images()

        logger.info(
            'Pdf document for the book slug "%s" (%d pages) available: %s' % (
                self.file_name.split('_')[0],
                len(self.images),
                document.filename
            )
        )

    def export_item(self, item):
        image_path = os.path.join(
            self.images_path,
            item['images'][0]['path']
        )
        self.images.append(
            (item['volume_index'], item['page_index'], image_path,)
        )
