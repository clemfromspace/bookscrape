"""This module contains the exporters for the ``pybook`` package"""

import os

from scrapy.exporters import BaseItemExporter

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.lib.units import inch


class PdfExporter(BaseItemExporter):
    """Exporter to export the crawled items images as a pdf file"""

    IMAGE_WIDTH = 7 * inch
    IMAGE_HEIGHT = 9.5 * inch

    output_dir = None
    images_path = None
    file_name = None
    document = None
    story = None

    def __init__(self, output_dir, images_path, file_name, **kwargs):
        self._configure(kwargs, dont_fail=True)

        self.output_dir = output_dir
        self.images_path = images_path
        self.file_name = file_name

        filename = os.path.join(
            output_dir,
            self.file_name + '.pdf'
        )
        self.document = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        self.story = list()

    def finish_exporting(self):
        self.document.build(self.story)

    def export_item(self, item):
        self.story.append(
            Image(
                os.path.join(
                    self.images_path,
                    item['images'][0]['path']
                ),
                self.IMAGE_WIDTH,
                self.IMAGE_HEIGHT
            )
        )
        self.story.append(PageBreak())
