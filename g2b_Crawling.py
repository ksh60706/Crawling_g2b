# -*- coding: utf-8 -*-
#import sys
from bs4 import BeautifulSoup
import urllib.request
#from urllib.parse import quote
import re
import requests

from pymongo import MongoClient

#TARGET_URL="http://www.g2b.go.kr:8340/search.do?kwd=%C4%AB%B7%BB%B4%D9&category=TGONG&subCategory=ALL&detailSearch=true&reSrchFlag=false&pageNum=1&sort=RDD&srchFd=ALL&date=&startDate=20170224&endDate=20190324&year=&orgType=balju&orgName=&orgCode=&swFlag=Y&dateType=3&area=&gonggoNo=&preKwd=&preKwds="
TARGET_URL="http://www.g2b.go.kr:8340/body.do?kwd=%C4%AB%B7%BB%B4%D9&category=TGONG&subCategory=ALL&detailSearch=true&sort=RDD&reSrchFlag=false&pageNum=1&srchFd=ALL&date=&startDate=20170224&endDate=20190324&startDate2=&endDate2=&orgType=balju&orgName=&orgCode=&swFlag=Y&dateType=3&area=&gonggoNo=&preKwd=&preKwds=&body=yes"

# TARGET_KEYWORD=

# DB 연결
def conn_db():
    conn = MongoClient("127.0.0.1")
    db = conn.testDB
    return db


# 클러스터링 함수
def clean_text(text):
    #cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text

# 조달청 공고 제목에서 링크된 본문 링크와 정보 가져오기
def get_info_from_g2b_title():
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
        soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')

        db = conn_db()
        collection_test = db.test

        #print(soup)
        for content in soup.select('ul.search_list>li'):
            print("******************************check******************************")
            #print(content)
            # 제목
            content_title = content.select('strong.tit>a')
            title = str(content_title[0].find_all(text=True))
            title = clean_text(title)


            # 상세내용 URL
            content_detail_URL_list = title.split("  ")
            content_NO = content_detail_URL_list[0][:-2]
            title = content_detail_URL_list[1]
            content_detail_URL = "http://www.g2b.go.kr:8081/ep/invitation/publish/bidInfoDtl.do?bidno="+content_NO+"&bidseq=00&releaseYn=Y&taskClCd=1 "
            print("공고제목 : ", title)
            print("공고 상세 URL : ", content_detail_URL)

            # 입찰마감일
            content_end_date = content.select('li.m1>span')
            if not content_end_date:
                end_date=""
            else:
                end_date = str(content_end_date[0].find_all(text=True))
                end_date = re.sub("[\[\'\]\\\]", "", end_date)
                end_date = end_date.replace("r", "").replace("n","").replace("t", "")

            print("입찰마감 : ", end_date)

            # 공고일
            content_announce_date = content.select('li.m2>span')
            announce_date = str(content_announce_date[0].find_all(text=True))
            announce_date = re.sub("[\[\'\]\\\]", "", announce_date)
            announce_date = announce_date.replace("r", "").replace("n", "").replace("t", "")
            print("공고일 : ", announce_date)

            # 개찰일
            content_open_date = content.select('li.m3>span')
            open_date = str(content_open_date[0].find_all(text=True))
            open_date = re.sub("[\[\'\]\\\]", "", open_date)
            open_date = open_date.replace("r", "").replace("n", "").replace("t", "")
            print("개찰일 : ", open_date)

            # 수요기관
            content_demand_agency = content.select('li.m4>span')
            demand_agency = str(content_demand_agency[0].find_all(text=True))
            #demand_agency = clean_text(demand_agency)
            #print("수요기관 : ", demand_agency)
            demand_agency = re.sub("[\[\'\]\\\]", "", demand_agency)
            print("수요기관 : ", demand_agency)

            # 공고기관
            content_public_agency = content.select('ul.info>li')
            public_agency = str(content_public_agency[0].find_all(text=True))
            #print("공고기관 : ", public_agency)
            public_agency = clean_text(public_agency)

            #public_agency = re.sub("[\r\n\t]", "", public_agency)
            public_agency = public_agency.replace("r", "").replace("t", "").replace("n", "").replace(" 공고기관  ", "")
            print("공고기관 : ", public_agency)

            collection_test.insert_one(
                {
                    'support_title' : title,
                    'support_detail_url' : content_detail_URL,
                    'support_end_date' : end_date,
                    'support_announce_date' : announce_date,
                    'support_open_date' : open_date,
                    'suuport_demand_agency' : demand_agency,
                    'support_public_agency' : public_agency
                }
            )

            get_info_from_detail_link(content_detail_URL)
    except Exception as ex:
        print("ERROR 발생", ex)
        return None

# 상세 링크 통해서 상세 정보 가져오기
def get_info_from_detail_link(URL):
    down_link = ""
    get_file_from_link(down_link)

# 파일 다운로드
def get_file_from_link(URL):
    print("File Download Hello")

    with open("test.xlsx", "wb") as file:
        response = requests.get("http://www.g2b.go.kr:8081/ep/co/fileDownload.do?fileTask=NOTIFY&fileSeq=20190231142::00::2::4")
        file.write(response.content)

def main():
    get_info_from_g2b_title()

if __name__ == '__main__':
    main()