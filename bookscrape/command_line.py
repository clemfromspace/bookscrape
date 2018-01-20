import argparse
import os
import sys

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

from bookscrape.crawl.spiders.kissmanga import KissmangaSpider


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


def crawl(book_slug, volumes, output_dir):

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

    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()


def parse_args(args):
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

    return parser.parse_args(args)


def main(args=None):
    if not args:
        args = sys.argv[1:]

    args = parse_args(args)
    crawl(args.slug, args.volumes, args.output_dir)


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
