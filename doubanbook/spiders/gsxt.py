# -*- coding: utf-8 -*-
# import scrapy
from scrapy import Request
from scrapy.spiders import Spider
from scrapy.selector import Selector
from doubanbook.items import CompanyDivItem
import sys
from urllib import quote


class GsxtSpider(Spider):
    name = 'gsxt'
    allowed_domains = ['gsxt.gov.cn']
    start_urls = [
        'http://www.gsxt.gov.cn/index.html?query=恒大',
        # 'http://www.gsxt.gov.cn/index.html?query=富力',
    ]

    def parse(self, response):
        print response.body
        print response.url
        # print 20 * '-'
        print 'begin parse'
        selector = Selector(response)
        for company_item in selector.css('a.search_list_item.db'):
            company_item_href = 'http://www.' + \
                self.allowed_domains[0] + \
                company_item.xpath('@href').extract_first()
            # print company_item_href
            yield Request(company_item_href, callback=self.parse_company_item)

        url_parameter = {
            'geetest_seccode': None,
            'tab': None,
            'geetest_validate': None,
            'searchword': None,
            'geetest_challenge': None,
            'token': None,
            'page': None
        }

        # cookies = {
        #     '__jsluid': '290854c3973c2113e198d9c9b48b7911',
        #     'UM_distinctid': '15d39b853b20-010e33a36ddaa4-38750f56-1fa400-15d39b853b378e',
        #     'Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa': '1499912087',
        #     'tlb_cookie': '46query_8080',
        #     'CNZZDATA1261033118': '1104089608-1499909272-%7C1500087472',
        #     'Hm_lvt_cdb4bc83287f8c1282df45ed61c4eac9': '1499931098,1499932630,1499932635,1500082199',
        #     'Hm_lpvt_cdb4bc83287f8c1282df45ed61c4eac9': '1500090408',
        #     'JSESSIONID': 'C164E69B2E34A6CC4992225241F0AE40-n2:0',
        # }
        reload(sys)
        sys.setdefaultencoding('utf-8')

        # print '打印：' + selector.xpath('//form[@name="qPagerForm"]/a[last()-1]/text()').extract_first()

        if selector.xpath(
                '//form[@name="qPagerForm"]/a[last()-1]/text()')\
                .extract_first() == '下一页':
            xpath_pat = '//form[@name="qPagerForm"]/input[@name="%s"]/@value'
            next_page_url_pat =\
                'http://www.gsxt.gov.cn/corp-query-search-%s.html'
            for (key, val) in url_parameter.items():
                url_parameter[key] = selector.xpath(
                    xpath_pat % key).extract_first()
                if key == 'page':
                    url_parameter[key] = str(int(url_parameter[key]) + 1)

            next_page_url = next_page_url_pat % (url_parameter['page']) + '?'
            for (key, val) in url_parameter.items():
                next_page_url += (key + '=' + quote(str(val))) + '&'
            next_page_url = next_page_url.rstrip('&')
            print '跳转到下一页：' + next_page_url
            yield Request(next_page_url, callback=self.parse)  # 被重定向至首页
        else:
            print '没有下一页'

    def parse_company_item(self, response):
        selector = Selector(response)
        item = CompanyDivItem()
        item['company_detail_div'] = selector.xpath(
            '//div[@class="companyDetail clearfix"]//text()').extract()
        item['details_div'] = selector.xpath(
            '//div[@class="details clearfix"]//text()').extract()
        # print item['company_detail_div']
        # print item['details_div']
        # yield item
        print selector.xpath(
            '//div[@class="companyName"]/h1[@class="fullName"]/text()')\
            .extract_first().strip()
        pass
