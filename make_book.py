import argparse
import csv
import json
import os
import sys
import urllib.request
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def fetch_webpage(url):
    """
    Fetches the HTML content of a web page given a URL.

    Parameters:
    url (str): The URL of the web page to fetch.

    Returns:
    str: The HTML content of the web page.
    """
    response = urllib.request.urlopen(url)
    html = response.read()
    return html.decode("utf-8")


def extract_section(html, tag, class_name=None):
    """
    Extracts sections from the HTML content based on the specified tag and class name.

    Parameters:
    html (str): The HTML content of the web page.
    tag (str): The HTML tag to search for.
    class_name (str, optional): The class name of the tag to search for. Defaults to None.

    Returns:
    list: A list of extracted sections as strings.
    """
    soup = BeautifulSoup(html, "html.parser")
    if class_name:
        sections = soup.find_all(tag, class_=class_name)
    else:
        sections = soup.find_all(tag)
    return [str(section) for section in sections]


def extract_content_by_class(html_content, class_name):
    """
    Extracts the text content from HTML tags of a specific class.

    Parameters:
    html_content (str): The HTML content as a string.
    class_name (str): The class name to search for.

    Returns:
    list: A list of strings containing the text content of each tag with the specified class.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    content_list = [
        element.get_text(strip=True) for element in soup.find_all(class_=class_name)
    ]
    return content_list


def extract_links(anchor_tags):
    """
    Extracts the href attribute from a list of <a> tag strings.

    Parameters:
    anchor_tags (list): A list of strings, each containing an <a> tag.

    Returns:
    list: A list of href attribute values (URLs).
    """
    links = []
    for tag in anchor_tags:
        soup = BeautifulSoup(tag, "html.parser")
        a_tag = soup.find("a", href=True)
        if a_tag:
            links.append(a_tag["href"])
    return links


def extract_links_and_text(anchor_tags):
    """
    Extracts URLs and link text from a list of <a> tag strings.

    Parameters:
    anchor_tags (list): A list of strings, each containing an <a> tag.

    Returns:
    dict: A dictionary where keys are URLs from href attributes and values are the link text.
    """
    links_dict = {}
    for tag in anchor_tags:
        soup = BeautifulSoup(tag, "html.parser")
        a_tag = soup.find("a", href=True)
        if a_tag:
            href = a_tag["href"]
            text = a_tag.get_text(strip=True)
            links_dict[href] = text
    return links_dict


def extract_stylesheet_links(html):
    """
    Extracts all stylesheet (CSS) links from an HTML page.

    Parameters:
    html (str): The HTML content of the web page.

    Returns:
    list: A list of URLs pointing to the CSS stylesheets.
    """
    soup = BeautifulSoup(html, "html.parser")
    stylesheet_links = []
    for link_tag in soup.find_all("link", rel="stylesheet"):
        href = link_tag.get("href")
        if href:
            stylesheet_links.append(href)
    return stylesheet_links


def get_chapter_urls(url):
    """
    Extracts all chapter URLs and the chapter names from the index page.

    Parameters:
    url (str): The main URL of the book (base URL or URL of any chapter or of index)

    Returns:
    dict: a dictionary with chapter URLs as keys and chapter names as values
    """
    if not url.endswith("/"):
        url = url[: url.rfind("/") + 1]
    index_page = fetch_webpage(url)
    section = extract_section(index_page, "ul").pop()
    anchors = extract_section(section, "a")
    links = extract_links_and_text(anchors)
    links = {f"{url}{key}": value for key, value in links.items()}
    return links


def remove_leading_to_class(html_content, target_class):
    """
    Removes the leading part of an HTML string up to and including a tag with a specific class.

    Parameters:
    html_content (str): The HTML content as a string.
    target_class (str): The class name to search for.

    Returns:
    str: The modified HTML content with the leading part removed.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    target_element = soup.find(class_=target_class)

    if target_element:
        # Find the position of the target element in the original HTML
        target_position = html_content.find(str(target_element))
        if target_position != -1:
            # Return the HTML content starting after the target element
            return html_content[target_position + len(str(target_element)) :]

    # If the target element is not found, return the original HTML content
    return html_content


def remove_rightmost_div_by_class(html_content, target_class):
    """
    Removes the rightmost part of an HTML string starting with a <div> tag of a specific class.

    Parameters:
    html_content (str): The HTML content as a string.
    target_class (str): The class name to search for in <div> tags.

    Returns:
    str: The modified HTML content with the rightmost part removed.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    div_tags = soup.find_all("div", class_=target_class)

    if div_tags:
        # Find the last occurrence of the target <div> tag
        last_div = div_tags[-1]
        # Find the position of the last <div> tag in the original HTML
        div_position = html_content.rfind(str(last_div))
        if div_position != -1:
            # Return the HTML content up to the start of the last <div> tag
            return html_content[:div_position]

    # If no target <div> tag is found, return the original HTML content
    return html_content


def remove_divs_by_class(html_content, target_class):
    """
    Removes all <div> sections of a specific class from an HTML string.

    Parameters:
    html_content (str): The HTML content as a string.
    target_class (str): The class name of the <div> tags to remove.

    Returns:
    str: The modified HTML content with the specified <div> sections removed.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Find and remove all <div> tags with the specified class
    for div in soup.find_all("div", class_=target_class):
        div.decompose()

    return str(soup)


def modify_headline_classes(html_content):
    """
    Adds the class "chapter" to all <h1>, <h2> and <h3> tags unless they already have a class "title" or "subtitle" or "author".
    For modified tags, all other classes except "chapter" are removed.

    Parameters:
    html_content (str): The HTML content as a string.

    Returns:
    str: The modified HTML content with updated classes for <h1> and <h2> tags.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Iterate over all <h1>, <h2> and <h3> tags
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        classes = tag.get("class", [])
        # Check if the tag has "title" or "author" class
        if (
            "title" not in classes
            and "author" not in classes
            and "subtitle" not in classes
        ):
            # Set the class to "chapter", removing any existing classes
            tag["class"] = ["chapter"]

    return str(soup)


def extract_meta_tags(html_string):
    # Parse the HTML string using BeautifulSoup
    soup = BeautifulSoup(html_string, "html.parser")

    # Initialize an empty dictionary to store meta tags
    meta_tags = {}

    # Find all meta tags in the HTML
    for meta in soup.find_all("meta"):
        # Get the 'name' or 'property' attribute as the key
        key = meta.get("name") or meta.get("property")
        # Get the 'content' attribute as the value
        value = meta.get("content")

        # If a key is found, add it to the dictionary
        if key and value:
            meta_tags[key] = value

    return meta_tags


def get_prosa(url):
    """
    Extracts the chapter content without header, navigation bar, and footer

    Parameters:
    url(str): The URL of the chapter

    Returns:
    str: The HTML content for the book chapter
    """
    page = fetch_webpage(url)
    # The prosa starts after the tag of class "anzeige-chap"
    page = remove_leading_to_class(page, "anzeige-chap")
    # Remove everything after and including the bottom navigation bar
    page = remove_rightmost_div_by_class(page, "bottomnavi-gb")
    # Remove and print ads
    page = remove_divs_by_class(page, "anzeige-print")
    # The prosa ends at the last <hr> tag
    last_hr_index = page.rfind("<hr")
    if last_hr_index != -1:
        page = page[:last_hr_index]
    # Upgrade heading levels to facilitate creating of TOC in Calibre
    page = modify_headline_classes(page)
    return page


def get_book_content(url):
    """
    Get the pure book content (just the prosa) of a book.

    Parameters:
    url (str): The base URL of the book.

    Returns:
    str: The concatenated prosa of all chapters.
    """
    chapter_urls = get_chapter_urls(url)
    book = [get_prosa(x) for x in chapter_urls.keys()]
    book = "\n".join(book)
    return book


def generate_html(meta_tags, main_content, stylesheet_urls, title):
    # Start the HTML document
    html = ["<!DOCTYPE html>", "<html>", "<head>"]

    # Add the title
    html.append(f"<title>{title}</title>")

    # Add meta tags
    for name, content in meta_tags.items():
        html.append(f'<meta name="{name}" content="{content}">')

    # Add stylesheet links
    for url in stylesheet_urls:
        html.append(f'<link rel="stylesheet" type="text/css" href="{url}">')

    # Close the head section and start the body section
    html.append("</head>")
    html.append("<body>")

    # Add the main content
    html.append(main_content)

    # Close the body and html tags
    html.append("</body>")
    html.append("</html>")

    # Join all parts into a single string
    return "\n".join(html)


def convert_relative_to_absolute(html_content, base_url):
    """
    Converts all relative links in an HTML page to absolute links using the provided base URL.

    Parameters:
    html_content (str): The HTML content as a string.
    base_url (str): The base URL to use for converting relative links to absolute links.

    Returns:
    str: The modified HTML content with absolute links.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    if not base_url.endswith("/"):
        base_url = base_url[: base_url.rfind("/") + 1]

    # Convert relative links in <a> tags
    for a_tag in soup.find_all("a", href=True):
        a_tag["href"] = urljoin(base_url, a_tag["href"])

    # Convert relative links in <img> tags
    for img_tag in soup.find_all("img", src=True):
        img_tag["src"] = urljoin(base_url, img_tag["src"])

    # Convert relative links in <link> tags
    for link_tag in soup.find_all("link", href=True):
        link_tag["href"] = urljoin(base_url, link_tag["href"])

    # Convert relative links in <script> tags
    for script_tag in soup.find_all("script", src=True):
        script_tag["src"] = urljoin(base_url, script_tag["src"])

    return str(soup)


def save_html_with_resources(html_string, save_dir, html_filename):
    # Create the save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    # Parse the HTML content
    soup = BeautifulSoup(html_string, "html.parser")

    # Create a subdirectory for resources
    if html_filename.endswith(".html"):
        # Remove the '.html' extension and append '_files'
        resources_dir = html_filename[:-5] + "_files"
    else:
        # If the filename doesn't end with '.html', return it unchanged with '_files' appended
        resources_dir = html_filename + "_files"
    resources_dir = os.path.join(save_dir, resources_dir)
    os.makedirs(resources_dir, exist_ok=True)

    # Define a function to download and replace links
    def download_and_replace(tag, attribute):
        url = tag.get(attribute)
        if url:
            # Resolve the full URL
            full_url = urljoin(html_filename, url)
            # Parse the URL to get the filename
            parsed_url = urlparse(full_url)
            filename = os.path.basename(parsed_url.path)
            local_path = os.path.join(resources_dir, filename)

            # Download the resource
            try:
                response = requests.get(full_url)
                response.raise_for_status()
                with open(local_path, "wb") as file:
                    file.write(response.content)

                # Update the tag's attribute to point to the local resource
                tag[attribute] = os.path.relpath(local_path, save_dir)
            except requests.RequestException as e:
                print(f"Failed to download {full_url}: {e}")

    # Download and replace links for <img> tags
    for img in soup.find_all("img"):
        download_and_replace(img, "src")

    # Download and replace links for <link> tags (e.g., stylesheets)
    for link in soup.find_all("link", rel="stylesheet"):
        download_and_replace(link, "href")

    # Download and replace links for <script> tags
    for script in soup.find_all("script"):
        download_and_replace(script, "src")

    # Save the modified HTML to a file
    html_path = os.path.join(save_dir, html_filename)
    with open(html_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

    return html_path


def write_book(base_url, output_dir="."):
    """
    Write a full book from project Gutenberg as a single html page.

    Parameters:
    base_url (str): The URL of any book chapter, or the index page, or the base URL
    output_dir (str): Directory to save the output files (default: current directory)
    """
    if not base_url.endswith("/"):
        base_url = base_url[: base_url.rfind("/") + 1]
    book_content = get_book_content(base_url)
    meta_tags = extract_meta_tags(fetch_webpage(base_url))
    # Get the author, either from a tag with class "author" or from the meta tags
    author = extract_content_by_class(book_content, "author")
    if author:
        author = author[0]
    else:
        author = meta_tags.get("author", "Unknown")
    # Get the title, either from a tag with class "title" or from the meta tags
    title = extract_content_by_class(book_content, "title")
    if title:
        title = title[0]
    else:
        title = meta_tags.get("title", "Unknown")
    stylesheet_urls = extract_stylesheet_links(fetch_webpage(base_url))
    full_page = generate_html(meta_tags, book_content, stylesheet_urls, title)
    full_page = convert_relative_to_absolute(full_page, base_url)
    file_name = f"{author} - {title}.html"
    save_html_with_resources(full_page, output_dir, file_name)


def parse_urls_from_file(file_path):
    """
    Parse URLs from different file formats.

    Parameters:
    file_path (str): Path to the input file

    Returns:
    list: List of URLs found in the file
    """
    urls = []

    # Determine file type based on extension
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == ".json":
            # JSON format: expect array of URLs or array of objects with 'url' field
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            urls.append(item)
                        elif isinstance(item, dict) and "url" in item:
                            urls.append(item["url"])
                else:
                    raise ValueError("JSON file must contain an array")

        elif file_ext == ".csv":
            # CSV format: expect URLs in first column or column named 'url'
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if "url" in reader.fieldnames:
                    # Use 'url' column if it exists
                    for row in reader:
                        if row["url"].strip():
                            urls.append(row["url"].strip())
                else:
                    # Use first column
                    f.seek(0)  # Reset file pointer
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if row and row[0].strip():
                            urls.append(row[0].strip())

        else:
            # Text format: one URL per line
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(
                        "#"
                    ):  # Skip empty lines and comments
                        urls.append(line)

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    return urls


def validate_urls(urls):
    """
    Validate that all URLs are from projekt-gutenberg.org

    Parameters:
    urls (list): List of URLs to validate

    Returns:
    tuple: (valid_urls, invalid_urls)
    """
    valid_urls = []
    invalid_urls = []

    for url in urls:
        if url.startswith("https://www.projekt-gutenberg.org/"):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)

    return valid_urls, invalid_urls


def main():
    parser = argparse.ArgumentParser(
        description="Convert Gutenberg.org books to HTML with embedded resources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL
  python make_book.py "https://www.projekt-gutenberg.org/goethe/faust2/faust2.html"
  
  # Multiple URLs on command line
  python make_book.py "https://www.projekt-gutenberg.org/goethe/faust2/faust2.html" "https://www.projekt-gutenberg.org/goethe/faust1/faust1.html"
  
  # URLs from text file (one per line)
  python make_book.py --file urls.txt
  
  # URLs from CSV file (first column or 'url' column)
  python make_book.py --file urls.csv
  
  # URLs from JSON file (array of strings or objects with 'url' field)
  python make_book.py --file urls.json
        """,
    )

    parser.add_argument(
        "urls", nargs="*", help="One or more Gutenberg.org URLs to convert"
    )

    parser.add_argument(
        "--file", "-f", help="Input file containing URLs (supports .txt, .csv, .json)"
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for generated HTML files (default: current directory)",
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing other URLs if one fails",
    )

    args = parser.parse_args()

    # Collect all URLs
    all_urls = []

    # Add URLs from command line arguments
    if args.urls:
        all_urls.extend(args.urls)

    # Add URLs from file if specified
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)

        file_urls = parse_urls_from_file(args.file)
        if not file_urls:
            print(f"Error: No valid URLs found in file '{args.file}'")
            sys.exit(1)

        all_urls.extend(file_urls)

    # Check if we have any URLs
    if not all_urls:
        parser.print_help()
        print(
            "\nError: No URLs provided. Please specify URLs on command line or use --file option."
        )
        sys.exit(1)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Validate URLs
    valid_urls, invalid_urls = validate_urls(unique_urls)

    if invalid_urls:
        print(
            "Warning: The following URLs are not from projekt-gutenberg.org and will be skipped:"
        )
        for url in invalid_urls:
            print(f"  {url}")
        print()

    if not valid_urls:
        print(
            "Error: No valid URLs found. All URLs must start with 'https://www.projekt-gutenberg.org/'"
        )
        sys.exit(1)

    # Create output directory if it doesn't exist
    if args.output_dir != ".":
        os.makedirs(args.output_dir, exist_ok=True)

    # Process each URL
    successful = 0
    failed = 0

    print(f"Processing {len(valid_urls)} book(s)...")
    print()

    for i, url in enumerate(valid_urls, 1):
        print(f"[{i}/{len(valid_urls)}] Processing: {url}")

        try:
            write_book(url, args.output_dir)
            print("  ✓ Successfully converted")
            successful += 1

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed += 1

            if not args.continue_on_error:
                print(
                    "\nStopping due to error. Use --continue-on-error to continue processing other URLs."
                )
                sys.exit(1)

        print()

    # Summary
    print("Processing complete!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
