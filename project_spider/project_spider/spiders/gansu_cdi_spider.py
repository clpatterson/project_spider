import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from scrapy.utils.request import request_fingerprint
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class gansu_cdi(scrapy.Spider):
	"""Scrapes all the documents from the examinations and investigations
	section (审查调查) of the Gansu CDI website.
	"""

	name = 'gansu'
	start_urls = [
		'http://www.gsjw.gov.cn/category/jlsc',
	]

	def parse(self, response):
		"""Find and pass all links for posts listed on one 
		bulletin directory page to parser.
		"""

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = "Unable to obtain IP address"

		server = response.headers.get(b'Server')
		if server is None:
			server = "Unable to obtain server information"
		server = server.decode('utf-8')

		# Get list of post urls.
		post_urls = response.xpath('//ul[@class="list"]/li/a/@href').extract() 
		for url in post_urls:
			yield response.follow(url, self.parse_docs, meta={'ip_address': ip_address,
										'deltafetch_key': request_fingerprint(response.request),
										'server': server})

		# Get next page.
		next_page = response.xpath('//div[@class="page"]/a[text()="下一页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)

	def parse_docs(self, response):
		"""Scrapes content from post page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		# Get title.
		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div class="content">(.*?)<div class="infoBox"', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
		title = title[0]

		# Pull all tag values. 
		text_tag = re.search(r'<div id="content"(.*?)</div>', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check != None:
				clean_sting = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_sting)
		text = ' '.join(text)

		ds_text = response.xpath('//div[@style="margin:0 auto; width:700px;"]/text()').extract_first()
		date = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ds_text)
		date = date.group()

		source = re.findall(r'来源：([\u4e00-\u9fff]*?)\s', ds_text)
		source = source[0].strip()

		url = response.url
		id_num = re.findall(r'contents/(\d*).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Gansu'
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
