import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class guizhou_cdi(scrapy.Spider):
	"""Scrapes all the documents from the examinations and investigations
	section (审查调查) of the Guizhou CDI website.
	"""

	name = 'guizhou'
	start_urls = [
		'http://www.gzdis.gov.cn/gzdt/jlsc/',
	]  

	def parse(self, response):
		"""Find and pass all links for posts listed on one 
		bulletin directory page to parser.
		"""
		# Get IP address.
		url = response.url
		base_url = re.findall(r'www\.(.*?)/', url)
		ip_address = socket.gethostbyname(base_url[0])

		server = response.headers.get(b'Server')
		if server is None:
			server = 'Unable to obtain server information'
		else:
			server = server.decode('utf-8')

		# Pull raw text with post url from script.
		post_urls = response.xpath('//ul[@class="list01"]/li/dl/dd/script/text()').extract()

		# Loop through script to extract url.  Then pass to parser. 
		for raw_string in post_urls:
			url = re.findall(r'var  str="(.*?)"', raw_string)
			if url == ['']:
				url = re.findall(r'var str_1 = "(.*?)"', raw_string)
				url = url[0]
			else:
				url = url[0]
			yield response.follow(url, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Extract total number of pages from pagination script.
		total_pages = response.xpath('//div[@class="page"]/script/text()').extract_first()
		total_pages = re.findall(r'createPageHTML\((\d*),', total_pages)
		total_pages = int(total_pages[0])

		for page in range(1,total_pages):
			next_page = 'http://www.gzdis.gov.cn/gzdt/jlsc/index_{}.html'.format(page)
			yield scrapy.Request(next_page, callback=self.parse)
		
	def parse_docs(self, response):
		"""Scrapes content from post page."""

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		body = response.body
		body = body.decode('utf-8')

		# Get all html that contains title, source, and date.
		tds_tag = re.search(r'<div class="btnr"(.*?)<div class="dy"', body, re.S)
		tds_tag = tds_tag.group()
		tds_tag = re.findall(r'>.*?(\d*?[\u4e00-\u9fff].*?)<',tds_tag, re.S)

		title = tds_tag[0]
		source = tds_tag[1]
		source = re.sub(r'[信息来源：]', '', source).strip()
		date = tds_tag[2]
		date = re.sub(r'[发布时间：]', '', date).strip()

		# Pull all tag values. 
		text_tag = re.search(r'<div class="wz" id="textBox"(.*?)</div>', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check is not None:
				clean_sting = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?', '', item)
				text.append(clean_sting)
		text = ' '.join(text)

		url = response.url
		id_num = re.findall(r'/t(.*?).html', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Guizhou'
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
                        		'server': server,
                        		'proxy': 'http://pattersoncharlesl:KUtKehiWcRcorGgM2@us-wa.proxymesh.com:31280'})

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