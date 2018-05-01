import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class jiangxi_cdi(scrapy.Spider):
	"""Scrapes all the posts from the examination and investigations
	section (审查调查) on the Jiangxi website.
	"""

	name = 'jiangxi'
	start_urls = [
		'http://www.jxlz.gov.cn/jjjcyw/jlsc/',
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
		body = body.decode('gbk')

		# Follow all links for posts listed on one
		#   disciplinary investigations directory page.
		urls = response.xpath('//td[@class="title"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		total_pages = re.findall(r'createPageHTML\((\d*),', body)
		total_pages = int(total_pages[0])

		# Loop through range for pages and create url and request.  
		for page in range(1,total_pages):
			next_page = 'http://www.jxlz.gov.cn/jjjcyw/jlsc/index_{}.htm'.format(page)
			yield scrapy.Request(next_page, callback=self.parse)
	
	def parse_docs(self, response):
		"""Scrapes content from page."""
		
		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('gbk')

		# Disgusting html structure has created this mess.
		title = response.xpath('//h2/text()').extract()
		if title is []:
			title_tag = re.search(r'<div class="Article_61">(.*?)<h3 class="daty"', body, re.S)
			if title_tag is None:
				title_tag = re.search(r'<td style="font-size: 170%;[^<](.*?)</td>',body, re.S)
				title_tag = title_tag.group()
				tag_values = re.findall(r'>[^>]*<',title_tag)
				title = re.sub(r'[>]?[<]?','', tag_values[0])
				title = title.strip()
			elif title_tag is not None:
				title_tag = title_tag.group()
				title = re.findall(r'([\u4e00-\u9fff]+[\u3000-\u303F]+?[\u4e00-\u9fff]+)',title_tag)
				title = title[0]
			else:
				title = re.sub(r'[\n]','', title[0])
				title = title.strip()

		text_tag = re.search(r'(.*?)<div class="clear"', body, re.S)
		if text_tag == None:
			text_tag = re.search(r'<style id=_Custom_V6_Style_>(.*?)<div class="yewei">', body, re.S)
			if text_tag == None:
				tag_values = 0
			else:
				text_tag = text_tag.group()
				
				excess_text= re.findall(r'<style id=_Custom_V6_Style_>[^</style>](.*?)</style>', text_tag, re.S)
				text_tag = re.sub(excess_text[0], '', text_tag)
				tag_values = re.findall(r'>[^>]*<',text_tag)
		else:
			text_tag = text_tag.group()
			tag_values = re.findall(r'>[^>]*<',text_tag)

		# Find Chinese text and clean where possible.
		if tag_values == 0:
			text = 'Unable to scrape this data. Please see screenshot pdf.'
		else:
			text = []
			for item in tag_values:
				han_check = re.search(r'[\u4e00-\u9fff]', item)
				if han_check is not None:
					clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
					clean_string = re.sub(r'[&nbsp;]', ' ', clean_string)
					text.append(clean_string)

		ds_tag = re.search(r'<div class="daty_con">(.*?)<div class="share_box">', body, re.S)
		if ds_tag == None:
			ds_tag = re.search(r'<td align="center" style="padding-top:[^<](.*?)</td>',body, re.S)
			if ds_tag == None:
				ds_tag = 0
		
		if ds_tag == 0:
			date = 'Unable to scrape this data. Please see screenshot pdf.'
		else:
			ds_tag = ds_tag.group()
			date_text = re.search(r'(\d{4})-(\d{2})-(\d{2})', ds_tag)
			date = date_text.group()

		source = re.findall(r'来源：([\u4e00-\u9fff]+)', ds_tag)
		if source == []:
			source = 'Unable to scrape this data. Please see screenshot pdf.'
		source = source[0]

		url = response.url
		id_num = re.findall(r'gplz/(.*?).htm', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Jiangxi'
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
