import re
import json
import time
import base64
import socket
import scrapy
from scrapy_splash import SplashRequest
from project_spider.screenshot_format import create_pdf

class screenshot(scrapy.Spider):

    name = 'screenshot'
    
    def start_requests(self):
        url = 'http://www.qhjc.gov.cn/html/2014828/n244415474.html'
        
        # Get IP address
        base_url = re.findall(r'www\.(.*?)/', url)
        try:
            ip_address = socket.gethostbyname(base_url[0])
        except socket.gaierror:
            ip_address = "Unable to obtain IP address"
        
        splash_args = {
            'wait': 3.0,
            'html': 1,
            'png': 1,
            'width': 600,
            'render_all': 1,
            'wait': 3.0,
        }
        yield SplashRequest(url, self.parse_result, endpoint='render.json', 
                            args=splash_args, meta={'ip_address':ip_address})

    def parse_result(self, response):
    
        #png_bytes = base64.b64decode(response.data['png'])
        png_b64 = response.data['png']
        header = 'data:image/png;base64,'
        png_b64 = header + png_b64
        
        time = response.headers.get(b'Date')
        time = time.decode('utf-8')
        
        server = response.headers.get(b'Server')
        server = server.decode('utf-8')
        
        ip_address = response.meta['ip_address']

        url = response.url
        id_num = re.findall(r'/(\d.*?)\.',url)[0]
        base_url = re.findall(r'www\.(.*?).gov', url)[0] + '/'
        filename = re.sub(r'/', '_',base_url + id_num)

        filename = filename + '.pdf'

        title = '中国汉字标题'

        create_pdf(png_b64, url, ip_address, time, server, filename, title)
#
        