from setuptools import setup, find_packages

setup(
    name = 'project_spider',
    version = '0.9',
    packages = find_packages(),
    package_data = {'project_spider': ['scripts/*.lua',]},
    entry_points = {'scrapy': ['settings = project_spider.settings']},
)
