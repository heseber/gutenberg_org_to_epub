# Create eBooks (epub) from books at projekt-gutenberg.org

## What this program does

This program is for you if you want to create an eBook (epub) for a book from [Projekt-Gutenberg.org](https://www.projekt-gutenberg.org/).

Here it what it does:
- Download all chapters, including the table of contents, from a book at [Projekt-Gutenberg.org](https://www.projekt-gutenberg.org/) and merge them into a single HTML file after stripping headers, navigation bars etc.
- Download all resources (images, css files, ...) to a subdirectory of the main html file.
- Update the resource links in the merged HTML file to point to the local copies. This is required for converting the HTML file to epub with Calibre.

If the name of the book was "my_book_title", you will end up with:
- The main HTML file: **my_book_title.html**
- A subdirectory with all resources: **my_book_title_files/**

## What else do you need?

To create an ePub file from the downloaded HTML file and its resources, please use the program **Calibre**. You can import the HTML file as a new book. When the book is imported, use "Convert Book" in Calibre with epub as output format. In the settings of the converter, section "table of contents", please tick the "manual fine tuning" option because the usage of heading tags in files from projekt-gutenberg is sometimes somewhat disorganized and needs to be fixed manually.

## Installation

```sh
git clone https://github.com/heseber/gutenberg_org_to_epub
cd gutenberg_org_to_epub
pip install virtualenv
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Single Book

```sh
source .venv/bin/activate
# The command line argument can be a link to any page of the book
python make_book.py "https://www.projekt-gutenberg.org/........./mybook.html"
```

### Batch Mode

The program now supports batch processing of multiple books. You can specify URLs directly on the command line or use input files.

#### Multiple URLs on Command Line

```sh
python make_book.py "https://www.projekt-gutenberg.org/goethe/faust1/faust1.html" "https://www.projekt-gutenberg.org/goethe/faust2/faust2.html"
```

#### URLs from Text File

Create a text file with one URL per line (see `example_urls.txt`):

```sh
python make_book.py --file urls.txt
```

#### URLs from CSV File

Create a CSV file with URLs in the first column or in a column named 'url' (see `example_urls.csv`):

```sh
python make_book.py --file urls.csv
```

#### URLs from JSON File

Create a JSON file with an array of URLs or objects with 'url' field (see `example_urls.json` and `example_urls_objects.json`):

```sh
python make_book.py --file urls.json
```

#### Additional Options

- `--output-dir` or `-o`: Specify output directory (default: current directory)
- `--continue-on-error`: Continue processing other URLs if one fails

```sh
# Save all books to a specific directory
python make_book.py --file urls.txt --output-dir ./books

# Continue processing even if some books fail
python make_book.py --file urls.txt --continue-on-error
```

### Input File Formats

#### Text File (.txt)
```
# Comments start with #
https://www.projekt-gutenberg.org/goethe/faust1/faust1.html
https://www.projekt-gutenberg.org/goethe/faust2/faust2.html
```

#### CSV File (.csv)
```csv
url,title,author
https://www.projekt-gutenberg.org/goethe/faust1/faust1.html,Faust Part 1,Goethe
https://www.projekt-gutenberg.org/goethe/faust2/faust2.html,Faust Part 2,Goethe
```

#### JSON File (.json)
```json
[
  "https://www.projekt-gutenberg.org/goethe/faust1/faust1.html",
  "https://www.projekt-gutenberg.org/goethe/faust2/faust2.html"
]
```

Or with objects:
```json
[
  {
    "url": "https://www.projekt-gutenberg.org/goethe/faust1/faust1.html",
    "title": "Faust Part 1",
    "author": "Goethe"
  }
]
```

Now you are ready to import the main HTML file as a new book into Calibre and to convert it to epub with Calibre.
