# -*- coding: utf-8 -*-
__author__ = 'yongtzha'


import requests
from bs4 import BeautifulSoup
import common
import os
import urlparse

logger = common.get_logger(__name__)

class QSBK(object):
	def __init__(self):
		self.url = 'http://www.qiushibaike.com'

	def get_page(self, page_url=None):
		# page_url = '%s/pages/%d' %(self.url,page)
		if not page_url:
			page_url = self.url
		logger.info('Get content from %s' % page_url)
		r = requests.get(page_url)
		print r.status_code
		print r.encoding
		data = r.text.encode('utf-8')
		with open('result.html', 'wb') as f:
			f.write(data)
		return data

	def article_tag(self, tag):
		return tag.name == 'div' and tag.has_attr('class') and tag['class'] == 'article block untagged mb15'.split()

	def article_class(self, css_class):
		return css_class == 'article block untagged mb15'

	def analysis_page(self, page_url=None):
		page_code = self.get_page(page_url)
		if not page_code:
			print 'could not get page content'
			return
		soup = BeautifulSoup(page_code, 'lxml')
		items = self.get_item(soup)
		next_page = self.get_next_page(soup)
		return items, next_page

	def get_item(self, page_soup):
		items = []
		for article in page_soup.find_all(name='div', class_=self.article_class):
			content = article.find('div', class_='content').get_text().strip().encode('utf-8')
			author = article.find('div', class_='author clearfix').find('h2').string.strip().encode('utf-8')
			stats_vote = article.find('div', class_='stats').span.i.string
			article_id = article['id'].split('_')[2]
			##get image url
			imgs = []
			for thumb_blk in article.find_all('div', class_='thumb'):
				for img_blk in thumb_blk.find_all('img'):
					imgs.append(img_blk['src'])
			items.append((author, content, stats_vote, imgs, article_id))
		return items

	def get_next_page(self, page_soup):
		next_page = None
		for page_block in page_soup.find('ul', class_='pagination').find_all('li'):
			p_class = page_block.find('span')['class']
			logger.info('p class is %s' % p_class)
			if 'next' in p_class:
				next_page = page_block.find('a')['href']
				logger.info('next page url is %s' % next_page)
				break
		return next_page


	def get_page_item(self, total_page=3):
		page_count = 1
		page_url = None
		total_items = []
		while page_count <= total_page:
			items, next_page = self.analysis_page(page_url)
			total_items.extend(items)
			if not next_page:
				break
			else:
				page_url = '%s%s' % (self.url, next_page)
			page_count += 1
		return total_items

	def save_items(self):
		items = self.get_page_item()
		for item in items:
			author = item[0]
			content = item[1]
			imgs = item[3]
			article_id = item[4]
			self.save_item(author, content, imgs, article_id)

	def save_item(self, author, content, imgs, article_id):
		try:
			article_dir = 'qushibaike/%s/%s'%(author, article_id)
			os.makedirs(article_dir)
		except OSError:
			pass
		finally:
			for img in imgs:
				self.download_img(img, article_dir)
			self.write_content(content, article_dir)

	def write_content(self, content, article_dir):
		with open('%s/content.txt' % article_dir, 'wb') as fd:
			fd.write(content)

	def download_img(self, img_url, save_dir):
		pr = urlparse.urlparse(img_url)
		file_name = pr.path.split('/')[-1]
		r = requests.get(img_url, stream=True)
		with open('%s/%s' % (save_dir, file_name), 'wb') as fd:
		    for chunk in r.iter_content(512):
		        fd.write(chunk)

if __name__ == '__main__':
	qsbk = QSBK()
	qsbk.save_items()
