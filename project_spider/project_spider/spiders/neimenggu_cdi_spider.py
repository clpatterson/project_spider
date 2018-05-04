import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class neimenggu_cdi(scrapy.Spider):
	"""Scrapes all the documents from the disciplinary examinations
	 section (执纪审查) of the Inner Mongolia/Neimenggu CDI website.
	 """


	name = 'neimenggu'
	start_urls = ['http://www.nmgjjjc.gov.cn/ajcc/',]

	def parse(self,response):
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

		body = response.body
		body = body.decode('utf-8')

		# Get and follow all other post urls.
		urls = response.xpath('//div[@class="zMain_con"]/div/h2/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Extract total number of pages from pagination script.
		total_pages = re.findall(r'\|ele.value>(\d*)\)\{alert\(\'错误的页码\'\)', body)
		total_pages = int(total_pages[0])

		# Loop through range for pages and create url and request.  
		for page in range(2,total_pages + 1):
			next_page = 'http://www.nmgjjjc.gov.cn/ajcc/index_{}.shtml'.format(page)
			yield scrapy.Request(next_page, callback=self.parse)
	
	def parse_docs(self, response):
		"""Scrapes content from page"""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		# Get title by plan a or b.
		title = response.xpath('//h2/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div class="detail_tit">(.*?)<em class="time"', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
		title = title[0]

		# Get all text and tags within the body section of the post.
		text_tag = re.search(r'<div class="detail_con">(.*?)<div class="detail_con"', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check != None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', item)
				clean_string = clean_string.strip()
				text.append(clean_string)
		text = ' '.join(text)

		# Get date and source.
		source= response.xpath('//div[@class="detail_tit"]/span/text()').re(r'来源：([\u4e00-\u9fff]+)')
		source = re.sub(r'[来源：]', '', source[0])
		source = source.strip()
		
		date = response.xpath('//div[@class="detail_tit"]/em/text()').extract()
		date = re.search(r'(\d{4})-(\d{2})-(\d{2})\s?(\d{2})?:?(\d{2})?', date[0])
		date = date.group()

		url = response.url
		id_num = re.findall(r'ajcc/(\d*).shtml', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Neimenggu'
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