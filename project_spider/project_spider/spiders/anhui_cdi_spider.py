import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from scrapy.utils.request import request_fingerprint
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class anhui_cdi(scrapy.Spider):
	"""Scrapes all the posts from the ministry level and county level
	case announcement sections (案件发布) on the Anhui website."""

	name = 'anhui'
	start_urls = [
		'http://www.ahjjjc.gov.cn/sggb/index.html',
		'http://www.ahjjjc.gov.cn/sggb286/index.html',
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

		body = response.body
		body = body.decode('utf-8')

		#section = response.xpath('//div[@class="news_row"]/a/h3/text()').extract_first()

		urls = response.xpath('//dl[@class="clearfix"]/dt/a/@href').extract()

		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
										'deltafetch_key': request_fingerprint(response.request),
										'server': server})

		#get next page url from next page bottom
		next_page = response.xpath('//div[@class="page ov"]/a[text()=">"]/@href').extract_first()
		if next_page is not None:
			yield scrapy.Request(next_page, callback=self.parse)

	def parse_docs(self, response):
		"""Scrapes content from page."""
		
		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h2/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div class="article">(.*?)<div', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
		title = title[0]
		
		text_tag = re.search(r'<div class="article_content" id="content">(.*?)</div>', body, re.S)
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

		ds_tag = re.search(r'<h3 class="clearfix"(.*?)</div>', body, re.S)
		ds_tag = ds_tag.group()
		date_text = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ds_tag)
		date = date_text.group()

		source = response.xpath('//h3[@class="clearfix"]/div/a/text()').extract_first()
		if source is None:
			source = re.findall(r'target="_blank">(.*?)</a>',ds_tag, re.S)
			source = source[0]
			if source is None:
				source = ''
		if len(source) == 1:
			source = re.findall(r'来源：(.*?)&nbsp;',ds_tag, re.S)
			source = source[0]
		
		url = response.url
		id_num = re.findall(r'p/(\d*).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Anhui'
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
