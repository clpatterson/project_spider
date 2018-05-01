import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class shandong_cdi(scrapy.Spider):
	"""Scrapes all the posts from the publicly released
	announcements section (通报曝光) of the Shandong website.
	"""

	name = 'shandong'
	start_urls = [
		'http://www.sdjj.gov.cn/tbbg/',
	]

	def parse(self,response):
		
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
		urls = response.xpath('//ul[@id="mycarousel"]/li/h3/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Get next page url.
		next_page = response.xpath('//div[@class="flip"]/a[text()=">"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)
	
	def parse_docs(self, response):
		"""Scrapes content from page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h2/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			tsd_tag = re.search(r'<div class="head">(.*?)<div', body, re.S)
			tsd_tag = tsd_tag.group()
			tsd = re.findall(r'>([\u4e00-\u9fff].*?)<',tsd_tag)
			title = tsd[0]
		title = title[0]

		text_tag = re.search(r'<div class=TRS_Editor>(.*?)</div>', body, re.S)
		if text_tag == None:
			text_tag = re.search(r'<div class="play"(.*?)<div id="flip"', body, re.S)
			text_tag = text_tag.group()
			#text = re.findall(r'>.*?(\d*?[\u4e00-\u9fff].*?)<',text_tag, re.S)
			tag_values = re.findall(r'>[^>]*<', text_tag, re.S)
		else:
			text_tag = text_tag.group()
			#text = re.findall(r'>.*?(\d*?[\u4e00-\u9fff].*?)<',text_tag, re.S)
			tag_values = re.findall(r'>[^>]*<', text_tag, re.S)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check is not None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_string)
		text = ' '.join(text)
		
		date = response.xpath('//div[@class="head"]/p/span/text()').re(r'发布.*')
		if date == None:
			date = tsd[2]
		date = re.search(r'(\d{4})-?/*?(\d{1,2})-?/*?(\d{1,2})', date[0])
		date = date.group().strip()
		
		source = response.xpath('//div[@class="head"]/p/span/text()').re(r'来源.*')
		if source == None:
			source = tsd [1]
		source = re.sub(r'[来源：]', '', source[0])
		source = source.strip()

		url = response.url
		id_num = re.findall(r'tbbg/(.*?).htm', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Shandong'
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
                        		'server': server
                        		'proxy': 'http://pattersoncharlesl:PASSWORD@us-wa.proxymesh.com:31280'})

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