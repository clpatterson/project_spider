import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class ccdi_scraper(scrapy.Spider):
	"""Scrapes all the documents from the investigations section (审查调查) of the CCDI website."""
	name = 'ccdi'
	start_urls = ['http://www.ccdi.gov.cn/scdc/',]

	def parse(self, response):
		# Follow links to 6 subdirectories for state and party investigations for the 3 government levels
		urls = response.xpath('//div[@class="title_3"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_doclist)

	def parse_doclist(self,response):

		body = response.body
		body = body.decode('utf-8')

		# Get IP address
		url = response.url
		base_url = re.findall(r'http://(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = 'Unable to obtain IP address'

		# Follow links for 20 documents listed on a subdirectory page
		urls = response.xpath('//ul[@class="list_news_dl fixed"]/li/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address})

		total_pages = re.findall(r'createPageHTML\((\d+?),', body)
		total_pages = int(total_pages[0])

		# Create pagination links and follow them until no pages are left
		for x in range(1,total_pages + 1):
			nextpage = 'index_{}.html'.format(x)
			yield response.follow(nextpage, callback=self.parse_doclist)
			
	def parse_docs(self, response):
		"""Scrapes content from page."""

		ip_address = response.meta['ip_address']

		server = response.headers.get(b'Server')
		if server is None:
			server = 'Unable to obtain server information'
		server = server.decode('utf-8')
		
		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h2/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<h2 class="tit">(.*?)</h2>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
		title = title[0]

		text_tag = re.search(r'<div class="content">(.*?)<div class="clear', body, re.S)
		text_tag = text_tag.group()
		text = re.findall(r'>[\u3000]*(\d*?[\u4e00-\u9fff].*?)<',text_tag)

		#tag_values = re.findall(r'>[^>]*<',text_tag)
		
		## Find Chinese text and clean.
		#text = []
		#for item in tag_values:
		#	han_check = re.search(r'[\u4e00-\u9fff]', item)
		#	num_check = re.search(r'[0-9]', item)
		#	if han_check or num_check is not None:
		#		clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', item)
		#		clean_string = clean_string.strip()
		#		text.append(clean_string)
		text = ' '.join(text)

		date = response.xpath('//div[@class="daty_con"]/em[@class="e e2"]/text()').extract()
		date = re.search(r'(\d{4})-?/*?(\d{1,2})-?/*?(\d{1,2})', date[0])
		date = date.group().strip()

		source = response.xpath('//div[@class="daty_con"]/em[@class="e e1"]/text()').extract()
		source = re.findall(r'来源：([\u4e00-\u9fff]+)', source[0])
		source = source[0]

		url = response.url
		id_num = re.findall(r'scdc/(.*?).html', url)[0]
		base_url = re.findall(r'www.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'CCDI'
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

		#One possible solution for finding titles, but it eleminates punctuation
		#title = re.search(r'<h2 class="tit">(.*?)</h2>', body, re.S)
		#clean = re.compile(u'[^\u4E00-\u9FA5]')
		#title = clean.sub(r'', title)
