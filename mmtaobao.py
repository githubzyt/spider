# __author__ = 'yongtzha'
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import common
import os
import logging
import json
import threading
# from multiprocessing import  Queue
from Queue import Queue
import time

logging.basicConfig(level=logging.INFO,
                    format='(%(threadName)-9s) %(message)s',)

proxies={
    "http":"http://10.158.100.1:8080",
    "https":"http://10.158.100.1:8080"
}

os.environ['http_proxy'] = 'http://10.158.100.1:8080'
os.environ['https_proxy'] = 'http://10.158.100.1:8080'


BUF_SIZE = 100
image_que=Queue(BUF_SIZE)
url_que = Queue(5000)

class TaobaoMM(object):

    def __init__(self, name, age, location, home_page):
        self.name = name
        self.age = age
        self.location = location
        self.home_page = home_page
        self.encoding = 'utf-8'

    def __str__(self):
        return '''
name: %s
age: %s
location: %s
home page: %s
''' % (self.name.encode(self.encoding), self.age.encode(self.encoding), self.location.encode(self.encoding), self.home_page.encode(self.encoding))


class ImageDownloader(threading.Thread):

    def __init__(self,group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ImageDownloader,self).__init__()
        self.target = target
        self.name = name

    def run(self):
        while True:
            if not image_que.empty():
                item = image_que.get()
                logging.info('Getting ' + str(item) 
                              + ' : ' + str(image_que.qsize()) + ' items in image queue')
                self.download_img(item)
        return

    def download_img(self,item):
        logging.debug('photo_album_link=%s' %photo_album_link)
        image_name=photo_album_link.split('/')[-1]
        photo_dir=os.path.join(mm_folder,'photos')
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)
        image_full_path=os.path.join(photo_dir,image_name)
        logging.debug('download file from %s to %s' %(photo_album_link,image_full_path))
        r=requests.get(photo_album_link,stream=True)
        with open(image_full_path,'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return image_full_path

class URLAnalyzer(threading.Thread):

    def __init__(self,group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(URLAnalyzer,self).__init__()
        self.target = target
        self.name = name

    def run(self):
        while True:
            if not url_que.empty():
                item = url_que.get()
                logging.debug('Getting ' + str(item) 
                              + ' : ' + str(url_que.qsize()) + ' items in url queue')
                self.analysis_url(item)
        return

    def is_link_available(self,link):
        if link.startswith('https://') or link.startswith('http://'):
            return True
        return False

    def get_img_link(self,img_tag):
        ori_img_link=img_tag.get('src')
        if ori_img_link:
            ori_img_link=ori_img_link.strip() 
        if ori_img_link and ori_img_link.startswith('//'):
            ori_img_link="http:"+ori_img_link
        return ori_img_link

    def get_href_link(self,a_tag):
        href=a_tag.get('href')
        if href:
            href=href.strip()
        if href and href.startswith('//'):
            href='http:'+href
        return href

    def analysis_url(self,item,page_encode='utf-8',base_link='http://mm.taobao.com/self'):
        link, depth = item
        if not self.is_link_available(link):
            return
        r = requests.get(link)
        data = r.text.encode(page_encode)
        soup = BeautifulSoup(data, 'lxml',from_encoding='utf-8')
        for img_tag in soup.find_all('img'):
            img_link=self.get_img_link(img_tag)
            if img_link and self.is_link_available(img_link):
                logging.debug('put a new image link %s' %img_link)
                image_que.put(img_link)
        new_depth=depth-1
        if new_depth >= 0:
            for herf_tag in soup.find_all('a'):
                href=self.get_href_link(herf_tag)
                if href and self.is_link_available(href) and href.startswith(base_link):
                    logging.debug('put %s in url queue' %href)
                    url_que.put((href, new_depth))

class MMTaobao(object):

    def __init__(self):
        self.base_link = 'http://mm.taobao.com/json/request_top_list.htm'
        self.page_encode = 'utf-8'
        self.save_folder = 'taobaomm'
        self.find_depth = 3

    def get_page_content(self, page_num):
        payload = {'page': page_num}
        r = requests.get(self.base_link, params=payload)
        data = r.text.encode(self.page_encode)
        logging.info('Get info from %s' % r.url)
        with open('mmtaobao.html', 'wb') as fd:
            fd.write(data)
        return data

    def get_mm_taobao(self, total_page=3):
        page = 1
        mm_list = []
        while page <= total_page:
            page_content = self.get_page_content(page)
            mm_infos = self.get_mm_list(page_content)
            mm_list.extend(mm_infos)
            page += 1
        return mm_list

    def get_mm_list(self, page_content):
        mm_info = []
        soup = BeautifulSoup(page_content, 'lxml')
        for info_blk in soup.find_all('div', class_='personal-info'):
            name_blk = info_blk.find('a', 'lady-name')
            mm_name = name_blk.string
            mm_home_page = 'http:'+name_blk['href']
            age_blk = name_blk.find_next_sibling()
            age = age_blk.get_text()
            location = age_blk.find_next_sibling().get_text()
            mm_info.append(TaobaoMM(mm_name, age, location, mm_home_page))
        return mm_info

    def get_photo_album_link(self, home_page):
        r = requests.get(home_page)
        data = r.text.encode(self.page_encode)
        soup =  BeautifulSoup(data, 'lxml', from_encoding='utf-8')
        photo_album_link = 'http:' + soup.find('a', text=u'\u76f8\u518c')['href']
        return photo_album_link

    def download_img(self,photo_album_link,mm_folder):
        logging.debug('photo_album_link=%s' %photo_album_link)
        image_name=photo_album_link.split('/')[-1]
        photo_dir=os.path.join(mm_folder,'photos')
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)
        image_full_path=os.path.join(photo_dir,image_name)
        logging.debug('download file from %s to %s' %(photo_album_link,image_full_path))
        r=requests.get(photo_album_link,stream=True)
        with open(image_full_path,'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return image_full_path

    def save_mms_info(self,total_page=3):
        mm_list = self.get_mm_taobao(total_page=total_page)
        for mm in mm_list:
            self.save_to_disk(mm.name,mm.age,mm.location,mm.home_page)

    def save_to_disk(self,name,age,location,home_page):
        mm_folder=os.path.join(self.save_folder,name)
        mm_file=os.path.join(mm_folder,'mm.txt')
        if not os.path.exists(mm_folder):
            os.makedirs(mm_folder)
        with open(mm_file,'w') as f:
            f.write('name: %s\n' %name.encode(self.page_encode))
            f.write('age: %s\n' %age.encode(self.page_encode))
            f.write('location: %s\n' %location.encode(self.page_encode))
            f.write('home page: %s\n' %home_page)


    def save_mm_info_by_mm_list(self,mm_list):
        logging.info('start save mm info')
        url_analyzer=[URLAnalyzer(name='url analyser %s' %i) for i in range(3)]
        image_analyzer=[ImageDownloader(name='image downloader %s' %i) for i in range(3)]
        for mm in mm_list:
            logging.info('mm info:\n%s' %str(mm))
            self.save_to_disk(mm.name,mm.age,mm.location,mm.home_page)
            url_que.put((mm.home_page,self.find_depth))
        for u in url_analyzer:
            u.start()
        for i in image_analyzer:
            i.start()
        logging.info('compelete save mm info')

    def save_mm_info_from_file(self,info_file):
        mm_list=json.dumps(info_file)
        self.save_mm_info_by_mm_list(mm_list)

def test():
    with open('homepage.html', 'wb') as fd:
        r = requests.get('http://mm.taobao.com/self/model_card.htm?user_id=93166849')
        data = r.text.encode('utf-8')
        fd.write(data)
        print r.headers


def test2():
    url = 'http://mm.taobao.com/539549300.htm'
    r = requests.get(url)
    print r.url
    print r.status_code
    print r.headers
    print r.content
    with open('login.html', 'wb') as fd:
        fd.write(r.text.encode('utf-8'))


def test_home_page():
    with open('homepage.html', 'rb') as f:
        data = f.read()
        # print data
        # print data[70:72].decode('utf-8')
        soup = BeautifulSoup(data, 'lxml', from_encoding='utf-8')
        print soup.prettify('utf-8')


def test_photo_album():
    url = 'https://mm.taobao.com/self/model_info.htm?user_id=687471686&is_coment=false'
    with open('model_info.htm', 'w') as f:
        r = requests.get(url)
        f.write(r.text.encode('utf-8'))

if __name__ == '__main__':
    mt = MMTaobao()
    mm_list=mt.get_mm_taobao(total_page=1)
    mt.save_mm_info_by_mm_list(mm_list)
