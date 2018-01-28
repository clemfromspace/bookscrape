import argparse
import os
import sys
from typing import Iterable

from scrapy import signals
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor

from bookscrape.crawl.spiders.kissmanga import KissmangaSpider
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


def crawl(book_slug: str,
          volumes: Iterable[int],
          output_dir: str,
          verbose=False):
    """Crawl the given provided book_slug, exporting the volumes
    to the provided directory

    """

    if verbose:
        configure_logging()

    runner = CrawlerRunner(
        settings={
            'IMAGES_STORE': os.path.join(output_dir, 'images'),
            **SETTINGS
        }
    )

    for volume in volumes:
        runner.crawl(
            KissmangaSpider,
            book_slug=book_slug,
            volume=volume,
            output_dir=output_dir
        )

    def error(failure, response, spider):
        if isinstance(failure.value, BookScrapeException):
            logger.error(str(failure.value))
        else:
            logger.error(failure)

    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    for crawler in list(runner.crawlers):
        crawler.signals.connect(error, signals.spider_error)

    logger.info('Crawling started for the book slug "%s"', book_slug)

    reactor.run()


def _parse_args(args):
    """Parse the given args

    Parameters
    ----------
    args: list

    """

    parser = argparse.ArgumentParser(description='Download a book.')
    parser.add_argument(
        'slug',
        metavar='slug',
        type=str,
        help='The slug of the book to download'
    )
    parser.add_argument(
        'volumes',
        metavar='volumes',
        type=int,
        nargs='+',
        help='The volume(s) of the book to download'
    )
    parser.add_argument(
        'output_dir',
        metavar='output_dir',
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
    crawl(args.slug, args.volumes, args.output_dir, args.verbose)


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
