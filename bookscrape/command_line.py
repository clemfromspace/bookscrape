import argparse
import os
import sys
from typing import Iterable

from scrapy import signals
from scrapy import spiderloader
from scrapy.settings import Settings
from scrapy.crawler import CrawlerRunner
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer

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
        'scrapy.pipelines.images.ImagesPipeline': 1,
        'bookscrape.crawl.pipelines.BookPipeline': 2
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


def crawl(provider: CrawlSpider,
          slug: str,
          volumes: Iterable[int],
          output_dir: str,
          verbose=False):
    """Crawl the given provided book identified by its slug on the spider,
    exporting the volumes to the given directory

    """

    if verbose:
        configure_logging()

    runner = CrawlerRunner(
        settings={
            'IMAGES_STORE': os.path.join(output_dir, 'images'),
            **SETTINGS
        }
    )

    @defer.inlineCallbacks
    def run_crawlers():
        for volume in volumes:
            yield runner.crawl(
                provider,
                book_slug=slug,
                volume=volume,
                output_dir=output_dir
            )

        reactor.stop()

    def error(failure, response, spider):
        if isinstance(failure.value, BookScrapeException):
            logger.error(str(failure.value))
        else:
            logger.error(failure)

    for crawler in list(runner.crawlers):
        crawler.signals.connect(error, signals.spider_error)

    logger.info(
        'Crawling started for the book slug "%s" on the "%s" provider',
        slug,
        provider.name
    )

    run_crawlers()
    reactor.run()


def _parse_args(args: list) -> argparse.ArgumentParser:
    """Parse the given args"""

    def parse_range_type(string: str) -> Iterable[int]:
        """Parse a range given as a string, ie: 10-20"""

        ranges = string.split('-')
        start = int(ranges[0])
        end = int(ranges[1]) if len(ranges) > 1 else start

        return list(range(start, end + 1))

    parser = argparse.ArgumentParser(
        description='Download the book volume(s) identified by '
                    'the slug from the given provider'
    )
    parser.add_argument(
        'provider',
        type=str,
        choices=_available_spiders().keys(),
        help='The provider to use'
    )
    parser.add_argument(
        'slug',
        type=str,
        help='The slug of the book to download'
    )
    parser.add_argument(
        'volumes',
        metavar='[volume_start-volume_end]',
        type=parse_range_type,
        help='The volume(s) of the book to download'
    )
    parser.add_argument(
        'output_dir',
        type=str,
        help='The full path of the directory to place the downloaded files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true'
    )

    return parser.parse_args(args)


def main(args=None):
    if not args:
        args = sys.argv[1:]

    args = _parse_args(args)
    crawl(
        _available_spiders()[args.provider],
        args.slug,
        args.volumes,
        args.output_dir,
        args.verbose
    )


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
