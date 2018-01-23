"""Spider for the kissmanga website"""

import codecs
import re
import cfscrape
from dateutil.parser import parse
from urllib.parse import urljoin
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from base64 import b64decode

from scrapy import Request
from scrapy.spiders import CrawlSpider

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

    def start_requests(self):
        """Solve the "Cloudflare" challenge and start the crawling"""

        tokens, user_agent = cfscrape.get_tokens(
            'http://kissmanga.com/',
            user_agent=self.settings.get('USER_AGENT')
        )

        yield Request(
            url='http://kissmanga.com/Manga/%s' % self.book_slug,
            cookies=tokens
        )

    def parse(self, response):
        """Parse the volume list and try to find the asked volume"""

        volumes = response.xpath('//table[@class="listing"]//tr[position()>2]')

        ordered_volumes = []

        for index, volume in enumerate(volumes):
            volume_id = int(
                volume.xpath('./td[1]/a/@href').extract()[0].split('id=')[-1]
            )
            volume_date = parse(volume.xpath('./td[2]/text()').extract()[0])
            ordered_volumes.append((volume_id, volume_date, index,))

        ordered_volumes = sorted(
            ordered_volumes,
            key=lambda tup: tup[2],
            reverse=True
        )
        ordered_volumes = sorted(ordered_volumes, key=lambda tup: tup[1])
        wanted_volume = ordered_volumes[self.volume-1]

        yield Request(
            urljoin(
                response.url,
                '/Manga/%s/v?id=%d' % (self.book_slug, wanted_volume[0])
            ),
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

        See Also
        --------
        https://gist.github.com/nhanb/74542c36d3dcc5dde4e90b34437fb523

        """

        iv = codecs.decode(b'a5e8e2e9c2721be0a84ad660c472c1f3', 'hex')

        sha = SHA256.new()
        sha.update(key)
        key = sha.digest()

        encoded = b64decode(obfuscated_path)

        dec = AES.new(key=key, mode=AES.MODE_CBC, IV=iv)
        result = dec.decrypt(encoded)

        return result.decode('utf-8').replace('\x10', '')

    def parse_images(self, response):
        """Parse the images list of the wanted book volume"""

        key_regex = re.compile(r'\["(.+)"\]; chko')
        key = re.findall(key_regex, response.body.decode('utf-8'))[1]
        key = bytes(key, 'utf8').decode('unicode_escape').encode('utf-8')

        p = re.compile(r'\.push\(wrapKA\("(.+)"\)')
        obfuscated_image_urls = re.findall(p, response.body.decode('utf-8'))

        image_urls = [
            self._decode_images_path(key, image_path)
            for image_path in obfuscated_image_urls
        ]

        for image_url in image_urls:
            page_index = image_url.split('/')[-1].replace(
                '.jpg',
                ''
            ).replace('.png', '')

            if '-' in page_index:
                page_index = page_index.split('-')[-1]

            page_index = int(page_index)

            yield BookPageItem(
                page_index=page_index,
                volume_index=self.volume,
                image_urls=[image_url]
            )
