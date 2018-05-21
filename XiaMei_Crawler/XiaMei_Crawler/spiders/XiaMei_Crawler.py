# -*- coding:utf-8 -*-
import scrapy
import re
import os
import urllib
import sys
import time
import urllib2
#from XiaMei_Crawler.items import XiaMeiPhotoAlbum
from ..items import XiaMeiPhotoAlbum
from scrapy.selector import Selector
from scrapy.http import HtmlResponse,Request
from urllib2 import URLError, HTTPError
print(os.getcwd())

#test = "https://www.nvshens.com/girl/21501/album/"
g_main_host = "https://www.nvshens.com"


#主目录
g_export_path_root = os.getcwd()+"/export_root"


#创建导出目录
if not os.path.exists(g_export_path_root):
    os.makedirs(g_export_path_root)

#相片专辑
g_photoAlbumList = []

#是否导出相片
g_export_photo = True

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
    except BaseException:
        print("AX ERROR :"+str(url))
        return 0


class XiaMei_spider(scrapy.spiders.Spider):

    name="XiaMei"#定义爬虫名

    allowed_domains=["nvshens.com"]    #搜索的域名范围，也就是爬虫的约束区域，规定爬虫只爬取这个域名下的网页

    g_girl_identifier = 0

    def __init__(self, girl_id=None, *args, **kwargs):
        self.g_girl_identifier = girl_id
        if self.g_girl_identifier == None: 
            print("AX ---> please input girl id.")
            exit(0)
        print("girl id :%s" % (self.g_girl_identifier))

        one_girl_url = os.path.join( g_main_host, "girl",self. g_girl_identifier  )
        print("one_girl_url:"+one_girl_url)
        self.start_urls=[ one_girl_url ]    

    #解析
    def parse(self, response):
        start_url =response.url    #爬取时请求的url
        tmp = True

        total_url = response.xpath('//*[@class="archive_more"]/a/@href').extract_first()
        if total_url == None:
            print("No Total Page")
            yield Request(url = start_url, callback=self.parse_album_url_one)
        else:

            total_url = g_main_host + total_url
            print(" Total_url :"+total_url)
            yield Request(url = total_url, callback=self.parse_album_url_total)
        if tmp:
            print("Temp Return...")
            return

    #没有全部的
    def parse_album_url_one(self, response):
        hxs=Selector(response) 

        items=hxs.xpath('//*[@class="igalleryli_div"]/a/@href').extract() 
        print("item len : %s " % len(items))
        tmp_cnt = 0;
        for i in range(len(items)):#遍历div个数
            album_url = g_main_host + items[i]
            print("AX --> one page request album url : "+album_url)
            yield Request(url=album_url, callback=self.parse_album)
            #debug 只处理一个目录的
            if(tmp_cnt == 0):
                break;

            tmp_cnt = tmp_cnt + 1

    #有全部的
    def parse_album_url_total(self, response):
        hxs=Selector(response) 

        items=hxs.xpath('//*[@class="igalleryli_div"]/a/@href').extract() 
        print("item len : %s " % len(items))
        tmp_cnt = 0;
        for i in range(len(items)):#遍历div个数
            #需要访问的下个url, Examples: https://www.nvshens.com/g/22942/
            album_url = g_main_host + items[i]
            print("AX --> request album url : "+album_url)
            yield Request(url=album_url, callback=self.parse_album)

            #debug 只处理一个目录的
            #if(tmp_cnt == 0):
            #    break;

            tmp_cnt = tmp_cnt + 1
            #print(items[i].split(" ")[1])

    def parse_album(self, response):
        first_url=response.url    #爬取时请求的url
        print("first_page:"+first_url)
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

        #print("AX ---> next page...")
        all_next_page = hxs.xpath('//*[@id="pages"]/a/@href').extract()
        next_page = all_next_page[-1]
        next_page_url = g_main_host+next_page
        #print("first next page")
        #print(next_page_url)
        yield Request(url=next_page_url, meta={'album':photoAlbum, 'first':first_url}, callback=self.parse_album_next_pages_new)
        g_photoAlbumList.append(photoAlbum)

    def parse_album_next_pages_new(self, response):
        photoAlbum = response.meta['album']
        save_photo(response, photoAlbum)

        first_url = response.meta['first']
        all_next_page = response.xpath('//*[@id="pages"]/a/@href').extract()
        next_page = all_next_page[-1]
        next_page_url = g_main_host+next_page
        #print( "find next page" )
        #print(first_url)
        #print( next_page_url )
        if ".html" in next_page_url:
            #print(next_page_url)
            yield Request(url=next_page_url, meta={'album':photoAlbum, 'first':first_url}, callback=self.parse_album_next_pages_new)


    def closed(self, reson):
        if g_export_photo == False:
            print("AX dont export photos..")
            return

        print("AX closed --> album len %s" % (len(g_photoAlbumList)))

        album_index = 1
        for album in g_photoAlbumList:

            #创建目录
            #album_number_str = str(album_index).zfill(3)
            album_number_str = ""
            album_name = g_export_path_root + "/" +str(self.g_girl_identifier)  +  "/"+album_number_str +"_"+ album["album_name"]
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


