import scrapy
import re

class ccdi_scraper(scrapy.Spider):
	"""Scrapes all the documents from the investigations section (审查调查) of the CCDI website."""
	name = 'ccdi'
	start_urls = ['http://www.ccdi.gov.cn/scdc/',]

	def parse(self, response):
		#follow links to 6 subdirectories for state and party investigations for the 3 government levels
		urls = response.xpath('//div[@class="title_3"]/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_doclist)  


	def parse_doclist(self,response):
		#follow links for 20 documents listed on a subdirectory page
		urls = response.xpath('//ul[@class="list_news_dl fixed"]/li/a/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs)

		#create pagination links and follow them until no pages are left
		for x in range(1,50):
			nextpage = 'index_{}.html'.format(x)
			yield response.follow(nextpage, callback=self.parse_doclist)
			
	def parse_docs(self, response):
		#scrapes content from page
		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h2/text()').re(r'[\u4e00-\u9fff].*')
		if title == []:
			title_tag = re.search(r'<h2 class="tit">(.*?)</h2>', body, re.S)
			title_tag = title_tag.group()
			title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)

		text_tag = re.search(r'<div class="TRS_Editor">(.*?)</div>', body, re.S)
		text_tag = text_tag.group()
		text = re.findall(r'>[\u3000]*(\d*?[\u4e00-\u9fff].*?)<',text_tag)


		yield{
			'url': response.url,
			'title': title,
			'date': response.xpath('//em[@class="e e2"]/text()').re(r'发布.*'),
			'source': response.xpath('//em[@class="e e1"]/text()').re(r'来源.*'),
			'text': text,
		}


		#One possible solution for finding titles, but it eleminates punctuation
		#title = re.search(r'<h2 class="tit">(.*?)</h2>', body, re.S)
		#clean = re.compile(u'[^\u4E00-\u9FA5]')
		#title = clean.sub(r'', title)








