"""This module contains the spider for the """

import re

from ..items import BookPageItem

from .kissmanga_readcomics_base import KissmangaReadcomicsBase


class ReadcomiconlineSpider(KissmangaReadcomicsBase):
    name = 'readcomiconline'
    allowed_domains = ['readcomiconline.to']
    url_key = 'Comic'

    def parse_images(self, response):
        """Parse the images list of the wanted book volume"""

        p = re.compile(r'\.push\("(.+)"\)')
        image_urls = re.findall(p, response.body.decode('utf-8'))

        for image_url in image_urls:
            page_index = self._get_page_index(image_url)

            yield BookPageItem(
                page_index=page_index,
                volume_index=self.volume,
                image_urls=[image_url]
            )

    def extract_images_urls(self, response):
        """Extract list of image urls from the provided response"""

        p = re.compile(r'\.push\("(.+)"\)')
        image_urls = re.findall(p, response.body.decode('utf-8'))

        return image_urls
