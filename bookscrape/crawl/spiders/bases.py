"""This module contains the base spider classes"""

import cfscrape

from scrapy import spiders

from bookscrape.exceptions import BookScrapeException


class CloudFlareSpider(spiders.CrawlSpider):
    """Base spider for the websites with the ``CloudFlare`` protection"""

    custom_settings = {
        'REDIRECT_ENABLED': True,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 0
    }
    cloudflare_token = None

    def start_requests(self):
        """Solve the "Cloudflare" challenge and start the crawling"""

        try:
            self.cloudflare_token, user_agent = cfscrape.get_tokens(
                'http://%s/' % self.allowed_domains[0],
                user_agent=self.settings.get('USER_AGENT')
            )
        except Exception:
            raise BookScrapeException(
                'Unable to bypass "cloudflare" antibot protection'
            )


class BookSpider(spiders.CrawlSpider):
    """Base class for all the spiders outputting a ``BookPageItem``"""

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
