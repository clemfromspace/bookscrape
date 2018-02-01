import os

import click
import cfscrape
from lxml.html import document_fromstring
from scrapy import signals
from scrapy import spiderloader
from scrapy.settings import Settings
from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from typing import Iterable

from bookscrape.crawl.exporters import PdfExporter
from bookscrape.exceptions import BookScrapeException
from bookscrape.loggers import logger


SETTINGS = {
    'BOT_NAME': 'bookscrape',
    'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) '
                  'Gecko/20100101 Firefox/10.0',
    'ROBOTSTXT_OBEY': False,
    'CONCURRENT_REQUESTS': 5,
    'COOKIES_ENABLED': False,
    'RETRY_TIMES': 4,
    'ITEM_PIPELINES': {
        'scrapy.pipelines.images.ImagesPipeline': 1
    },
    'REDIRECT_ENABLED': True
}


def _available_spiders() -> dict:
    """Get the spiders list of the current project"""

    settings = Settings()
    settings.setmodule('bookscrape.crawl.settings')

    spider_loader = spiderloader.SpiderLoader.from_settings(settings)
    spiders = spider_loader.list()

    return {
        name: spider_loader.load(name)
        for name in spiders
    }


class BookCrawler:
    """Crawl the provided book, exporting the crawled images"""

    exporter = None

    def __init__(self, provider: CrawlSpider, slug: str, output_dir: str, verbose=False):

        self.provider = provider
        self.slug = slug
        self.output_dir = output_dir
        self.verbose = verbose

        if verbose:
            configure_logging()

        self.runner = CrawlerRunner()

    def get_volumes_links(self) -> Iterable[str]:
        """Get the available list of volumes links for the wanted book slug"""

        scraper = cfscrape.create_scraper()
        book_url = (
            f'http://{self.provider.allowed_domains[0]}/'
            f'{self.provider.url_key}/{self.slug}'
        )

        response = scraper.get(book_url)
        document = document_fromstring(response.text)
        volume_elements = document.xpath('//table[@class="listing"]//tr[position()>2]')

        if not volume_elements:
            raise BookScrapeException('No volumes found for the "%s" slug' % self.slug)

        volumes = []

        for index, volume_element in enumerate(volume_elements):
            volume_link = volume_element.xpath(
                './td[1]/a/@href'
            )[0]
            volumes.append(volume_link)

        volumes.reverse()

        return volumes

    def run(self, volume_start: int, volume_end: int):
        self.exporter = PdfExporter(
            self.output_dir,
            os.path.join(self.output_dir, 'images'),
            file_name='%s_%s.pdf' % (
                self.slug,
                '-'.join([str(volume_start), str(volume_end)])
            )
        )
        logger.info(
            'Crawling started for the book slug "%s" on the "%s" provider.',
            self.slug,
            self.provider.name
        )

        volumes_list = list(range(volume_start, volume_end + 1))
        self.crawl(volumes_list)
        reactor.run()

    @staticmethod
    def _on_error(failure):
        if isinstance(failure.value, BookScrapeException):
            logger.error(str(failure.value))
        else:
            logger.error(failure)

    def _get_crawler(self) -> Crawler:
        crawler = Crawler(self.provider, settings={
            'IMAGES_STORE': os.path.join(self.output_dir, 'images'),
            **SETTINGS
        })
        crawler.signals.connect(
            self._on_error,
            signals.spider_error
        )
        crawler.signals.connect(
            self.exporter.export_item,
            signals.item_scraped
        )

        return crawler

    @defer.inlineCallbacks
    def crawl(self, volumes: Iterable[int]):
        yield self.runner.crawl(
            self._get_crawler(),
            book_slug=self.slug,
            volumes=volumes
        )

        reactor.stop()
        self.exporter.finish_exporting()


@click.command()
@click.argument('provider', type=click.Choice(_available_spiders().keys()))
@click.argument('book_slug')
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True)
def main(provider, book_slug, output_dir, verbose):
    book_crawler = BookCrawler(
        _available_spiders()[provider],
        book_slug,
        output_dir,
        verbose
    )

    click.echo(f'Fetching the available volumes for the "{book_crawler.slug}" book...')

    try:
        volumes_list = book_crawler.get_volumes_links()
    except BookScrapeException:
        raise click.ClickException(
            f'Failed to parse the volumes list '
            f'for the "{book_crawler.slug}" book.'
            f' Is the slug correct ?',
        )

    click.echo(f'{len(volumes_list)} volume(s) available for the "{book_crawler.slug}" book')

    volumes_start = click.prompt('Starting volume ?', type=int)
    volumes_end = click.prompt('Ending volume ?', type=int)

    book_crawler.run(volumes_start, volumes_end)


if __name__ == "__main__":
    main()
