# -*- coding: utf-8 -*-
import scrapy
from BBCcrawl.items import BbccrawlUrlItem, BbccrawlItem


class BbcSpider(scrapy.Spider):
    name = "bbc"
    allowed_domains = ["bbc.com"]
    start_urls = ['http://bbc.com/news', 'http://bbc.com/']
    articlecount = 0

    # def start_requests(self):
    #     yield scrapy.Request('http://bbc.com/news',
    #                          callback=self.parse,
    #                          headers=
    #          {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'},
    #                          dont_filter=True)


    def parse(self, response):
        # 新闻页面的处理
        if response.url[-1] in '1234567890':
            self.articlecount += 1
            print(self.articlecount)
            print('得到新闻页面：', response.url)
            item = BbccrawlItem()
            urlItem = BbccrawlUrlItem()
            # 对新闻内容的处理
            # for para in response.xpath('//div[contains(@property, "articleBody")]/p'):
            #     print(para.xpath('text()'))
            item['Id'] = self.articlecount
            # 决定是否留存item的标记
            self.gooditem = True

            # 处理文章标题
            try:
                item['Title'] = response.xpath('//h1[contains(@class, "story-body__h1")]/text()').extract()[0]
            except IndexError:
                # 丢弃文章
                self.gooditem = False

            # 处理文章主体
            # 正常模式
            try:
                body = response.xpath('//div[contains(@property, "articleBody")]/p/text()').extract()
                item['Summary'] = body[0]
                item['Content'] = '\n'.join(body[1:])
            except IndexError:
                # 视频模式
                try:
                    body = response.xpath('//div[contains(@id, "media-asset-page-text")]/div/p/text()').extract()
                    item['Summary'] = ''
                    item['Content'] = '\n'.join(body)
                except IndexError:
                    # 丢弃文章
                    self.gooditem = False

            # 处理分类
            # 方法1：使用文章内部的分类标志
            try:
                item['Type'] = response.xpath('//a[contains(@data-entityid, "section-label")]/text()').extract()[0]
            except IndexError:
                # 方法2：使用导航栏上被选中的分类标志
                try:
                    item['Type'] = response.xpath(
                        '//a[contains(@class, "selected")][1]/span/text() | //li[contains(@class, "selected")][1]/a/span/text()').extract()[
                        0]
                except IndexError:
                    # 方法3：从URL中提取
                    try:
                        item['Type'] = response.url.split('/news/')[1].split('/')[-1].rstrip('-1234567890')
                    except IndexError:
                        # 疑难杂类
                        item['Type'] = ''

            # 处理 Reference URL
            item['Refer'] = response.url

            # 获取relative time
            try:
                item['relative_time'] = int(response.xpath('//li[contains(@class, "mini-info-list__item")]/div/@data-seconds').extract()[0])
            except IndexError:
                try:
                    item['relative_time'] = int(response.xpath('//p[contains(@class, "date")][1]/@data-seconds').extract()[0])
                except IndexError:
            # drop the item
                    self.gooditem = False

            item['Pubtime'] = response.xpath('//div[@class="story-body"]//ul[@class="mini-info-list"]//div/text()').extract_first()
            # 处理related topics
            related_list = response.xpath('//div[@id="topic-tags"]//li/a/text()').extract()
            # 将list分割成字符串储存
            item['related_topics'] = (','.join(related_list))
            # 将爬取好的文章对象yield
            if self.gooditem: yield item

            # 处理其它链接
            # 对延伸阅读的处理（一）——使用文末的more on this story
            for story in response.xpath('//div[contains(@class, "more-on-this-story")]'):
                for linkedstory in story.xpath('div/ul/li'):
                    try:
                        urlItem['URL'] = linkedstory.xpath('a/@href').extract()[0]
                        urlItem['Title'] = linkedstory.xpath('a/div/div/div/span/text()').extract()[0]
                        if urlItem['URL'][0:6] != 'http://':
                            urlItem['URL'] = 'http://www.bbc.com' + urlItem['URL']
                        yield scrapy.Request(url=urlItem['URL'])
                    except IndexError:
                        pass

            # 对延伸阅读的处理（二）——使用文中插入的Read More
            for story in response.xpath('//a[contains(@class, "story-body__link")]'):
                urlItem['URL'] = story.xpath('@href').extract()[0]
                # urlItem['Title'] = story.xpath('text()').extract()[0]
                if urlItem['URL'][0:6] != 'http://':
                    urlItem['URL'] = 'http://www.bbc.com' + urlItem['URL']
                yield scrapy.Request(url=urlItem['URL'])




        # 对新闻首页的处理
        elif response.url[-4:] == 'news':
            for link in response.xpath('//a[contains(@class, "navigation-wide-list__link")]'):
                urlItem = BbccrawlUrlItem()
                urlItem['URL'] = link.xpath('@href').extract()[0]
                urlItem['Title'] = link.xpath('span/text()').extract()[0]
                if urlItem['URL'][0:6] != 'http://':
                    urlItem['URL'] = 'http://www.bbc.com' + urlItem['URL']
                    print('抓取到【新闻首页】中的栏目链接：')
                    print(urlItem)
                yield scrapy.Request(url=urlItem['URL'])


        # BBC主页的处理
        else:
            for link in response.xpath('//a[contains(@class, "media__link")]'):
                urlItem = BbccrawlUrlItem()
                urlItem['URL'] = link.xpath('@href').extract()[0]
                urlItem['Title'] = link.xpath('text()').extract()[0].lstrip().rstrip()
                if urlItem['URL'][0:6] != 'http://':
                    urlItem['URL'] = 'http://www.bbc.com' + urlItem['URL']
                    print('抓取到【首页】中的新闻链接：')
                    print(urlItem)
                yield scrapy.Request(url=urlItem['URL'])
