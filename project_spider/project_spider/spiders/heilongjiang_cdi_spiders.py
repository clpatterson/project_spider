import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class heilongjiang_cdi(scrapy.Spider):
	"""Scrapes all the posts from examination and investigations
	section (曝光台) of the Heilongjiang CDI website.
	"""

	name = 'heilongjiang'
	start_urls = [
		'http://www.hljjjjc.gov.cn/news.php?cid=15&page=1',
	]

	def parse(self, response):
		"""Finds and requests all posts to be parsed."""

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
		urls = response.xpath('//div[@class="main01_con font_16"]/ul/li/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address, 
																'server': server})

		#get next page url from next page bottom
		next_page = response.xpath('//div[@class="page_list1"]/a[@title="下一页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)


			
	def parse_docs(self, response):
		"""Scrapes content from page."""
		
		body = response.body
		body = body.decode('utf-8')

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		title = response.xpath('//div[@class="main02_tit01"]/text()').extract()
		title = title[0]
		#if title == []:
		#	title_tag = re.search(r'<h1 class="fl">(.*?)</h1>', body, re.S)
		#	title_tag = title_tag.group()
		#	title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)

		text_tag = re.search(r'<div class="main02_con font_17">(.*?)<!--三级页', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			num_check = re.search(r'[0-9]', item)
			if han_check or num_check != None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', item)
				clean_string = clean_string.strip()
				text.append(clean_string)
		text = ' '.join(text)

		ds_text = response.xpath('//div[@class="main02_tit02 black font_16"]/text()').extract()
		date = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ds_text[0])
		date = date.group()

		source = re.findall(r'来源：([\u4e00-\u9fff].*?)\s', ds_text[0])
		if source == []:
			source = ''
		else:
			source = source[0].strip()

		url = response.url
		id_num = re.findall(r'&id=(\d*)', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Heilongjiang'
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