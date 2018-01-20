"""this module contains the tests for the command line of the ``bookscrape`` package"""

import unittest
from unittest import mock

from bookscrape.command_line import main


class TestCommandLine(unittest.TestCase):
    """Test case for the command line of the ``bookscrape`` package"""

    def test_main_should_raise_if_wrong_arguments_given(self):
        """Test that the ``main`` method should raise if wrong arguments were given"""

        # This should raise when no arguments are passed
        with self.assertRaises(SystemExit):
            main([])

        # This should raise when mandatory arguments are missing
        with self.assertRaises(SystemExit):
            main(['Akira', '1'])

    @mock.patch('bookscrape.command_line.crawl')
    def test_main_should_call_the_crawl_command(self, crawl):
        """Test that the ``main`` method should call the ``crawl`` method with the corrects args"""

        # With only one volume
        main(['Akira', '1', 'not/a/path'])
        crawl.assert_called_with('Akira', [1], 'not/a/path')

        # With two volumes
        main(['Akira', '1', '2', 'not/a/path'])
        crawl.assert_called_with('Akira', [1, 2], 'not/a/path')

