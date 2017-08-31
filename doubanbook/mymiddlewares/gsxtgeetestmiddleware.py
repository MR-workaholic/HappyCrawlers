# coding:utf-8
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import time
import PIL.Image as image
import re
import cStringIO
import urllib2
import random
from scrapy.http import HtmlResponse
from urllib import unquote


class GsxtGeetestMiddleware(object):
    target_url = 'http://www.gsxt.gov.cn/index.html'

    def __init__(self, br_name='chrome'):
        if br_name.lower() == 'chrome':
            pass

    def process_request(self, request, spider):
        if spider.name == 'gsxt' and \
                len(request.url.split('?')) == 2 and \
                request.url.split('?')[0] == self.target_url and \
                len(request.url.split('?')[1].split('=')) == 2 and \
                request.url.split('?')[1].split('=')[0] == 'query':
            pass
            self.browser = webdriver.Chrome("/usr/bin/chromedriver")
            self.browser.get(request.url)
            print '输入企业码'
            searchword = unquote(request.url.split('?')[1].split('=')[1])
            self.browser.find_element_by_id('keyword').clear()
            self.browser.find_element_by_id(
                'keyword').send_keys(searchword.decode('utf8'))
            self.s(1)

            print '点击查询按钮'
            self.browser.find_element_by_id('btn_query').click()
            self.s(1)

            cur_token = None
            eating_count = 0
            waiting_count = 0
            jump_judgement = False
            while(True):
                while(not jump_judgement and
                      cur_token is not None and
                      cur_token == self.get_token(
                          "//div[@class='gt_cut_bg_slice']")):
                    print 'waiting' + cur_token
                    waiting_count += 1
                    if waiting_count == 2:
                        jump_judgement = True
                        waiting_count = 0
                    self.s(2)

                jump_judgement = False
                if cur_token is None:
                    print '等待验证码'
                    #     等待页面的上元素刷新出来
                    WebDriverWait(self.browser, 30).until(
                        lambda the_browser: the_browser.find_element_by_xpath(
                            "//div[@class='gt_slider_knob gt_show']").is_displayed())
                    WebDriverWait(self.browser, 30).until(
                        lambda the_browser: the_browser.find_element_by_xpath(
                            "//div[@class='gt_cut_bg gt_show']").is_displayed())
                    WebDriverWait(self.browser, 30).until(
                        lambda the_browser: the_browser.find_element_by_xpath(
                            "//div[@class='gt_cut_fullbg gt_show']").is_displayed())

                cur_token = self.get_token("//div[@class='gt_cut_bg_slice']")
                print cur_token

                #     下载图片
                image1 = self.get_image(
                    "//div[@class='gt_cut_bg gt_show']/div")
                image2 = self.get_image(
                    "//div[@class='gt_cut_fullbg gt_show']/div")

                #     计算缺口位置
                loc = self.get_diff_location(image1, image2)

                #     生成x的移动轨迹点
                track_list = self.get_track(loc)

                #     找到滑动的圆球
                element = self.browser.find_element_by_xpath(
                    "//div[@class='gt_slider_knob gt_show']")
                location = element.location
                #     获得滑动圆球的高度
                y = location['y']

                #     鼠标点击元素并按住不放
                print "第一步,点击元素"
                ActionChains(self.browser).click_and_hold(
                    on_element=element).perform()
                self.s(1)

                print "第二步，拖动元素"
                track_string = ""
                for track in track_list:
                    y_offset = 504
                    track_string = track_string + \
                        "{%d,%d}," % (track, y - y_offset)
                #         xoffset=track+22:这里的移动位置的值是相对于滑动圆球左上角的相对值，而轨迹变量里的是圆球的中心点，所以要加上圆球长度的一半。
                #         yoffset=y-445:这里也是一样的。不过要注意的是不同的浏览器渲染出来的结果是不一样的，要保证最终的计算后的值是22，也就是圆球高度的一半
                    ActionChains(self.browser).move_to_element_with_offset(
                        to_element=element,
                        xoffset=track + 22,
                        yoffset=y - y_offset).perform()
                    ActionChains(self.browser).click_and_hold().perform()
                #         间隔时间也通过随机函数来获得
                    self.s(random.randint(10, 50) / 50)
                # print track_string

                print "第三步，释放鼠标"
                #     释放鼠标
                ActionChains(self.browser).release(
                    on_element=element).perform()
                self.s(1)
                result_element = WebDriverWait(self.browser, 10, 1.0).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "gt_info_text")))
                try:
                    result = result_element.text.encode("utf-8")
                except StaleElementReferenceException:
                    result = '页面已经跳转，成功通过测试'

                print result
                if '通过' in result:
                    break
                elif '验证失败' in result:
                    jump_judgement = True
                elif '出现错误' in result:
                    eating_count = 5
                else:
                    eating_count += 1

                if eating_count == 5:
                    self.s(0.8)
                    self.browser.refresh()
                    self.browser.find_element_by_id('keyword').clear()
                    self.browser.find_element_by_id('keyword').send_keys(
                        searchword.decode('utf8'))
                    self.s(1)
                    self.browser.find_element_by_id('btn_query').click()
                    eating_count = 0
                    jump_judgement = False
                    waiting_count = 0
                    cur_token = None

            self.s(1)
            body = self.browser.page_source
            print "goto" + self.browser.current_url
            return HtmlResponse(self.browser.current_url,
                                body=body,
                                encoding='utf-8')

        else:
            return None

    def s(self, int):
        time.sleep(int)

    def get_merge_image(self, filename, location_list):
        '''
        根据位置对图片进行合并还原
        :filename:图片
        :location_list:图片位置
        '''
        pass

        im = image.open(filename)

        new_im = image.new('RGB', (260, 116))

        im_list_upper = []
        im_list_down = []

        for location in location_list:

            if location['y'] == -58:
                pass
                im_list_upper.append(
                    im.crop((abs(location['x']), 58, abs(location['x']) + 10, 166)))
            if location['y'] == 0:
                pass

                im_list_down.append(
                    im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        new_im = image.new('RGB', (260, 116))

        x_offset = 0
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]

        return new_im

    def get_token(self, div):
        '''
        获取每次验证码的token
        :div:token's div
        '''
        token_div_list = self.browser.find_elements_by_xpath(div)
        return re.findall("gt\/(.*)\/bg", token_div_list[0].get_attribute('style'))[0]

    def get_image(self, div):
        '''
        下载并还原图片
        :driver:webdriver
        :div:图片的div
        '''
        pass

        # 找到图片所在的div
        background_images = self.browser.find_elements_by_xpath(div)

        location_list = []

        imageurl = ''

        for background_image in background_images:
            location = {}

            # 在html里面解析出小图片的url地址，还有长高的数值
            location['x'] = int(re.findall(
                "background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;", background_image.get_attribute('style'))[0][1])
            location['y'] = int(re.findall(
                "background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;", background_image.get_attribute('style'))[0][2])
            imageurl = re.findall("background-image: url\(\"(.*)\"\); background-position: (.*)px (.*)px;",
                                  background_image.get_attribute('style'))[0][0]

            location_list.append(location)

        imageurl = imageurl.replace("webp", "jpg")

        jpgfile = cStringIO.StringIO(urllib2.urlopen(imageurl).read())

        # 重新合并图片
        image = self.get_merge_image(jpgfile, location_list)

        return image

    def is_similar(self, image1, image2, x, y):
        '''
        对比RGB值
        '''
        pass

        pixel1 = image1.getpixel((x, y))
        pixel2 = image2.getpixel((x, y))

        for i in range(0, 3):
            if abs(pixel1[i] - pixel2[i]) >= 50:
                return False

        return True

    def get_diff_location(self, image1, image2):
        '''
        计算缺口的位置
        '''

        i = 0

        for i in range(0, 260):
            for j in range(0, 116):
                if self.is_similar(image1, image2, i, j) is False:
                    return i

    def get_track(self, length):
        '''
        根据缺口的位置模拟x轴移动的轨迹
        '''
        pass

        list = []

        first_stage = length / 5 * 4
    #     间隔通过随机范围函数来获得
        x = random.randint(1, 2)
        while length - x >= first_stage:
            list.append(x)
            length = length - x
            x = random.randint(1, 2)

        x = random.randint(-1, 2)
        while length - x >= 5:
            list.append(x)
            length = length - x
            x = random.randint(-1, 2)

        # for i in xrange(length):
        # list.append(1)

        return list
