
#!bin/bash
cd /home/ec2-user/project_spider/project_spider
source /home/ec2-user/venv/python36/bin/activate
sudo docker run -d -p 8050:8050 -p 5023:5023 scrapinghub/splash --max-timeout 3600
scrapy crawl anhui --logfile /home/ec2-user/project_spider/project_spider/logs/anhui_spider.log
scrapy crawl ccdi --logfile /home/ec2-user/project_spider/project_spider/logs/ccdi_spider.log
scrapy crawl chongqing --logfile /home/ec2-user/project_spider/project_spider/logs/chongqing_spider.log
# Fujian is down b/c site blocks requests from Ec2 server
#scrapy crawl fujian --logfile /home/ec2-user/project_spider/project_spider/logs/fujian_spider.log
scrapy crawl gansu --logfile /home/ec2-user/project_spider/project_spider/logs/gansu_spider.log
scrapy crawl guangdong --logfile /home/ec2-user/project_spider/project_spider/logs/guangdong_spider.log
scrapy crawl guangxi --logfile /home/ec2-user/project_spider/project_spider/logs/guangxi_spider.log
scrapy crawl guizhou --logfile /home/ec2-user/project_spider/project_spider/logs/guizhou_spider.log
# Hainan is down b/c site blocks requests from Ec2 server
#scrapy crawl hainan --logfile /home/ec2-user/project_spider/project_spider/logs/hainan_spider.log
scrapy crawl hebei --logfile /home/ec2-user/project_spider/project_spider/logs/hebei_spider.log
scrapy crawl heilongjiang --logfile /home/ec2-user/project_spider/project_spider/logs/heilongjiang_spider.log
scrapy crawl henan --logfile /home/ec2-user/project_spider/project_spider/logs/henan_spider.log
scrapy crawl hubei --logfile /home/ec2-user/project_spider/project_spider/logs/hubei_spider.log
scrapy crawl jiangsu --logfile /home/ec2-user/project_spider/project_spider/logs/jiangsu_spider.log
# Jiangxi site is an unstructured  html mess. Spider returns inconsistenly results.
#scrapy crawl jiangxi --logfile /home/ec2-user/project_spider/project_spider/logs/jiangxi_spider.log
scrapy crawl liaoning --logfile /home/ec2-user/project_spider/project_spider/logs/liaoning_spider.log
scrapy crawl neimenggu --logfile /home/ec2-user/project_spider/project_spider/logs/neimenggu_spider.log
scrapy crawl ningxia --logfile /home/ec2-user/project_spider/project_spider/logs/ningxia_spider.log
scrapy crawl qinghai --logfile /home/ec2-user/project_spider/project_spider/logs/qinghai_spider.log
scrapy crawl shandong --logfile /home/ec2-user/project_spider/project_spider/logs/shandong_spider.log
scrapy crawl shanghai --logfile /home/ec2-user/project_spider/project_spider/logs/shanghai_spider.log
# Shanxi site employs an anit-scraping sheild. 
#scrapy crawl shanxi --logfile /home/ec2-user/project_spider/project_spider/logs/shanxi_spider.log
scrapy crawl sichuan --logfile /home/ec2-user/project_spider/project_spider/logs/sichuan_spider.log
scrapy crawl tianjin --logfile /home/ec2-user/project_spider/project_spider/logs/tianjin_spider.log
scrapy crawl xinjiang --logfile /home/ec2-user/project_spider/project_spider/logs/xinjiang_spider.log
scrapy crawl xizang --logfile /home/ec2-user/project_spider/project_spider/logs/xizang_spider.log
scrapy crawl yunnan --logfile /home/ec2-user/project_spider/project_spider/logs/yunnan_spider.log
scrapy crawl zhejiang --logfile /home/ec2-user/project_spider/project_spider/logs/zhejiang_spider.log
sudo docker rm $(sudo docker stop $(sudo docker ps -a -q --filter ancestor=scrapinghub/splash --format="{{.ID}}"))
deactivate
curl -s --user 'api:ee10595a5c96af57b7b403fa6d9e353d-b892f62e-8a9bdb97' \
    https://api.mailgun.net/v3/sandbox97378fda2ee74f3d9f45adfc69dddc34.mailgun.org/messages \
    -F from='Excited User <mailgun@sandbox97378fda2ee74f3d9f45adfc69dddc34.mailgun.org>' \
    -F to=YOU@sandbox97378fda2ee74f3d9f45adfc69dddc34.mailgun.org \
    -F to=dragonspinetea@gmail.com \
    -F subject='Hello' \
    -F text='Testing some Mailgun awesomeness!'
