"""This module contains the loggers for the ``bookscrape`` package"""

from logzero import setup_logger, LogFormatter


log_formatter = LogFormatter(
    fmt='%(color)s[%(levelname)1.1s %(asctime)s]%(end_color)s %(message)s'
)
logger = setup_logger(
    name='bookscrape',
    formatter=log_formatter
)
