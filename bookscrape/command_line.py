import os

import click
from scrapy import signals
from scrapy import spiderloader
from scrapy.settings import Settings
from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer

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

    def __init__(self,
                 provider: CrawlSpider,
                 slug: str,
                 volumes: range,
                 output_dir: str,
                 verbose=False):

        self.provider = provider
        self.slug = slug
        self.volumes = list(volumes)
        self.output_dir = output_dir
        self.verbose = verbose

        if verbose:
            configure_logging()

        self.runner = CrawlerRunner()
        self.exporter = PdfExporter(
            output_dir,
            os.path.join(output_dir, 'images'),
            file_name='%s_%s.pdf' % (
                slug,
                '-'.join([str(volumes.start), str(volumes.stop - 1)])
            )
        )

    def run(self):
        logger.info(
            'Crawling started for the book slug "%s" on the "%s" provider.',
            self.slug,
            self.provider.name
        )
        self.crawl()
        reactor.run()

    @staticmethod
    def _on_error(failure):
        if isinstance(failure.value, BookScrapeException):
            logger.error(str(failure.value))
        else:
            logger.error(failure)

    def _get_crawler(self):
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
    def crawl(self):
        with click.progressbar(self.volumes) as bar:
            for volume in bar:
                yield self.runner.crawl(
                    self._get_crawler(),
                    book_slug=self.slug,
                    volume=volume,
                    output_dir=self.output_dir
                )

        reactor.stop()
        self.exporter.finish_exporting()


class RangeParamType(click.ParamType):
    name = 'range'

    def convert(self, value, param, ctx):
        try:
            ranges = value.split('-')
            start = int(ranges[0])
            end = int(ranges[1]) if len(ranges) > 1 else start
            return range(start, end + 1)
        except ValueError:
            self.fail('%s is not a valid range' % value, param, ctx)

RANGE = RangeParamType()


@click.command()
@click.argument('provider', type=click.Choice(_available_spiders().keys()))
@click.argument('book_slug')
@click.argument('volumes', type=RANGE)
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True)
def main(provider, book_slug, volumes, output_dir, verbose):
    BookCrawler(
        _available_spiders()[provider],
        book_slug,
        volumes,
        output_dir,
        verbose
    ).run()


if __name__ == "__main__":
    main()
