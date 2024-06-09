"""
This script scrapes https://www.monetizemore.com/blog by iterating back in its history.

Install Notes:
  You have to install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
"""
import os
import random
import time

from bs4 import BeautifulSoup
import pdfkit
import requests
import tempfile

if os.name == 'nt':
    wkhtmltopdf_path = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
else:
    wkhtmltopdf_path = '/usr/local/bin/wkhtmltopdf'

output_dir = 'output'
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def scrape_section(base_url):
    page = 1
    total_pages = 1

    url = base_url

    # extract the category name from the url
    category_name = base_url.split('/')[-2]

    cat_output_dir = f"{output_dir}/{category_name}"
    if not os.path.exists(cat_output_dir):
        os.makedirs(cat_output_dir)

    while page <= total_pages:
        print(f"Scraping page {page}")

        # request the url using user-agent to avoid 403 forbidden
        html = requests.get(url, headers={'User-Agent': user_agent})
        soup = BeautifulSoup(html.content, 'html.parser')

        # find all divs with class 'page-numbers'
        page_numbers = soup.find_all('a', class_='page-numbers')

        if len(page_numbers) > 0:
            # the last div contains the highest page number
            if int(page_numbers[-2].text) != total_pages:
                total_pages = int(page_numbers[-2].text)
                print(f"Blog has {total_pages} pages")

        # find all divs with class 'single-casestudy-otr'
        divs = soup.find_all('div', class_='single-casestudy-otr')

        # find all a-tags in the divs
        a_tags = [div.find_all('a') for div in divs]

        # extract the href attribute from the a-tags
        page_urls = [a['href'] for a_list in a_tags for a in a_list]

        print(f"Found {len(page_urls)} blog posts on page {page}")

        # loop and retrieve each url
        for page_url in page_urls:
            file_name = page_url.split('/')[-2]
            output_file = f"{cat_output_dir}/{file_name}.pdf"

            # if output_file already exists, skip this one
            if os.path.exists(output_file):
                print(f"Output file {output_file} already exists, skipping")
                continue

            # pause for a random time between 1 and 3 seconds
            print("Pausing...")
            time.sleep(random.randint(1, 3))

            print("Retrieving:", page_url)
            blog_page = requests.get(page_url, headers={'User-Agent': user_agent})
            soup = BeautifulSoup(blog_page.content, 'html.parser')

            # remove the header and footer tags from the blog post
            for div in soup.find_all('header'):
                div.decompose()
            for div in soup.find_all('footer'):
                div.decompose()

            # remove the breadcrumbs from the blog post
            for div in soup.find_all('section', class_='cont-breadcrumb-sec'):
                div.decompose()

            # remove the right div from the blog post
            for div in soup.find_all('div', class_='blogdetail-right'):
                div.decompose()

            # remove 'cont-keep-reading' and 'cont-worldwide-publishers' divs
            for div in soup.find_all('section', class_='cont-keep-reading'):
                div.decompose()
            for div in soup.find_all('section', class_='cont-worldwide-publishers'):
                div.decompose()

            # remove section tag with 'cont-fixed-sec' class
            for div in soup.find_all('section', class_='cont-fixed-sec'):
                div.decompose()

            # remove class 'single-post' from body tag
            for div in soup.find_all('body', class_='single-post'):
                div['class'].remove('single-post')

            # remove class 'cont-case-detail-content' from section tag with that class
            for div in soup.find_all('section', class_='cont-case-detail-content'):
                div['class'].remove('cont-case-detail-content')

            # Add CSS to avoid splitting lines between pages
            css = """
                <style>
                    div, p {
                        page-break-inside: avoid;
                    }
                </style>
                """

            # add css to head tag in blog post
            head = soup.head
            head.append(BeautifulSoup(css, 'html.parser'))

            # remove all script tags from page
            for script in soup.find_all('script'):
                script.decompose()

            # Write content to a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp:
                temp.write(str(soup.html).encode('utf-8'))
                temp_path = temp.name

            # Render HTML and write content to PDF file
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
            pdfkit.from_file(temp_path, output_file, configuration=config)

            # Remove the temporary file
            os.remove(temp_path)

            print("Saved:", output_file)

        page += 1
        url = f'{base_url}page/{page}/'

        # pause for a random time between 1 and 3 seconds
        print("Pausing...")
        time.sleep(random.randint(1, 3))


url = 'https://www.monetizemore.com/blog'

# request the url using user-agent to avoid 403 forbidden
html = requests.get(url, headers={'User-Agent': user_agent})
soup = BeautifulSoup(html.content, 'html.parser')

# find a links on the page with category/ in them
category_tags = soup.find_all('a', href=lambda x: x and 'category/' in x)

# extract the href and text content from the a-tags
categories = [(a['href'], a.text) for a in category_tags]

print("Found", len(categories), "categories")

# loop through each category and scrape the section
for category in categories:
    if 'Portuguese' in category[1]:
        continue

    print(f"Scraping category: {category[1]}")

    scrape_section(category[0])

    print(f"Finished scraping category: {category[1]}")
