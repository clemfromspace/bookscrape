import argparse

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from crawl.spiders.kissmanga import KissmangaSpider


def crawl(book_slug, volumes, output_dir):

    configure_logging()

    runner = CrawlerRunner(settings=get_project_settings())

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


def main():
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
        '--output_dir',
        metavar='output_dir',
        type=str,
        help='The full path of the directory to place the downloaded files'
    )

    args = parser.parse_args()

    crawl(args.slug, args.volumes, args.output_dir)


if __name__ == "__main__":
    # execute only if run as a script
    main()
