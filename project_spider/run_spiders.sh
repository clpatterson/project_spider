
#!bin/bash
source /home/ec2-user/venv/python36/bin/activate
sudo docker run -d -p 8050:8050 -p 5023:5023 scrapinghub/splash --max-timeout 3600
scrapy crawl anhui > /logs/anhui_spider.log
scrapy crawl ccdi > /logs/ccdi_spider.log
scrapy crawl chongqing > /logs/chongqing_spider.log
scrapy crawl fujian > /logs/fujian_spider.log
scrapy crawl gansu > /logs/gansu_spider.log
scrapy crawl guangdong > /logs/guangdong_spider.log
scrapy crawl guangxi > /logs/guangxi_spider.log
scrapy crawl guizhou > /logs/guizhou_spider.log
scrapy crawl hainan > /logs/hainan_spider.log
scrapy crawl hebei > /logs/hebei_spider.log
scrapy crawl heilongjiang > /logs/heilongjiang_spider.log
scrapy crawl henan > /logs/henan_spider.log
scrapy crawl hubei > /logs/hubei_spider.log
scrapy crawl jiangsu > /logs/jiangsu_spider.log
#scrapy crawl jiangxi > /logs/jiangxi_spider.log
scrapy crawl liaoning > /logs/liaoning_spider.log
scrapy crawl neimenggu > /logs/neimenggu_spider.log
scrapy crawl ningxia > /logs/ningxia_spider.log
scrapy crawl qinghai > /logs/qinghai_spider.log
scrapy crawl shandong > /logs/shandong_spider.log
scrapy crawl shanghai > /logs/shanghai_spider.log
#scrapy crawl shanxi > /logs/shanxi_spider.log
scrapy crawl sichuan > /logs/sichuan_spider.log
scrapy crawl tianjin > /logs/tianjin_spider.log
scrapy crawl xinjiang > /logs/xinjiang_spider.log
scrapy crawl xizang > /logs/xizang_spider.log
scrapy crawl yunnan > /logs/yunnan_spider.log
scrapy crawl zhejiang > /logs/zhejiang_spider.log
sudo docker rm $(sudo docker stop $(sudo docker ps -a -q --filter ancestor=scrapinghub/splash --format="{{.ID}}"))
deactivate
