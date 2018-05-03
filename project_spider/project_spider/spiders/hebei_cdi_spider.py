import re
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.items import post
from project_spider.screenshot_format import create_pdf


class hebei_cdi(scrapy.Spider):
	"""Scrapes all the posts from both the disciplinary examinations
	(执纪审查) and the disciplinary action (纪律处分) sections of 
	the Hebei CDI website.
	"""


	name = 'hebei'
	start_urls = [
		'http://www.hebcdi.gov.cn/node_122866.htm',
		'http://www.hebcdi.gov.cn/node_124627.htm',
	]

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
		
		# Follow all links for posts.
		urls = response.xpath('//div[@class="feed-item"]/h2/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs, meta={'ip_address': ip_address,
																'server': server})

		# Get next page url from next page button.
		next_page = response.xpath('//div[@id="displaypagenum"]/center/a[text()=">"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)


	def parse_docs(self, response):
		# scrapes content from page
		body = response.body
		body = body.decode('utf-8')

		ip_address = response.meta['ip_address']
		server = response.meta['server']

		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<h1>(.*?)</h1>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)
		title = title[0]

		# Pull all tag values. 
		text_tag = re.search(r'<div class="min_content">(.*?)<!--/enpcontent', body, re.S)
		text_tag = text_tag.group()
		excess_text = re.findall(r'<div class="min_content">(.*?)/enpproperty-->', text_tag, re.S)
		text_tag = re.sub(excess_text[0], '', text_tag)
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			num_check = re.search(r'[0-9]', item)
			if han_check or num_check is not None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?', '', item)
				text.append(clean_string)
		text = ' '.join(text)

		sd_tag = re.search(r'<div class="min_cc">(.*?)</div>', body, re.S)
		sd_tag = sd_tag.group()
		sd_text = re.findall(r'>(.*?)<',sd_tag, re.S)
		source = sd_text[3]
		date = sd_text[5]

		url = response.url
		id_num = re.findall(r'cn/(.*?).htm', url)[0]
		base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
		base_url = re.sub(r'\.', '_', base_url)
		filename = re.sub(r'/', '_', base_url + id_num) + '.pdf'
		screenshot_url = 'https://s3.amazonaws.com/tigersandflies/screenshot_pdfs/' + filename

		# Put scraped data into item pipeline.
		item = post()
		item['cdi'] = 'Hebei'
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