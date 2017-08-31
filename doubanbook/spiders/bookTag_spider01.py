# -*- coding: utf-8 -*-
import scrapy
# from doubanbook.items import DoubanbookIndexItem
from doubanbook.items import DoubanbookItem


class BookTagSpider(scrapy.Spider):
    name = "booktag"
    allowed_domains = ["book.douban.com"]
    start_urls = [
        "https://book.douban.com/"
    ]

    def parse(self, response):
        # first
        # filename = response.url.split("/")[-2] + ".html"
        # with open(filename, "wb") as f:
        #     f.write(response.body)

        # second
        # for bigTag in response.css('ul.clearfix'):
        #     item = DoubanbookIndexItem()
        #     bigTagTitle = bigTag.css(
        #         'li.tag_title::text').extract_first().strip()
        #     item['tagTitle'] = bigTagTitle
        #     smallTagList = bigTag.xpath(
        #         "li/a[@class='tag']/text()").extract()
        #     smallTagStr = ""
        #     for smallTag in smallTagList:
        #         smallTagStr += smallTag + ','
        #     smallTagStr.rstrip(',')
        #     item['tagItem'] = smallTagStr
        #     yield item

        # third
        url_template = "https://book.douban.com/%s?start=%d&type=T"
        for big_tag_ul in response.css('ul.clearfix'):
            tag_href_list = big_tag_ul.xpath(
                "li/a[@class='tag']/@href").extract()
            for tag_href_item in tag_href_list:
                # print tag_href_item
                url = url_template % (tag_href_item.lstrip('/'), 0)
                # print url
                yield scrapy.Request(url, callback=self.parse_dir_contents)

    def parse_dir_contents(self, response):
        # print response.url
        for book_item in response.css('li.subject-item'):
            item = DoubanbookItem()
            item['bookTitle'] = book_item.xpath(
                "div[@class='info']/h2/a/text()").extract_first().strip()
            pub = book_item.xpath(
                "div[@class='info']/div[@class='pub']/text()").extract_first().strip()
            pub_content = pub.split('/')
            item['bookPrice'] = pub_content[-1]
            item['bookDate'] = pub_content[-2]
            item['bookPress'] = pub_content[-3]
            item['bookAuthor'] = ','.join(pub_content[:-3])
            item['bookRatingNums'] = book_item.xpath(
                "div[@class='info']/div[@class='star clearfix']/span[@class='rating_nums']/text()").extract_first()
            item['bookRatingPl'] = book_item.xpath(
                "div[@class='info']/div[@class='star clearfix']/span[@class='pl']/text()").extract_first().strip()
            item['bookIntroduction'] = book_item.xpath(
                "div[@class='info']/p/text()").extract_first()
            if item['bookIntroduction'] is not None:
                item['bookIntroduction'].strip()
            yield item

        next_page_url = response.xpath(
            '//*[@id="subject_list"]/div[@class="paginator"]/span[@class="next"]/a/@href').extract_first()
        if next_page_url:
            yield scrapy.Request("https://book.douban.com" + next_page_url, callback=self.parse_dir_contents)
            # print next_page_url
