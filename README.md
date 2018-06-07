# Project_spider

Project spider is a data aggregation tool built to support the Asia Society's [Catching Tigers and Flies](http://www.chinafile.com/infographics/visualizing-chinas-anti-corruption-campaign) project.
Built primarily with the [Scrapy](https://github.com/scrapy/scrapy) and [Splash](https://github.com/scrapy-plugins/scrapy-splash) web scraping frameworks, project_spider scrapes and aggregates publicly available corruption reports from 26 provincial and central government sites.
Corruption report data is stored in a PostgreSQL Amazon RDS instance and legal grade screenshots containing meta-data are stored as pdfs in S3. Scrapers are deployed on an Ec2 instance and scheduled to run every 72 hrs. 

The rotating IP Proxy solution [Proxymesh](https://proxymesh.com/) is used to avoid banning and Scrapy plugin [Delta-fetch](https://github.com/scrapy-plugins/scrapy-deltafetch) eliminates redundant crawling.

## Deployment

Deployed on T2 micro Ec2 Amazon Linux AMI.

## Versioning

Currently in Beta

## Authors

Charlie Patterson

