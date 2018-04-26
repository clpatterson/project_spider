import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class henan_cdi(scrapy.Spider):
	"""Scrapes all the posts from the examinations and investigations
	section of the Henan website.
	"""

	name = 'henan'
	start_urls = [
		'http://www.hnsjct.gov.cn/sitesources/hnsjct/page_pc/gzdt/jlsc/list1.html',
	]

	def start_requests(self):
		for url in self.start_urls:
			yield SplashRequest(url, self.parse,
				endpoint='render.html',
				args={'wait': 3.0},
			)

	def parse(self, response):

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = "Unable to obtain IP address"

		server = "Unable to obtain server information"

		# Follow all links for posts.
		urls = response.xpath('//div[@class="colRtitle"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Get next page url.
		next_page = response.xpath('//ul[@class="pagination"]/li/a[@aria-label="Next"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield SplashRequest(next_page, self.parse,
				endpoint='render.html',
				args={'wait': 3.0},
			)
	
	def parse_docs(self, response):
		"""Scrapes content from page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//div[@class="cms-article-tit"]/text()').re(r'[\u4e00-\u9fff].*')
		title = title[0]

		text_tag = re.search(r'<div class="article-detail"(.*?)<!-- 文章评论-start', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)

		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check != None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?', '', item)
				text.append(clean_string)
		text = ' '.join(text)
		
		ds_tag = re.search(r'<div class="cms-article-attach">(.*?)<div class="cms-article-share">', body, re.S)
		ds_tag = ds_tag.group()
		
		date_text = re.search(r'(\d{4})-(\d{2})-(\d{2})', ds_tag)
		date = date_text.group()
		
		source = re.findall(r'来源：([\u4e00-\u9fff]+)', ds_tag)
		source = source[0]

		url = response.url
		id_num = re.findall(r'article(.*?).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Henan'
		item['title'] = title
		item['date'] = date
		item['source'] = source
		item['text'] = text
		item['url'] = response.url
		item['screenshot_url'] = screenshot_url

		yield item

		# Pass url to splash for screenshoting.
		splash_args = {
						'wait': 3.0,
        				'html': 1,
        				'png': 1,
        				'width': 600,
        				'render_all': 1,
        				'wait': 3.0,
    					}
		yield SplashRequest(response.url,
							self.create_screenshot,
							endpoint='render.json',
                        	args=splash_args,
                        	meta={'ip_address': ip_address,
                        		'title': title,
                        		'filename': filename,
                        		'server': server})

	def create_screenshot(self, response):

		png_b64 = response.data['png']
		header = 'data:image/png;base64,'
		png_b64 = header + png_b64

		time = response.headers.get(b'Date')
		time = time.decode('utf-8')

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		url = response.url

		filename = response.meta['filename']

		title = response.meta['title']

		create_pdf(png_b64, url, ip_address, time, server, filename, title)
