# -*- coding: utf-8 -*-
import scrapy
import time
import json
from urllib import urlencode
import re
from twisted.internet import defer, reactor
from doubanbook.libs import slide_challenge
from copy import deepcopy
import random
import sys
from doubanbook.items import CompanyDivItem
from urllib import quote
import hashlib


class GsxtSpiderNewSpider(scrapy.Spider):
    name = 'gsxt_spider_new'
    allowed_domains = ['gsxt.gov.cn']
    start_urls = [
        'http://www.gsxt.gov.cn/index.html?search=恒大',
        'http://www.gsxt.gov.cn/index.html?search=万达',
        'http://www.gsxt.gov.cn/index.html?search=绿城',
    ]
    request_gt_url_pat = 'http://www.gsxt.gov.cn/SearchItemCaptcha?v=%s'
    index_url = 'http://www.gsxt.gov.cn/index.html'
    geetest_url = 'http://api.geetest.com/get.php?'
    crack_url = 'http://119.23.121.156:4067/'
    slide_url = 'http://api.geetest.com/ajax.php?gt={}&challenge={}&userresponse={}&passtime={}&imgload={}&a={}&callback={}'
    search_url = 'http://www.gsxt.gov.cn/corp-query-search-1.html'
    search_words = [
        '恒大',
        '万达',
        '绿城',
        # '440101000348898',
        # '440301800011103',
    ]

    headers = {
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Host': 'www.gsxt.gov.cn',
        'Upgrade-Insecure-Requests': '1',
        # 'Content-Type': 'application/x-www-form-urlencoded',
        # 'Origin': 'http://www.gsxt.gov.cn',
        # 'X-Requested-With': 'XMLHttpRequest',
    }

    def parse(self, response):
        # print response.url
        # print response.body
        # print response.meta['searchword']
        print 'begin parse'
        selector = scrapy.Selector(response)
        meta = deepcopy(response.meta)
        for company_item in selector.css('a.search_list_item.db'):
            company_item_href = 'http://www.' + \
                self.allowed_domains[0] + \
                company_item.xpath('@href').extract_first()
            headers = deepcopy(self.headers)
            headers.update({
                'Referer': response.url,
            })
            yield scrapy.Request(
                url=company_item_href,
                method='GET',
                callback=self.parse_company_item,
                meta=meta,
                headers=headers,
                errback=self.recall_company_content,
                # priority=7,
            )

        url_parameter = {
            'geetest_seccode': None,
            'tab': None,
            'geetest_validate': None,
            'searchword': None,
            'geetest_challenge': None,
            'token': None,
            'page': None
        }

        reload(sys)
        sys.setdefaultencoding('utf-8')

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

            headers = deepcopy(self.headers)
            headers.update({
                'Referer': response.url,
            })
            # next_page_post_url = next_page_url_pat % (url_parameter['page'])
            next_page_url = next_page_url_pat % (url_parameter['page']) + '?'
            for (key, val) in url_parameter.items():
                if key == 'token':  # 该破解过程token为None
                    continue
                next_page_url += (key + '=' + quote(str(val))) + '&'
            next_page_url = next_page_url.rstrip('&')
            print '跳转到下一页：' + next_page_url
            yield scrapy.Request(
                method='GET',
                url=next_page_url,
                callback=self.parse,
                headers=headers,
                meta=meta,
                errback=self.recall_company_content,
                # priority=6,
            )

        else:
            print '没有下一页'

        pass

    def recall_company_content(self, failure):
        print 'reason for failure is ', repr(failure)
        print 'begin recall_company_content'
        request = failure.request.copy()
        yield request
        # meta = deepcopy(request.meta)
        # meta.update({
        #     'change_proxy': True,
        # })
        # print 'change ip url is ', request.url
        # yield scrapy.Request(
        #     url=request.url,
        #     method='GET',
        #     callback=self.parse_company_item,
        #     priority=7,
        #     meta=meta,
        #     errback=self.recall_company_content,
        # )

    def recall_search_and_slide(self, failure):
        print 'season for failure is ', repr(failure)
        print 'begin recall_search_and_slide'
        request = failure.request
        meta = deepcopy(request.meta)
        meta.update({
            'change_proxy': True,
        })
        v = self._get_timestamp()
        request = scrapy.Request(
            url=self.request_gt_url_pat % v,
            meta=meta,
            dont_filter=True,
            callback=self.get_gt_challenge,
            method='GET',
            headers=self.headers,
            # priority=2,
        )
        yield request

    def parse_company_item(self, response):
        print 'begin parse_company_item'
        try:
            selector = scrapy.Selector(response)
            item = CompanyDivItem()
            item['company_detail_div'] = selector.xpath(
                '//div[@class="companyDetail clearfix"]//text()').extract()
            item['details_div'] = selector.xpath(
                '//div[@class="details clearfix"]//text()').extract()
            print item['company_detail_div']
            print item['details_div']
            yield item
            print selector.xpath(
                '//div[@class="companyName"]/h1[@class="fullName"]/text()')\
                .extract_first().strip()
        except Exception as e:
            print 'error: ', e
        pass

    # def start_requests(self):
    #     print 'begin start_requests'
    #     requests = []
    #     for i, searchword in enumerate(self.search_words):
    #         print 'search ', searchword, i
    #         print hashlib.md5(searchword).hexdigest()
    #         request = scrapy.Request(
    #             url=self.index_url,
    #             callback=self.search_and_slide,
    #             method='GET',
    #             headers=self.headers,
    #             dont_filter=True,
    #             meta={
    #                 'searchword': searchword,
    #                 'autoproxy': True,  # 开启中间件的IP代理服务
    #                 'cookiejar': hashlib.md5(searchword).hexdigest(),
    #             },
    #             priority=1,
    #         )
    #         requests.append(request)
    #         # yield request
    #     return requests

    def make_requests_from_url(self, url):
        print 'begin make_requests_from_url ', url
        searchword = url.split('?')[1].split('=')[1]
        print searchword
        return scrapy.Request(
            url=self.index_url,
            callback=self.search_and_slide,
            method='GET',
            headers=self.headers,
            dont_filter=True,
            meta={
                'searchword': searchword,
                'autoproxy': True,  # 开启中间件的IP代理服务
                'cookiejar': hashlib.md5(searchword).hexdigest(),
            },
            # priority=1,
        )

    def search_and_slide(self, response):
        print 'begin search_and_slide'
        meta = deepcopy(response.meta)
        if 'try_again' in meta and meta['try_again']:
            meta.update({
                'change_proxy': True,
            })
            del meta['try_again']
        # else:
            # meta.update({
            #     'cookiejar': hashlib.md5(meta['searchword']).hexdigest()
            # })

        v = self._get_timestamp()
        # print 'url one is ' + self.request_gt_url_pat % v
        request = scrapy.Request(
            url=self.request_gt_url_pat % v,
            meta=meta,
            dont_filter=True,
            callback=self.get_gt_challenge,
            method='GET',
            headers=self.headers,
            # priority=2,
        )
        # print 20 * '*-'
        # print request.body
        yield request
        pass

    def _get_timestamp(self):
        t = int(round(time.time() * 1000))
        return str(t)

    def get_gt_challenge(self, response):
        print 'begin get_gt_challenge'
        data = json.loads(response.body)
        gt = data['gt']
        challenge = data['challenge']
        request = scrapy.Request(
            method='GET',
            url=self.geetest_url + urlencode({
                'gt': gt,
                'challenge': challenge,
                'product': 'popup',
                'offline': 'false',
                'type': 'slide',
                'path': '/static/js/geetest.5.10.10.js',
                'protocol': '',
                'callback': 'geetest_' +
                str(int(time.time() * 1000 + 1e4 * random.random())),
            }),
            meta=deepcopy(response.meta),
            headers={
                'Referer': self.index_url,
            },
            dont_filter=True,  # dont deduplicat it
            # priority=3,
            callback=self.handle_gt_challenge,
            errback=self.recall_search_and_slide
        )
        yield request

    def handle_gt_challenge(self, response):
        pass
        print 'begin handle_gt_challenge'
        match = re.match('^geetest_\d+\((.*)\)$',
                         response.text.strip())  # 正则获取body中的json内容
        data = json.loads(match.group(1))  # json
        gt = data['gt']
        challenge = data['challenge']
        bg = data['bg']
        fullbg = data['fullbg']
        slice_img = data['slice']
        xpos = data['xpos']
        ypos = data['ypos']
        host = 'http://' + data['static_servers'][0]
        meta = deepcopy(response.meta)
        meta.update({           # 传递参数
            'gt': gt,
            'challenge': challenge,
            'slide_start_time': time.time() * 1000,
        })
        yield scrapy.FormRequest(
            method='POST',
            url=self.crack_url + 'api/model/slide',
            meta=meta,
            formdata={
                'originUrl': host + fullbg,
                'shadowUrl': host + bg,
                'chunkUrl': host + slice_img,
                'left': str(xpos),
                'top': str(ypos)
            },
            dont_filter=True,
            # priority=4,
            callback=self.slide_crack,
            errback=self.recall_search_and_slide
        )

    def slide_crack(self, response):
        print 'begin slide_crack'
        d = defer.Deferred()    # 装载阻塞/延迟操作
        data = json.loads(response.body)
        pos_arr = data['trail']
        passtime = pos_arr[-1][-1]
        meta = response.meta
        # print pos_arr
        slide_start_time = meta['slide_start_time']
        code = data['target_pos']
        gt = meta['gt']
        challenge = meta['challenge']
        pos_arr = data['trail']
        now = time.time() * 1000
        userresponse = slide_challenge.encode_pos(code, challenge)  # 使用库
        a = slide_challenge.encode_pos_arr(pos_arr)
        passtime = pos_arr[-1][-1]
        new_meta = deepcopy(response.meta)
        new_meta.update({
            'code': code,
            'pos_arr': json.dumps(pos_arr),
            'args': response.request.body
        })
        req = scrapy.Request(
            method='GET',
            url=self.slide_url.format(
                gt,
                challenge,
                userresponse,
                passtime,
                random.randint(200, 2000),
                a,
                'geetest_' + self._get_timestamp(),
            ),
            meta=new_meta,
            dont_filter=True,
            # priority=5,
            callback=self.get_result,
            errback=self.recall_search_and_slide
        )

        if now - slide_start_time < passtime:  # 判断是否应该阻塞执行
            sleeptime = (passtime - (now - slide_start_time)) / 1000.0
            # sleeptime for 最大延迟，阻塞执行后通过req检测破解结果
            reactor.callLater(sleeptime, d.callback, req)
        else:
            pass
            reactor.callLater(0, d.callback, req)  # 不用延迟执行
        return d

    def get_result(self, response):
        print 'begin get_result'
        meta = deepcopy(response.meta)
        print response.text
        match = re.match('^geetest_\d+\((.*)\)$', response.text.strip())
        data = json.loads(match.group(1))
        if data['success'] == 1:
            print 'success'
            validate = data['validate']
            seccode = validate + '|jordan'
            meta.update({
                'validate': validate,
                'seccode': seccode,
            })
            formdata = {
                'tab': 'ent_tab',
                'searchword': meta['searchword'],
                'geetest_challenge': meta['challenge'],
                'geetest_validate': validate,
                'geetest_seccode': seccode
            }
            # print meta
            headers = deepcopy(self.headers)
            headers.update({
                'Referer': self.index_url,
            })
            yield scrapy.FormRequest(
                method='POST',
                url=self.search_url,
                meta=meta,
                formdata=formdata,
                dont_filter=True,
                # priority=6,
                callback=self.parse,
                headers=headers,
            )
        else:
            response.meta.update({
                'try_again': True,
            })
            print 'failed'
            yield self.search_and_slide(response).next()
