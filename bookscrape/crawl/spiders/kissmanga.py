"""Spider for the kissmanga website"""

import codecs
import re
import requests

from urllib.parse import urljoin
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from base64 import b64decode

from bookscrape.exceptions import BookScrapeException

from .kissmanga_readcomics_base import KissmangaReadcomicsBase


class KissmangaSpider(KissmangaReadcomicsBase):
    name = 'kissmanga'
    allowed_domains = ['kissmanga.com']
    url_key = 'Manga'

    @staticmethod
    def _decode_images_path(key: bin, obfuscated_path: str) -> str:
        """De-obfuscated an image path from the "kissmanga" website"""

        iv = codecs.decode(b'a5e8e2e9c2721be0a84ad660c472c1f3', 'hex')

        sha = SHA256.new()
        sha.update(key)
        key = sha.digest()

        encoded = b64decode(obfuscated_path)

        dec = AES.new(key=key, mode=AES.MODE_CBC, IV=iv)
        result = dec.decrypt(encoded)

        return result.decode('utf-8').replace('\x10', '')

    def _get_decode_key(self, response) -> bytes:
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

    def extract_images_urls(self, response):
        """Extract list of image urls from the provided response"""

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

        return image_urls
