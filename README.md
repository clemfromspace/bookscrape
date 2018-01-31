[![PyPI](https://img.shields.io/pypi/v/bookscrape.svg)](https://pypi.python.org/pypi/bookscrape) [![Build Status](https://travis-ci.org/clemfromspace/bookscrape.svg?branch=master)](https://travis-ci.org/clemfromspace/bookscrape) [![Test Coverage](https://api.codeclimate.com/v1/badges/c716cb35ce542efa1bff/test_coverage)](https://codeclimate.com/github/clemfromspace/bookscrape/test_coverage) [![Maintainability](https://api.codeclimate.com/v1/badges/c716cb35ce542efa1bff/maintainability)](https://codeclimate.com/github/clemfromspace/bookscrape/maintainability)

## Bookscrape
Scrape and build e-books from various websites

### Usage
```
bookscrape kissmanga Akira 1-2 --output_dir=/Users/bookscrape/Documents/
```

The above command will download the volumes `1` and `2` from the `Akira` manga on the `kissmanga` website and save the pdfs files containing the extracted images to `/Users/bookscrape/Documents/`

```
bookscrape --help

usage: bookscrape [-h] [--verbose] {kissmanga,readcomiconline} slug [volume_start-volume_end] output_dir

Download a book volume identified by its slug from the given provider

positional arguments:
  {kissmanga,readcomiconline} The provider to use
  slug                        The slug of the book to download
  [volume_start-volume_end]   The range of volume(s) of the book to download
  output_dir                  The full path of the directory to place the downloaded files
```

### Supported providers
- kissmanga (http://kissmanga.com/)
- readcomiconline (http://readcomiconline.to)


### Install
```
pip install bookscrape
```
