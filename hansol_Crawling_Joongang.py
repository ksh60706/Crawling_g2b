from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import sys
from pymongo import MongoClient
import requests
import lxml.html
from elasticsearch import Elasticsearch
import json

import datetime

# 어제 날짜 구하기
YESTERDAY_DATE = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d")

# 유동적으로 변할 URL 주소 설정
TARGET_URL_BEFORE_KEYWORD = "https://search.joins.com/TotalNews?SortType=New&SearchCategoryType=TotalNews"
TARGET_URL_KEYWORD = "&Keyword="
TARGET_URL_START_DATE = "&PeriodType=DirectInput&StartSearchDate="
TARGET_URL_END_DATE = "&EndSearchDate="
TARGET_URL_PAGENO = "&page="

MONGO_USER_NAME = "IDCRAWLING"
MONGO_USER_PASSWORD = "Hanhdwas200!"

# 검색 키워드
target_keyword = "한솔제지"




# 정규화 처리
def clean_text(text):
    #cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text

def normalize_spaces(text):
    '''
    연결되 있는 공백을 하나의 공백으로 변경
    :param text:
    :return:
    '''
    return re.sub(r'\s+', ' ', text).strip()

# DB 연결 함수
def db_conn():
    #conn = MongoClient('127.0.0.1')
    #db = conn.DB_CRAWLING

    conn = MongoClient("mongodb://" + MONGO_USER_NAME + ":" + MONGO_USER_PASSWORD + "@localhost:27017/?authSource=DBCRAWLING")
    db = conn['DBCRAWLING']

    print("디비연결 완료")
    return db

# ES 연결 함수
def es_conn():

    # 로컬 피씨
    #conn = Elasticsearch(hosts="127.0.0.1", port=9200)

    conn = Elasticsearch(hosts="168.1.1.195", port=9200)
    print("ES연결 완료")
    return conn

def check_page_count(URL):
    '''
    :param url: 해당 url로 접속하여 페이지 수 파악하기
    :return: 전체 페이지 수
    '''

    try :
        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        total_tag = soup.select("span.total_number")[0].text
        total = total_tag.split(" / ")[0].split("-")[1]
        #print(int(total))

        return int(total)
    except Exception as ex:
        print("페이지수 파악 에러 발생", ex)
        return None




# 페이지 리스트 추출 함수
# 제목, 상세 페이지 URL, 내용
def get_detail_url_from_list(URL):
    '''
    :param URL: 검색결과 url
    :return: 상세 페이지의 URL
    '''
    try :
        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        #print(soup)
        #print(soup.find_all("h2.headline > a"))
        #print(soup.select("h2.headline > a"))
        for link in soup.select("h2.headline > a"):
            #print(link)
            url = link.get("href")
            #print(url)
            yield url

        #url_tag = soup.select("h2.headline > a")
        #url = url_tag.get("href")
        #print(url)
        #yield url

    except Exception as ex:
        print("페이지 상세 URL 파악 에러 발생", ex)
        return None





# 페이지 상세 데이터 함수
def get_content_from_link(URL):
    '''
    :param URL: 상세페이지 url
    :return:  크롤링 내용
    '''
    try :
        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        title = soup.select_one("h1#article_title").text
        # print(title)

        # print(URL)
        content = normalize_spaces(soup.select_one("div#article_body").text).split(" ")
        #print(content)

        newsDate_tag = soup.select("div.article_head > div.clearfx > div.byline > em")[1].text
        #print(newsDate_tag)
        newsDate = newsDate_tag.replace("입력 ", "")
        #print(newsDate)

        news = {
            "crawling_type": "뉴스",
            "crawling_company": "중앙일보",
            "crawling_keyword": target_keyword,
            "crawling_title": title,
            "crawling_url": URL,
            "crawling_content": content,
            "crawling_newsDate": newsDate
        }
        return news

    except Exception as ex :
        print("상세 내용 파악 에러 발생", ex)
        return None



# 메인 함수
def main():

    # 페이지 수 확인
    TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGENO # 전체
    target_pageNo = check_page_count(TARGET_URL + str(1))
    #target_pageNo = 2

    TARGET_URL = ""

    # 디비연결
    #db = db_conn()
    #collection = db.NEWS_HANSOL

    # 엘라스틱서치 연결
    es = es_conn()



    # 상세 URL 가져오기
    for i in range(0, target_pageNo):
        print(str(i + 1) + "번쨰 ")

        TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGENO + str(i + 1)

        print(TARGET_URL)
        urls = get_detail_url_from_list(TARGET_URL)

        # 상세 내용 가져오기
        for url in urls:
            #print(url)
            get_content_from_link(url)
            content = get_content_from_link(url)

            # 엘라스틱 데이터 입력
            content_json = json.dumps(content)
            es.index(index="crawling_testtt_nori", body=content_json,
                     id=content["crawling_url"].split("/")[-1])


            # 디비 데이터 입력
            #collection.insert_one(content)









if __name__ == '__main__':
    main()