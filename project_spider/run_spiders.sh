#!bin/bash
source /home/ec2-user/venv/python36/bin/activate
sudo docker run -d -p 8050:8050 -p 5023:5023 scrapinghub/splash
scrapy crawl anwei
scrapy crawl ccdi
scrapy crawl chongqing
scrapy crawl fujian
scrapy crawl gansu
scrapy crawl guangdong
scrapy crawl guangxi
scrapy crawl guizhou
scrapy crawl hainan
scrapy crawl hebei
scrapy crawl heilongjiang
scrapy crawl henan
scrapy crawl hubei
scrapy crawl jiangsu
#scrapy crawl jiangxi
scrapy crawl liapning
scrapy crawl neimenggu
scrapy crawl ningxia
scrapy crawl qinghai
scrapy crawl shandong
scrapy crawl shanghai
#scrapy crawl shanxi
scrapy crawl sichuan
scrapy crawl tianjin
scrapy crawl xinjiang
scrapy crawl xizang
scrapy crawl yunnan
#scrapy crawl zhejiang
sudo docker rm $(sudo docker stop $(sudo docker ps -a -q --filter ancestor=scrapinghub/splash --format="{{.ID}}"))
