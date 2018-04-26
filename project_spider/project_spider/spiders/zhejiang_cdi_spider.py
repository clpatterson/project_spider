import re
import socket
import requests
import scrapy
from scrapy_splash import SplashRequest
from project_spider.screenshot_format import create_pdf


class zhejiang_cdi(scrapy.Spider):
	"""Scrapes all the documents from the discipline and 
	 inspection section (审查调查) of the Zhejiang CDI website.
	 """

	name = 'zhejiang'
	start_urls = ['http://www.zjsjw.gov.cn/ch112/jlsc/',]

	def parse(self,response):

		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		ip_address = socket.gethostbyname(base_url[0])

		# Follow all links for posts.
		urls = response.xpath('//ul[@class="listUl cf"]/li/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs)

		# Extract total number of pages from pagination script.
		#total_pages = re.findall(r'var maxpage = (\d*);', body)
		#total_pages = int(total_pages[0])
		total_pages = 6

		for page in range(1,total_pages + 1):
			next_page = 'http://www.zjsjw.gov.cn/ch112/system/count//0112003/000000000000/000/000/c0112003000000000000_00000000{}.shtml'.format(page)
			yield scrapy.Request(next_page, callback=self.parse, meta={'ip_address':ip_address})


			
	def parse_docs(self, response):
		"""scrapes content from page"""
		
		body = response.body
		body = body.decode('gbk')

		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<div class="crumb nobd mb25">(.*?)<div class="info"', body, re.S)
			title_tag = title_tag.group()
			title_tag = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
			title = title_tag[3]

		# Pull all tag values. 
		text_tag = re.search(r'<div class="artCon">(.*?)<div class="artSpecial"', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check != None:
				clean_sting = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_sting)

		date_tag = re.search(r'<span id="pubtime_baidu">(.*?)<span id="source_baidu">', body, re.S)
		date_tag = date_tag.group()
	
		date = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2})?:?(\d{2})?:?(\d{2})?', date_tag)
		date = date.group()

		
		source_tag = re.search(r'<span id="source_baidu">(.*?)<span id="author_baidu"', body, re.S)
		source_tag = source_tag.group()
		source = response.xpath('//span[@id="source_baidu"]/text()').re(r'来源：\r\n\r\n([\u4e00-\u9fff]+)')
		if source == []:
			source = re.findall(r'([\u4e00-\u9fff]+)', source_tag)
			if source == ['来源'] or []:
				source = ''
			else:
				source = source[1]
		else:
			source = source[0]
			

		yield{
			'url': response.url,
			'title': title,
			'date': date,
			'source': source,
			'text': text,
		}

#		# Pass url to splash for screenshoting.
#		splash_args = {
#        'wait': 3.0,
#        'html': 1,
#        'png': 1,
#        'width': 600,
#        'render_all': 1,
#        'wait': 3.0,
#    	}
#		yield SplashRequest(response.url, self.create_screenshot, endpoint='render.json', 
#                        args=splash_args, meta={'ip_address':ip_address, 'title': title})
#
#	def create_screenshot(self, response):
#
#		png_b64 = response.data['png']
#		header = 'data:image/png;base64,'
#		png_b64 = header + png_b64
#
#		time = response.headers.get(b'Date')
#		time = time.decode('utf-8')
#        
#		server = response.headers.get(b'Server')
#		server = server.decode('utf-8')
#
#		ip_address = response.meta['ip_address']
#
#		url = response.url
#		id_num = re.findall(r'/(\d.*?)\.',url)
#		id_num = re.sub(r'/', '_',id_num[0])
#
#		filename = id_num + '.pdf'
#
#		title = response.meta['title']
#
#		create_pdf(png_b64, url, ip_address, time, server, filename, title)