"""This module contains the base spider for kissmanga and readcomics"""

from dateutil.parser import parse

from scrapy import Request

from bookscrape.exceptions import BookScrapeException

from ..items import BookPageItem

from .bases import BookSpider, CloudFlareSpider


class KissmangaReadcomicsBase(CloudFlareSpider, BookSpider):
    """Base spider class for the ``kissmanga`` and ``readcomics`` websites"""

    def start_requests(self):
        """Start the first request (the volume listing)"""

        super().start_requests()

        yield Request(
            url='http://%s/%s/%s' % (
                self.allowed_domains[0],
                self.url_key,
                self.book_slug
            ),
            cookies=dict(
                vns_readType1='1',  # All images on one page
                **self.cloudflare_token
            ),
            callback=self.parse_volumes_list
        )

    def _get_volumes_list(self, response):
        """Get the volumes list"""

        volumes = response.xpath('//table[@class="listing"]//tr[position()>2]')

        if not len(volumes):
            raise BookScrapeException(
                'No volumes found for the "%s" slug' % self.book_slug
            )

        ordered_volumes = []

        for index, volume in enumerate(volumes):
            volume_id = int(
                volume.xpath(
                    './td[1]/a/@href'
                ).extract_first().split('id=')[-1]
            )
            volume_date = parse(volume.xpath('./td[2]/text()').extract_first())
            ordered_volumes.append((volume_id, volume_date, index,))

        ordered_volumes.reverse()

        return ordered_volumes

    def parse_volumes_list(self, response):
        """Parse the volume list and try to find the asked volume"""

        ordered_volumes = self._get_volumes_list(response)

        try:
            wanted_volume = ordered_volumes[self.volume-1]
        except IndexError:
            raise BookScrapeException(
                'The %d volume was not found for the "%s" slug' % (
                    self.volume,
                    self.book_slug
                )
            )

        yield response.follow(
            '/%s/%s/v?id=%d' % (
                self.url_key,
                self.book_slug,
                wanted_volume[0]
            ),
            callback=self.export_images
        )

    def _get_page_index(self, image_url: str) -> int:
        """Get the index of the page from a given image_url"""

        page_index = image_url.split('/')[-1].replace(
            '.jpg',
            ''
        ).replace('.png', '').replace(
            '&imgmax=25000',
            ''
        ).replace('\x08', '').replace(
            '\x05',
            ''
        ).replace(
            'RCO',
            ''
        ).strip()

        if '-' in page_index:
            page_index = page_index.split('-')[-1]

        return page_index

    def export_images(self, response):
        """Export the extracted images"""

        for image_url in self.extract_images_urls(response):
            page_index = self._get_page_index(image_url)

            yield BookPageItem(
                page_index=page_index,
                volume_index=self.volume,
                image_urls=[image_url]
            )
