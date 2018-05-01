import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class chongqing_cdi(scrapy.Spider):
	"""Scrapes all the documents from the examinations and investigations
	section (审查调查) of the Chongqing CDI website.
	"""

	name = 'chongqing'
	start_urls = ['http://jjc.cq.gov.cn/html/node_282706.htm',]

	def parse(self, response):
		"""Finds and requests all posts to be parsed."""

		# Get IP address.
		url = response.url
		base_url = re.findall(r'http://(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = 'Unable to obtain IP address'

		server = response.headers.get(b'Server')
		if server is None:
			server = 'Unable to obtain server information'
		server = server.decode('utf-8')

		# Get and follow all other post urls.
		urls = response.xpath('//div[@id="list"]/ul/li/h1/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		#get next page url from next page bottom
		next_page = response.xpath('//div[@id="displaypagenum"]/center/a[text()="下一页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)

	def parse_docs(self, response):
		"""Scrapes content from page"""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div id="text">(.*?)<div class="ls"', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'([\u4e00-\u9fff]+[\u3001-\u303f]?)',title_tag)
		title = title[0]
		title = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', title)

		# Get all text and tags within the body section of the post.
		text_tag = re.search(r'<div class="nr"(.*?)<div class="bk_b"', body, re.S)
		text_tag = text_tag.group()
		bullshit_text = re.search(r'<p align="justify"(.*?)<!--enpcontent-->', text_tag, re.S)
		bullshit_text = bullshit_text.group()
		text_tag = re.sub(bullshit_text, '', text_tag)
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			num_check = re.search(r'[0-9]', item)
			if han_check or num_check is not None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', item)
				clean_string = clean_string.strip()
				text.append(clean_string)
		text = ' '.join(text)

		# Get date and source.
		ds_tag = re.search(r'<div class="ls">(.*?)<div class="nr"', body, re.S)
		ds_tag = ds_tag.group()
		date_text = re.search(r'(\d{4})-?年?(\d{2})月?-?(\d{2})-?日?\s?(\d{2})?:?(\d{2})?', ds_tag)
		date = date_text.group()
		date = re.sub(r'年|月', '-', date)
		date = re.sub(r'日', '', date)
		date = date.strip()
		
		source = re.findall(r'来源：([\u4e00-\u9fff]+)', ds_tag)
		source = source[0]

		url = response.url
		id_num = re.findall(r'html/(.*?).htm', url)[0]
		base_url = re.findall(r'http://(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Chongqing'
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

