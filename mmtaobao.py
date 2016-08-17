# -*- coding: utf-8 -*-
# __author__ = 'yongtzha'

import requests
from bs4 import BeautifulSoup
import common

logger = common.get_logger(__name__)

class TaobaoMM(object):
    
    def __init__(self,name,age,location,home_page):
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
''' %(self.name.encode(self.encoding), self.age.encode(self.encoding), self.location.encode(self.encoding), self.home_page.encode(self.encoding))

class MMTaobao(object):

    def __init__(self):
        self.base_link = 'http://mm.taobao.com/json/request_top_list.htm'
        self.page_encode = 'utf-8'

    def get_page_content(self, page_num):
        payload = {'page': page_num}
        r = requests.get(self.base_link, params=payload)
        data = r.text.encode(self.page_encode)
        logger.info('Get info from %s' %r.url)
        with open('mmtaobao.html', 'wb') as fd:
            fd.write(data)
        return data

    def get_mm_taobao(self, total_page=3):
        page = 1
        mm_list = []
        while page <= total_page:
            page_content = self.get_page_content(page)
            mm_infos=self.get_mm_list(page_content)
            mm_list.extend(mm_infos)
            page += 1
        return mm_list

    def get_mm_list(self,page_content):
        mm_info=[]
        soup = BeautifulSoup(page_content,'lxml')
        for info_blk in soup.find_all('div',class_='personal-info'):
            name_blk = info_blk.find('a','lady-name')
            mm_name = name_blk.string
            mm_home_page = 'http:'+name_blk['href']
            age_blk = name_blk.find_next_sibling()
            age = age_blk.get_text()
            location = age_blk.find_next_sibling().get_text()
            mm_info.append(TaobaoMM(mm_name,age,location,mm_home_page))
        return mm_info


if __name__ == '__main__':
    mt = MMTaobao()
    for mm in mt.get_mm_taobao():
        print str(mm)
