import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class sichuan_cdi(scrapy.Spider):
	"""Scrapes all the documents from the authoritative announcements
	section (权威发布) of the Sichuan CDI website.
	"""

	name = 'sichuan'
	start_urls = ['http://www.scjc.gov.cn/zhyw/qwfb/', ]

	def parse(self, response):

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = "Unable to obtain IP address"

		server = response.headers.get(b'Server')
		server = server.decode('utf-8')

		# Follow all links for posts.
		urls = response.xpath('//p[@class="name"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address, 'server': server})

		# Get next page url.
		next_page = response.xpath('//a[@class="page-next"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)
	
	def parse_docs(self, response):
		"""Scrapes content from page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h3/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<h3 class="article">(.*?)</h3>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<', title_tag)
		title = title[0]

		text_tag = re.search(r'<div class="content_txt">(.*?)</div>', body, re.S)
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

		date = response.xpath('//p[@class="laiyuan"]/span/text()').re(r'发布.*')
		date = re.sub(r'[发布日期：]', '', date[0])
		date = date.strip()

		source = response.xpath('//p[@class="laiyuan"]/span/text()').re(r'来源.*')
		source = source[0][3:]
		source = source.strip()

		url = response.url
		id_num = re.findall(r'qwfb/(\d*?/\d*?).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Sichuan'
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

