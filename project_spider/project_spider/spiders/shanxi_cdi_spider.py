import re
import scrapy

class shanxi_cdi(scrapy.Spider):
	"""Scrapes all the posts from examination and investigations
	section (审查调查) of the Shanxi CDI website.
	 """

	name = 'shanxi'
	start_urls = [
		'http://www.sxdi.gov.cn/gzdt/jlsc/',
	]


	def parse(self,response):
		"""Finds and requests all posts to be parsed."""

		# Follow all links for posts listed on one 
		# directory page.
		urls = response.xpath('//a[@class="overflow fl"]/@href').extract()
		for href in urls:
			yield response.follow(href, self.parse_docs)

		#get next page url from next page bottom
		next_page = response.xpath('//a[text()="下一页"]/@href').extract_first()
		if next_page is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)


			
	def parse_docs(self, response):
		"""Scrapes content from page."""
		
		body = response.body
		body = body.decode('utf-8')

		title = response.xpath('//h1/text()').re(r'[\u4e00-\u9fff].*')
		#if title == []:
		#	title_tag = re.search(r'<h1 class="fl">(.*?)</h1>', body, re.S)
		#	title_tag = title_tag.group()
		#	title = re.findall(r'>([\u4e00-\u9fff].*?)<',title_tag)

		text_tag = re.search(r'<dd>(.*?)</dl>', body, re.S)
		text_tag = text_tag.group()
		tag_values = re.findall(r'>[^>]*<',text_tag)
		
		# Find Chinese text and clean.
		text = []
		for item in tag_values:
			han_check = re.search(r'[\u4e00-\u9fff]', item)
			if han_check != None:
				clean_string = re.sub(r'[\u3000]?[\r]?[\n]?[\t]?[>]?[<]?[\xa0]?[&nbsp;]?', '', item)
				clean_string = clean_string.strip()
				text.append(clean_string)

		ds_text = response.xpath('//p[@class="fl"]/span/text()').extract_first()
		date = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ds_text)
		date = date.group()

		source = re.findall(r'来源：([\u4e00-\u9fff].*?)\s', ds_text)
		source = source[0].strip()

		yield{
			'url': response.url,
			'title': title,
			'date': date,
			'source': source,
			'text': text,
		}