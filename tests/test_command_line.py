"""this module contains the tests for the command line of the ``bookscrape`` package"""

import unittest
from unittest import mock

from click.testing import CliRunner

from bookscrape.command_line import _available_spiders, BookCrawler, main
from bookscrape.crawl.spiders.kissmanga import KissmangaSpider
from bookscrape.crawl.spiders.readcomiconline import ReadcomiconlineSpider


class TestCommandLine(unittest.TestCase):
    """Test case for the command line of the ``bookscrape`` package"""

    @classmethod
    def setUpClass(cls):

        super().setUpClass()

        cls.runner = CliRunner()

    def test__available_spiders_should_return_the_list_of_available_spiders(self):
        """Test that the ``_get_available_spiders`` should return the list of available spiders"""

        available_spiders = {
            'kissmanga': KissmangaSpider,
            'readcomiconline': ReadcomiconlineSpider
        }

        self.assertCountEqual(
            _available_spiders(),
            available_spiders
        )

    def test_main_should_raise_if_wrong_arguments_given(self):
        """Test that the ``main`` method should raise if wrong arguments were given"""

        # This should raise when no arguments are passed
        result = self.runner.invoke(main, [])

        # This should raise when mandatory arguments are missing
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(
            result.output,
            'Usage: main [OPTIONS] PROVIDER BOOK_SLUG VOLUMES OUTPUT_DIR\n'
            '\n'
            'Error: Missing argument "provider".  Choose from kissmanga, readcomiconline.\n'
        )

    def test_main_should_call_the_crawl_command(self):
        """Test that the ``main`` method should call the ``crawl`` method with the corrects args"""

        # With only one volume
        with mock.patch.object(BookCrawler, '__init__') as mocked:
            self.runner.invoke(main, ['kissmanga', 'Akira', '1', '/'])
        mocked.assert_called_with(KissmangaSpider, 'Akira', range(1, 2), '/', False)

        # With two volumes
        with mock.patch.object(BookCrawler, '__init__') as mocked:
            self.runner.invoke(main, ['kissmanga', 'Akira', '1-2', '/'])
        mocked.assert_called_with(KissmangaSpider, 'Akira', range(1, 3), '/', False)

    @mock.patch('twisted.internet.reactor.run')
    @mock.patch.object(BookCrawler, '_get_crawler', return_value=None)
    def test_crawl_should_call_the_crawl_method_on_the_crawler_runner(self, mocked_crawler, mocked_run):
        """Test that the ``crawl`` method should call the ``CrawlerRunner.crawl``"""

        bookcrawler = BookCrawler(KissmangaSpider, 'Akira', range(1, 2), '/')

        with mock.patch('scrapy.crawler.CrawlerRunner.crawl') as mocked_crawl:
            bookcrawler.run()

        # The crawl method should be called
        mocked_crawl.assert_called_once_with(
            bookcrawler._get_crawler(),
            book_slug='Akira',
            volume=1,
            output_dir='/'
        )

        # The twisted reactor should be launched
        mocked_run.assert_called_once_with()

        bookcrawler = BookCrawler(KissmangaSpider, 'Akira', range(1, 3), '/')

        # If we want to get two volumes, the crawl method should be called twice
        with mock.patch('scrapy.crawler.CrawlerRunner.crawl') as mocked_crawl:
            bookcrawler.run()

        calls = [
            mock.call(
                bookcrawler._get_crawler(),
                book_slug='Akira',
                volume=i,
                output_dir='/'
            )
            for i in range(1, 3)
        ]

        mocked_crawl.assert_has_calls(calls)
