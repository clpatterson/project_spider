import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class qinghai_cdi(scrapy.Spider):
	"""Scrape all the documents from the discipline examination
	section (纪律审查) of the Qinghai CDI website.
	"""

	name = 'qinghai'
	start_urls = ['http://www.qhjc.gov.cn/html/ajcc/index.html', ]

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
		urls = response.xpath('//tr/td/li/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_post, meta={'ip_address': ip_address, 'server': server})

		# Get next page url from next page bottom
		next_page = response.xpath('//div[@class="t14 tred1"]/a[text()="下一页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)
			
	def parse_post(self, response):

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('gbk')

		title = response.xpath('//div[@class="xl_tit1 tblack1"]/text()').re(r'[\u4e00-\u9fff].*')
		title = title[0]
		#if title == []:
		#	title_tag = re.search(r'<h3 class="article">(.*?)</h3>', body, re.S)
		#	title_tag = title_tag.group()
		#	title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)

		text_tag = re.search(r'<div class="xl_con1">(.*?)<div class="bot twhite1"', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<', text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			num_check = re.search(r'[0-9]', item)
			if han_check or num_check is not None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_string)

		text = ' '.join(text)

		ds_tag = response.xpath('//div[@class="xl_tit2"]/text()').extract()
		ds_tag = ds_tag[0]
		date = re.search(r'(\d{4})-?/*?(\d{1,2})-?/*?(\d{1,2})', ds_tag)
		date = date.group().strip()

		source = re.findall(r'来源：\s?([\u4e00-\u9fff]+)', ds_tag)
		source = source[0].strip()

		url = response.url
		id_num = re.findall(r'/(\d.*?)\.', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Qinghai'
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

		server = response.meta['server']

		ip_address = response.meta['ip_address']

		url = response.url

		filename = response.meta['filename']

		title = response.meta['title']

		create_pdf(png_b64, url, ip_address, time, server, filename, title)
		
