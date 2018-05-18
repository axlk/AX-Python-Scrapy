# -*- coding:utf-8 -*-
import scrapy
import re
import os
import urllib
import sys
import time
import urllib2
from ..items import XiaMeiPhotoAlbum
from scrapy.selector import Selector
from scrapy.http import HtmlResponse,Request
from urllib2 import URLError, HTTPError
print(os.getcwd())

#test = "https://www.nvshens.com/girl/21501/album/"
g_main_host = "https://www.nvshens.com"
g_girl_identifier = "21501"


g_export_path_root = os.getcwd()+"/export_root"


#创建导出目录
if not os.path.exists(g_export_path_root):
    os.makedirs(g_export_path_root)

g_photoAlbumList = []


def save_photo(response, album):

    current_url=response.url
    #print("AX --> process url:"+current_url)
    hxs=Selector(response) 

    #所有图片
    photos = hxs.xpath('//*[@id="hgallery"]/img/@src').extract()
    #print("AX --> photo size : %s" % len(photos))
    for i in range(len(photos)):
        album['photos'].append(photos[i])
        #print(photos[i])

    #print(len(album['photos']))

#获取html内容
def get_html_content(html_label):
    rc = re.compile("\<.*?\>" ) 
    return rc.sub('',html_label) 

def get_page_source(url):
    headers = {'Accept': '*/*',
               'Accept-Language': 'en-US,en;q=0.8',
               'Cache-Control': 'max-age=0',
               'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
               'Connection': 'keep-alive',
               'Referer': 'http://www.nvshens.com/'
               }
    req = urllib2.Request(url, None, headers)
    try:
        response = urllib2.urlopen(req)
        page_source = response.read()
        return page_source
    except HTTPError:
        return 0


class XiaMei_spider(scrapy.spiders.Spider):

    name="XiaMei"#定义爬虫名

    allowed_domains=["nvshens.com"]    #搜索的域名范围，也就是爬虫的约束区域，规定爬虫只爬取这个域名下的网页

    one_girl_url = os.path.join( g_main_host, "girl", g_girl_identifier, "album/",  )

    start_urls=[ one_girl_url ]

    
    def closed(self, reson):
        print("AX closed --> album len %s" % (len(g_photoAlbumList)))

        album_index = 1
        for album in g_photoAlbumList:

            #创建目录
            album_name = g_export_path_root + "/" + str(album_index)
            album_index = album_index + 1

            if not os.path.exists( album_name ):
                os.makedirs( album_name )
                print("create album path :"+album_name)

            #下载图片
            print("all photo num :"+str(len(album['photos'])))
            for photo_url in album['photos']:

                photo_name = photo_url.split('/')[-1]
                photo_save_path = album_name+"/"+photo_name

                if not os.path.exists( photo_save_path ):
                    print("download photo :"+photo_url)
                    #urllib.urlretrieve(photo_url, photo_save_path)
                    photo_content = get_page_source(photo_url)
                    if photo_content != 0:
                        f = open(photo_save_path, 'wb')
                        f.write(photo_content)
                        f.close()
                        print(len(photo_content))
                    else:
                        print("404 found ..")
                else:
                    print("photo exists... :"+photo_save_path)

                #print(photo_url)


            """
            print(len(album['photos']))
            for photo_url in album['photos']:
                print(photo_url)
            """


    #该函数名不能改变，因为Scrapy源码中默认callback函数的函数名就是parse
    def parse(self, response):
        current_url=response.url    #爬取时请求的url
        body=response.body  #返回的html
        unicode_body=response.body_as_unicode() #返回的html unicode      

        hxs=Selector(response) 

        items=hxs.xpath('//a[@class="caption"]/@href').extract() 
        print("item len : %s " % len(items))
        tmp_cnt = 0;
        for i in range(len(items)):#遍历div个数
            #需要访问的下个url, Examples: https://www.nvshens.com/g/22942/
            album_url = g_main_host + items[i]
            print("AX --> request album url : "+album_url)
            yield Request(url=album_url, callback=self.parse_album)

            #if(tmp_cnt == 0):
            #    break;

            tmp_cnt = tmp_cnt + 1
            #print(items[i].split(" ")[1])



    def parse_album(self, response):
        current_url=response.url    #爬取时请求的url
        hxs=Selector(response) 


        album_name = hxs.xpath('//*[@id="htilte"]').extract()[0]
        album_desc = hxs.xpath('//*[@id="ddesc"]').extract()[0]
        #album_photo_num = hxs.xpath('//*[@id="dinfo"]/span').extract()
        album_desc_info = hxs.xpath('//*[@id="dinfo"]').extract()[0]


        #print(album_name)
        #print(album_desc)
        #print(album_desc_info)

        photoAlbum = XiaMeiPhotoAlbum()
        photoAlbum['photos'] = []
        photoAlbum['create_time'] = time.time()


 
        photoAlbum['album_name'] = get_html_content(album_name)
        #print(photoAlbum['album_name'])
        photoAlbum['album_desc'] = get_html_content(album_desc)
        #print(photoAlbum['album_desc'])
        photoAlbum['album_desc_info'] = get_html_content(album_desc_info)


        #print(photoAlbum['album_desc_info'])

        #print("AX ---> org id:")
        #print(id(photoAlbum))
        save_photo(response, photoAlbum)

        page_start_org = hxs.xpath('//*[@id="pages"]/a/@href').extract()[1]
        temp = page_start_org.split("/")[-1]
        page_template = page_start_org.replace(temp,"")
        all_pages = []
        #print("AX --> page _template ....")
        for i in range(2,50):
            next_page_url = g_main_host+page_template+str(i)+".html"
            #print(next_page_url)
            all_pages.append(next_page_url)

        for url in all_pages:
            yield Request(url=url, meta={'album':photoAlbum, 'first':current_url}, callback=self.parse_album_next_pages)


        #获取所有页
        """
        all_pages = hxs.xpath('//*[@id="pages"]/a/@href').extract()
        for i in range(1, len(all_pages)):
            next_page_url = g_main_host+all_pages[i]
            #print(" process next pages :"+next_page_url)
            yield Request(url=next_page_url, meta={'album':photoAlbum}, callback=self.parse_album_next_pages)
        """

        g_photoAlbumList.append(photoAlbum)            


        """
        print(len(photoAlbum['photos']))
        for photo_url in photoAlbum['photos']:
            print(photo_url)
        """


    def parse_album_next_pages(self, response):

        photoAlbum = response.meta['album']
        save_photo(response, photoAlbum)


