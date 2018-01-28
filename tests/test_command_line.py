"""this module contains the tests for the command line of the ``bookscrape`` package"""

import unittest
from unittest import mock

from bookscrape.command_line import _available_spiders, crawl, main
from bookscrape.crawl.spiders.kissmanga import KissmangaSpider
from bookscrape.crawl.spiders.readcomiconline import ReadcomiconlineSpider


class TestCommandLine(unittest.TestCase):
    """Test case for the command line of the ``bookscrape`` package"""

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
        with self.assertRaises(SystemExit):
            main([])

        # This should raise when mandatory arguments are missing
        with self.assertRaises(SystemExit):
            main(['kissmanga', 'Akira', '1'])

    @mock.patch('bookscrape.command_line.crawl')
    def test_main_should_call_the_crawl_command(self, crawl):
        """Test that the ``main`` method should call the ``crawl`` method with the corrects args"""

        # With only one volume
        main(['kissmanga', 'Akira', '1', 'not/a/path'])
        crawl.assert_called_with(KissmangaSpider, 'Akira', [1], 'not/a/path', False)

        # With two volumes
        main(['kissmanga', 'Akira', '1', '2', 'not/a/path'])
        crawl.assert_called_with(KissmangaSpider, 'Akira', [1, 2], 'not/a/path', False)

    @mock.patch('twisted.internet.reactor.run')
    @mock.patch('scrapy.crawler.CrawlerRunner.crawl')
    def test_crawl_should_call_the_crawl_method_on_the_crawler_runner(self, mocked_crawl, mocked_run):
        """Test that the ``crawl`` method should call the ``CrawlerRunner.crawl``"""

        crawl(KissmangaSpider, 'Akira', [1], 'not-a-path')

        # The crawl method should be called
        mocked_crawl.assert_called_once_with(
            KissmangaSpider,
            book_slug='Akira',
            volume=1,
            output_dir='not-a-path'
        )

        # The twisted reactor should be launched
        mocked_run.assert_called_once_with()

        # If we want to get two volumes, the crawl method should be called twice
        volumes = [1, 2]
        crawl(KissmangaSpider, 'Akira', volumes, 'not-a-path')

        calls = [
            mock.call(
                KissmangaSpider,
                book_slug='Akira',
                volume=volume,
                output_dir='not-a-path'
            )
            for volume in volumes
        ]

        mocked_crawl.assert_has_calls(calls)
