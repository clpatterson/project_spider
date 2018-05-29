import re
import socket
import json
from pkgutil import get_data
import scrapy
from scrapy_splash import SplashRequest
from scrapy.utils.request import request_fingerprint
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class hainan_cdi(scrapy.Spider):
	"""Scrapes all the documents from the anti-corruption bulletin
	 section (反腐快报) of the Guangdong CDI website.
	 """

	name = 'test_hainan'
	start_urls = [
		'http://www.hnlzw.net/jlsc_sggb.php?ncount=8&nbegin=0',
		'http://www.hnlzw.net/djcf_sggb.php',
		'http://www.hnlzw.net/jlsc_sxgb.php',
		'http://www.hnlzw.net/djcf_sxgb.php',
	]
	lua_source = get_data(
		'project_spider', 'scripts/crawlera.lua'
		).decode('utf-8')

	def parse(self,response):
		"""Finds and requests all posts to be parsed."""

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		try:
			ip_address = socket.gethostbyname(base_url[0])
		except socket.gaierror:
			ip_address = "Unable to obtain IP address"

		server = response.headers.get(b'Server')
		if server is None:
			server = 'Unable to obtain server information'
		server = server.decode('utf-8')

		# Gets post urls.
		urls = response.xpath('//div[@id="mainrconlist"]/ul/li/h1/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
										'deltafetch_key': request_fingerprint(response.request),
										'server': server})

		# Get total number of records.
		final_page = response.xpath('//div[@id="pages"]/a[text()="末页"]/@href').extract_first()
		total_records = re.findall(r'begin=(\d*)', final_page)
		total_records = int(total_records[0])

		# Get section from url.
		section_url = re.findall(r'net/(.*?).php', url)[0]
		
		# Generate next page urls.
		for page in range(8,total_records+1,8):
			next_page = 'http://www.hnlzw.net/{}.php?ncount=8&nbegin={}'.format(section_url, page)
			yield scrapy.Request(next_page, callback=self.parse)


			
	def parse_docs(self, response):
		"""Scrapes content from page."""
		
		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('gbk')

		title = response.xpath('//div[@id="arttitl"]/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div id="arttitl"(.*?)</div>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>.*?(\d*?[\u4e00-\u9fff].*?)<',title_tag, re.S)
		title = title[0]
		
		text_tag = re.search(r'<div id="artcon"(.*?)<!--', body, re.S)
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

		ds_tag = str(response.xpath('//div[@id="artdes"]/text()').extract())
		date_text = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ds_tag)
		date = date_text.group()

		source = re.findall(r'来源：([\u4e00-\u9fff].*?)\s', ds_tag)
		if source == []:
			source = ''
		else:
			source = source[0]

		url = response.url
		id_num = re.findall(r'xuh=(\d*)', url)[0]
		base_url = re.findall(r'www\.(.*?).net', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Hainan'
		item['title'] = title
		item['date'] = date
		item['source'] = source
		item['text'] = text
		item['url'] = response.url
		item['screenshot_url'] = screenshot_url

		yield item

		# Pass url to splash for screenshoting
		yield SplashRequest(response.url,
					self.create_screenshot,
					endpoint='execute',
					args={'lua_source':hainan_cdi.lua_source,
						'crawlera_user':self.settings['CRAWLERA_APIKEY']},
					cache_args=['lua_source'],
					meta={'dont_proxy': True,
						'ip_address': ip_address,
                        			'title': title,
                        			'filename': filename,
                        			'server': server})

	def create_screenshot(self, response):

		png_json = json.loads(response.body)
		png_b64 = png_json['png']
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
