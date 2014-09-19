#!/usr/bin/env python
import sys
import os
import json
import logging

from bs4 import BeautifulSoup
import futures
import requests
from internetarchive import get_item
import magic


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ROOT_DIR = os.get_cwd()

FIRST_PAGE = ('http://biorxiv.org/search/%20jcode%3Abiorxiv%20numresults%3A100%20sort%3A'
              'publication-date%20direction%3Adescending%20format_result%3Astandard')


def get_soup(url):
    r = requests.get(url)
    return BeautifulSoup(r.content)

def get_last_page(soup):
    for link in soup.find_all('a'):
        if 'link-icon-after' in link.attrs.get('class', []):
            if 'Last ' in link.contents:
                last_page = link.attrs.get('href', '').split('?page=')[-1]
                return int(last_page)

def get_articles_from_page(soup):
    for link in soup.find_all('a'):
        if 'highwire-cite-linked-title' in link.attrs.get('class', []):
            yield link.attrs.get('href')

def download_pdf(url):
    metadata_url = '{0}.figures-only'.format(url)
    soup = get_soup(metadata_url)
    metadata = get_md(soup)

    item = get_item(metadata['identifier'])
    if item.exists:
        log.info('{0} already exists, skipping'.format(metadata['identifier']))
        return

    log.info('downloading metadata and data for item {0}'.format(metadata['identifier']))

    item_dir = os.path.join(ROOT_DIR, metadata['identifier'])
    if not os.path.exists(item_dir):
        os.mkdir(item_dir)
    os.chdir(item_dir)        

    with open('{0}.json'.format(metadata['identifier']), 'w') as fp:
        json.dump(metadata, fp)

    fname = '{0}.pdf'.format(metadata['identifier'])
    pdf_url = '{0}.full.pdf'.format(url)
    r = requests.get(pdf_url)
    r.raise_for_status()

    # Error out if file is not a PDF.
    mime = magic.from_buffer(r.content, mime=True)
    if mime != 'application/pdf':
        log.error('{0}/{0}.pdf is not a PDF, not archiving'.format(metadata['identifier']))
        return

    with open(fname, 'wb') as fp:
        fp.write(r.content)

    for tag in soup.find_all('a'):
        if 'highwire/filestream' in tag.attrs.get('href', ''):
            url = 'http://biorxiv.org{0}'.format(tag.attrs.get('href'))
            r = requests.get(url)
            fname = url.split('/')[-1]
            with open(fname, 'wb') as fp:
                fp.write(r.content)
    os.chdir(ROOT_DIR)
    log.info('successfully downloaded item {0}'.format(metadata['identifier']))

def get_md(soup):
    md = dict(
        # Defualt IA metadata.
        collection='biorxiv',
        mediatype='texts',
        language='eng',
    )

    for link in soup.find_all('a'):
        if 'highlight' in link.attrs.get('class', []):
            if '/collection/' in link.attrs.get('href', ''):
                md['subject'] = link.contents[0]

    meta_tags = [x.attrs for x in soup.find_all('meta')]
    for tag in meta_tags:
        if 'name' not in tag:
            continue

        # DC metadata.
        if tag['name'] == 'DC.Identifier':
            md['identifier'] = 'biorxiv-{0}'.format(tag['content'].replace('/', '-'))
            md['external-identifier'] = 'urn:bioRxiv:{0}'.format(tag['content'])
        elif tag['name'] == 'DC.Date':
            md['date'] = tag['content']
        elif tag['name'] == 'DC.Publisher':
            md['publisher'] = tag['content']
        elif tag['name'] == 'DC.Title':
            md['title'] = tag['content']
        elif tag['name'] == 'DC.Rights':
            md['rights'] = tag['content']
            if 'http://' in tag['content']:
                md['licenseurl'] = 'http://{0}'.format(tag['content'].split('http://')[-1])
        elif tag['name'] == 'DC.Description':
            md['description'] = tag['content']
        elif tag['name'] == '':
            md[''] = tag['content']
        elif tag['name'] == 'DC.Contributor':
            if not md.get('contributor'):
                md['contributor'] = []
            md['contributor'].append(tag['content'])

        # og metadata.
        elif tag['name'] == 'og:url':
            md['source'] = tag['content']

        # citation metadata
        elif tag['name'] == 'citation_journal_title':
            md['journaltitle'] = tag['content']
        elif tag['name'] == 'citation_author':
            if not md.get('creator'):
                md['creator'] = []
            md['creator'].append(tag['content'])
    return md

def get_all_articles():
    soup = get_soup(FIRST_PAGE)
    for i in range(0, (get_last_page(soup) + 1)):
        if i != 0:
            page_url = FIRST_PAGE + '?page={0}'.format(i)
        else:
            page_url = FIRST_PAGE
        log.info('getting all articles from page {0}'.format(page_url))
        soup = get_soup(page_url)
        for link in get_articles_from_page(soup):
            yield link


if __name__ == '__main__':
    # If URL is provided as an argument, archive only the URL provided
    # and exit with 0.
    if sys.argv[-1].startswith('http:'):
        link = sys.argv[-1]
        download_pdf(link)
        sys.exit(0)
        
    # Else, Archive everything we don't have.
    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        for result in executor.map(download_pdf, get_all_articles()):
            pass
