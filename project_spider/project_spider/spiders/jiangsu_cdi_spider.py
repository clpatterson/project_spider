import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from scrapy.utils.request import request_fingerprint
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class jiangsu_cdi(scrapy.Spider):
	"""Scrapes all the documents from the examinations and investigations
	section (审查调查) of the Jiangsu CDI website.
	"""

	name = 'jiangsu'
	start_urls = [
		'http://www.qfyf.net/col/col17/index.html',
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

		server = 'Apache/2.4.25 (Unix)'
		
		# Get urls for all post on directory page.
		urls = response.xpath('//div[@class="simple_pgContainer"]/ul/li/a/@href').extract()
		for href in urls:
			href = response.urljoin(href)
			yield SplashRequest(href, self.parse_docs, endpoint='render.html',
				args={'wait': 3.0},
				meta={'ip_address': ip_address,
						'deltafetch_key': request_fingerprint(response.request),
						'server': server}
		)

		# Get next page url from next page bottom.
		next_page = response.xpath('//a[@title="下页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield SplashRequest(next_page, self.parse, endpoint='render.html',
				args={'wait': 5.0},
			)
	
	def parse_docs(self, response):
		"""Scrapes content from page."""

		body = response.body
		body = body.decode('utf-8')

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		title = title[0]
		#if title == []:
		#	title_tag = re.search(r'<h3 class="article">(.*?)</h3>', body, re.S)
		#	title_tag = title_tag.group()
		#	title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)

		text_tag = re.search(r'<meta name="ContentStart">(.*?)<meta name="ContentEnd">', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)

		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			num_check = re.search(r'[0-9]', item)
			if han_check or num_check != None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?', '', item)
				text.append(clean_string)
		text = ' '.join(text)

		ds_tag = response.xpath('//div[@class="c-conten-top"]/p/i/text()').extract()
		date = re.search(r'(\d{4})-(\d{2})-(\d{2})', ds_tag[0])
		date = date.group()

		source = ds_tag[4]

		url = response.url
		id_num = re.findall(r'art/(.*?).html', url)[0]
		base_url = re.findall(r'www\.(.*?).net', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Jiangsu'
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
