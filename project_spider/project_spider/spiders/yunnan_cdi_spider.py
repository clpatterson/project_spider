import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class yunnan_cdi(scrapy.Spider):
	"""Scrape all the posts from the disciplinary investigations
	section ('纪律审查') of the Yunnan CDI website.
	"""

	name = 'yunnan'
	start_urls = ['http://www.jjjc.yn.gov.cn/list-5.html', ]

	def parse(self, response):
		"""Finds and requests all posts to be parsed."""

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = 'Unable to obtain IP address'

		server = response.headers.get(b'Server')
		if server is None:
			server = 'Unable to obtain server information'
		server = server.decode('utf-8')

		# Follow all links for posts listed on one
		#   disciplinary investigations directory page.
		urls = response.xpath('//div[@class="tListTit"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Get next page url.
		next_page = response.xpath('//li[@class="next"]/a/@href').extract_first()
		if next_page is not None:
			yield scrapy.Request(next_page, callback=self.parse)

	def parse_docs(self, response):
		"""Scrape content from individal post page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//div[@class="iTitle"]/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div class="iTitle">(.*?)</div>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<', title_tag)
		title = title[0]

		text_tag = re.search(r'<div class="itp">(.*?)</div>', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<', text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check is not None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_string)
		text = ' '.join(text)

		date = response.xpath('//div[@class="dt"]/span/text()').re(r'发布.*')
		date = re.search(r'(\d{4})-?/*?(\d{1,2})-?/*?(\d{1,2})\s(\d{2})?:?(\d{2})?:?(\d{2})?', date[0])
		date = date.group().strip()

		source = response.xpath('//div[@class="dt"]/span/text()').re(r'来源.*')
		source = re.sub(r'[来源：]', '', source[0])
		source = source.strip()

		url = response.url
		id_num = re.findall(r'info-(\d*?-?\d*?).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Yunnan'
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
                        		'server': server,
                        		'proxy': 'http://pattersoncharlesl:KUtKehiWcRcorGgM2@us-wa.proxymesh.com:31280'})

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
