# -*- coding: utf-8 -*-
import sys
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import quote
import re
import requests

#TARGET_URL="http://www.g2b.go.kr:8340/search.do?kwd=%C4%AB%B7%BB%B4%D9&category=TGONG&subCategory=ALL&detailSearch=true&reSrchFlag=false&pageNum=1&sort=RDD&srchFd=ALL&date=&startDate=20170224&endDate=20190324&year=&orgType=balju&orgName=&orgCode=&swFlag=Y&dateType=3&area=&gonggoNo=&preKwd=&preKwds="
TARGET_URL="http://www.g2b.go.kr:8340/body.do?kwd=%C4%AB%B7%BB%B4%D9&category=TGONG&subCategory=ALL&detailSearch=true&sort=RDD&reSrchFlag=false&pageNum=1&srchFd=ALL&date=&startDate=20170224&endDate=20190324&startDate2=&endDate2=&orgType=balju&orgName=&orgCode=&swFlag=Y&dateType=3&area=&gonggoNo=&preKwd=&preKwds=&body=yes"

# TARGET_KEYWORD=


# 클러스터링 함수
def clean_text(text):
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text

# 조달청 공고 제목에서 링크된 본문 링크와 정보 가져오기
def get_info_from_g2b_title():
    #
    # source_code_from_URL = urllib.request.urlopen(TARGET_URL)
    # #source_code = requests.request("GET",TARGET_URL)
    # #print("success2")
    # #plain_text = source_code.text
    # #print(source_code_from_URL)
    # soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')
    # print("success2")
    # print(soup)


    try:
        source_code_from_URL = urllib.request.urlopen(TARGET_URL)
        print("1")
        soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')
        print("2")
        print("3")

        #print(soup)
        for content in soup.select('ul.search_list>li'):
            print("check")
            #print(content)
            content_title = content.select('strong.tit>a')
            title = str(content_title[0].find_all(text=True))
            title = clean_text(title)
            #print("공고제목 : ", title)

            content_end_date = content.select('li.m1>span')
            end_date = str(content_end_date[0].find_all(text=True))
            end_date = re.sub('\r','', end_date)
            end_date = re.sub('\n', '', end_date)
            end_date = re.sub('\t', '', end_date)
            #end_date = end_date.replace("\r", "")
            #end_date = end_date.replace("\n", "")
            #end_date = end_date.replace("\t", "")
            #end_date = clean_text(end_date)
            print(end_date)


    except:
        print("ERROR")
        return None


def main():
    get_info_from_g2b_title()

if __name__ == '__main__':
    main()