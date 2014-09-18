#!/usr/bin/env python
import os
import json

from bs4 import BeautifulSoup
import requests


FIRST_PAGE = ('http://biorxiv.org/search/%20jcode%3Abiorxiv%20numresults%3A100%20sort%3A'
              'publication-date%20direction%3Adescending%20format_result%3Astandard')


def get_soup(url):
    r = requests.get(url)
    return BeautifulSoup(r.content)

def get_articles_from_page(soup):
    for link in soup.find_all('a'):
        if 'highwire-cite-linked-title' in link.attrs.get('class', []):
            yield link.attrs.get('href')

def download_pdf(url):
    metadata_url = '{0}.figures-only'.format(url)
    soup = get_soup(metadata_url)
    metadata = get_md(soup)

    if not os.path.exists(metadata['identifier']):
        os.mkdir(metadata['identifier'])
    os.chdir(metadata['identifier'])        

    with open('{0}.json'.format(metadata['identifier']), 'w') as fp:
        json.dump(metadata, fp)

    fname = '{0}.pdf'.format(metadata['identifier'])
    pdf_url = '{0}.full.pdf'.format(url)
    r = requests.get(pdf_url)
    r.raise_for_status()
    with open(fname, 'wb') as fp:
        fp.write(r.content)

    for tag in soup.find_all('a'):
        if 'highwire/filestream' in tag.attrs.get('href', ''):
            url = 'http://biorxiv.org{0}'.format(tag.attrs.get('href'))
            r = requests.get(url)
            fname = url.split('/')[-1]
            with open(fname, 'wb') as fp:
                fp.write(r.content)
    os.chdir('..')

def get_md(soup):
    meta_tags = [x.attrs for x in soup.find_all('meta')]
    md = {}
    for tag in meta_tags:
        if 'name' not in tag:
            continue

        if tag['name'] == 'DC.Identifier':
            md['identifier'] = 'biorxiv-{0}'.format(tag['content'].replace('/', '-'))
            md['external-identifier'] = 'urn:bioRxiv:{0}'.format(tag['content'])
        elif tag['name'] == 'DC.Date':
            md['date'] = tag['content']
        elif tag['name'] == 'DC.Publisher':
            md['publisher'] = tag['content']
        elif tag['name'] == 'DC.Rights':
            md['rights'] = tag['content']
            if 'http://' in tag['content']:
                md['licenseurl'] = 'http://{0}'.format(tag['content'].split('http://')[-1])
        elif tag['name'] == 'DC.Description':
            md['description'] = tag['content']
        elif tag['name'] == '':
            md[''] = tag['content']

        elif tag['name'] == 'og:url':
            md['source'] = tag['content']

        elif tag['name'] == 'citation_journal_title':
            md['journaltitle'] = tag['content']

        elif tag['name'] == 'citation_author':
            if not md.get('creator'):
                md['creator'] = []
            md['creator'].append(tag['content'])
        #elif tag['name'] == '':
        #    md[''] = tag['content']
        #else:
        #    pass
        #print tag.get('name'), tag.get('content')

        #DC.Contributor Sergey Kryazhimskiy
        #DC.Contributor Daniel Paul Rice
        #DC.Contributor Elizabeth Jerison
        #DC.Contributor Michael M Desai
    return md

def get_all_articles():
    soup = get_soup(FIRST_PAGE)
    for i in range(0, (get_last_page(soup) + 1)):
        if i != 0:
            page_url = FIRST_PAGE + '?page={0}'.format(i)
        else:
            page_url = FIRST_PAGE
        soup = get_soup(page_url)
        for link in get_articles_from_page(soup):
            download_pdf(link)

def get_last_page(soup):
    for link in soup.find_all('a'):
        if 'link-icon-after' in link.attrs.get('class', []):
            if 'Last ' in link.contents:
                last_page = link.attrs.get('href', '').split('?page=')[-1]
                return int(last_page)





if __name__ == '__main__':
    get_all_articles()
