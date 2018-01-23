"""Spider for the kissmanga website"""

import codecs
import re
import cfscrape
import requests
from dateutil.parser import parse
from urllib.parse import urljoin
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from base64 import b64decode

from scrapy import Request
from scrapy.spiders import CrawlSpider

from bookscrape.exceptions import BookScrapeException

from ..items import BookPageItem


class KissmangaSpider(CrawlSpider):
    name = 'kissmanga'
    allowed_domains = ['kissmanga.com']

    custom_settings = {
        'REDIRECT_ENABLED': True,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 0
    }

    def __init__(self, book_slug, volume, output_dir, *args, **kwargs):
        """Init the spider with the start url

        Parameters
        ----------
        book_slug: str
            The slug of the wanted book on the "kissmanga" website
        volume: str
            The volume of the wanted book on the "kissmanga" website
        output_dir: str
            The path of the directory to place the downloaded files

        """

        super().__init__(*args, **kwargs)

        self.book_slug = book_slug
        self.volume = int(volume)
        self.output_dir = output_dir

        self.cloudflare_token = None

    def start_requests(self):
        """Solve the "Cloudflare" challenge and start the crawling"""

        try:
            self.cloudflare_token, user_agent = cfscrape.get_tokens(
                'http://kissmanga.com/',
                user_agent=self.settings.get('USER_AGENT')
            )
        except Exception:
            raise BookScrapeException(
                'Unable to bypass "cloudflare" antibot protection'
            )

        yield Request(
            url='http://kissmanga.com/Manga/%s' % self.book_slug,
            cookies=dict(
                vns_readType1='1',
                **self.cloudflare_token
            ),
            callback=self.parse_volumes_list
        )

    def parse_volumes_list(self, response):
        """Parse the volume list and try to find the asked volume"""

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
            '/Manga/%s/v?id=%d' % (self.book_slug, wanted_volume[0]),
            callback=self.parse_images
        )

    @staticmethod
    def _decode_images_path(key, obfuscated_path):
        """De-obfuscated an image path from the "kissmanga" website

        Parameters
        ----------
        key: binary
        obfuscated_path: str

        Returns
        -------
        str
            The de-obfuscated image path

        """

        iv = codecs.decode(b'a5e8e2e9c2721be0a84ad660c472c1f3', 'hex')

        sha = SHA256.new()
        sha.update(key)
        key = sha.digest()

        encoded = b64decode(obfuscated_path)

        dec = AES.new(key=key, mode=AES.MODE_CBC, IV=iv)
        result = dec.decrypt(encoded)

        return result.decode('utf-8').replace('\x10', '')

    def _get_decode_key(self, response):
        """Get the key to decode the obfuscated images"""

        try:
            # Try to find the key to decrypt the obfuscated images in the page
            key_regex = re.compile(r'\["(.+)"\]; chko')
            key = re.findall(key_regex, response.body.decode('utf-8'))[-1]
        except IndexError:
            # No success, need to parse the key from the javascript file
            javascript_response = requests.get(
                urljoin(response.url, '/Scripts/lo.js'),
                cookies=self.cloudflare_token,
                headers={
                    'user-agent': self.settings.get('USER_AGENT')
                }
            )
            key_regex = re.compile(r'\["(.+)\"]')
            key = re.findall(key_regex, javascript_response.text)[0].replace(
                '"',
                ''
            ).split(',')[21]

        decoded_key = bytes(
            key,
            'utf8'
        ).decode('unicode_escape').encode('utf-8')

        return decoded_key

    def parse_images(self, response):
        """Parse the images list of the wanted book volume"""

        key = self._get_decode_key(response)
        p = re.compile(r'\.push\(wrapKA\("(.+)"\)')
        obfuscated_image_urls = re.findall(p, response.body.decode('utf-8'))

        try:
            image_urls = [
                self._decode_images_path(key, image_path)
                for image_path in obfuscated_image_urls
            ]
        except Exception:
            raise BookScrapeException(
                'Unable to decrypt the obfuscated image paths :('
            )

        for image_url in image_urls:
            page_index = image_url.split('/')[-1].replace(
                '.jpg',
                ''
            ).replace('.png', '').replace(
                '&imgmax=25000',
                ''
            ).replace('\x08', '').replace('\x05', '').strip()

            if '-' in page_index:
                page_index = page_index.split('-')[-1]

            page_index = int(page_index)

            yield BookPageItem(
                page_index=page_index,
                volume_index=self.volume,
                image_urls=[image_url]
            )
