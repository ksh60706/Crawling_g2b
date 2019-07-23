import urllib.request
# from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import sys
from pymongo import MongoClient
import requests
import lxml.html
from elasticsearch import Elasticsearch
import json

import datetime

from konlpy.tag import Kkma

# 어제 날짜 구하기
YESTERDAY_DATE = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d")

# 유동적으로 변할 URL 주소 설정
TARGET_URL_BEFORE_KEYWORD = "http://nsearch.chosun.com/search/total.search?sort=1"
TARGET_URL_KEYWORD = "&query="
TARGET_URL_START_DATE = "&date_start="
TARGET_URL_END_DATE = "&date_end="
TARGET_URL_PAGENO = "&pn="

MONGO_USER_NAME = "IDCRAWLING"
MONGO_USER_PASSWORD = "Hanhdwas200!"

# 검색 키워드
target_keyword = "한솔제지"

kkma = Kkma()


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

def check_page_count(URL):
    '''

    :param url: 해당 url로 접속하여 페이지 수 파악하기
    :return: 전체 페이지 수
    '''
    #print(URL)
    try :
        response = requests.get(URL)
        root = lxml.html.fromstring(response.content)
        totalCnt = root.cssselect('div.count_box')[0].text_content()
        totalCnt = str(totalCnt.split("건")[0])
        #print("총 건수 : "+totalCnt)
        pageCnt = (int(totalCnt) // 10) + 1
        #print("총 페이지수 : " + str(pageCnt))
        return pageCnt
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
    #URL = "http://nsearch.chosun.com/search/total.search?query=%ED%95%9C%EC%86%94&sort=1&pn=1"
    #print('def1')
    #print(URL)
    try :
        #print('def2')
        #source_code_from_URL = urllib.request.urlopen(URL)


        response = requests.get(URL)
        root = lxml.html.fromstring(response.content)
        for a in root.cssselect('dl.search_news > dt > a'):
            url = a.get('href')
            yield url

    except Exception as ex:
        print("에러발생1", ex)
        return None




# 페이지 상세 데이터 함수
def get_content_from_link(URL):
    '''
    :param URL: 상세페이지 url
    :return:  크롤링 내용
    '''
    #print(URL)

    blackListArticle = ['newsteacher', 'edu', 'kid', 'baby', 'photo']

    checkURL = URL.split(".")
    if checkURL[0][7:] in blackListArticle:
        '''
        print(checkURL[0][7:])
        print("주소는 : ",URL)
        news = {
            "crawling_type": "뉴스",
            "crawling_company": "조선일보",
            "crawling_keyword": target_keyword,
            "crawling_title": "",
            "crawling_url": URL,
            "crawling_content": "",
            "crawling_newsDate": ""
        }
        return news
        '''
        return None

    else:

        try :
            response = requests.get(URL)
            root = lxml.html.fromstring(response.content)
            #print("제목 : ", root.cssselect('#news_title_text_id')[0].text_content())
            mainContent = ""
            for p in root.cssselect('.par'):
                mainContent = mainContent + p.text_content()
                mainContent = normalize_spaces(mainContent)

            #print("내용 : ", normalize_spaces(root.cssselect('.par').text_content()))
            #print("내용 : ", mainContent)
            '''
            print("내용 : ", [
                normalize_spaces(p.text_content())
                for p in root.cssselect('.par')[0]
                if normalize_spaces(p.text_content()) != ''
            ])
            '''
            #print("날짜 : ", normalize_spaces(root.cssselect('.news_date')[0].text_content()))

            if not root.cssselect('#news_title_text_id'):
                title = ""
            else:
                title = root.cssselect('#news_title_text_id')[0].text_content()

            if not root.cssselect('.par'):
                content = ""
            else:
                content = kkma.nouns(root.cssselect('.par')[0].text_content())

            if not root.cssselect('.news_date'):
                newsDate = ""
            else:
                newsDate_tag = root.cssselect('.news_date')[0].text_content()
                newsDate = datetime.datetime.strptime(newsDate_tag.replace("입력 ","").replace(".","-") + ":00", "%Y-%m-%d %H:%M:%S")

            news={
                "crawling_type": "뉴스",
                "crawling_company": "조선일보",
                "crawling_keyword": target_keyword,
                "crawling_title": title,
                "crawling_url": URL,
                "crawling_content": content,
                "crawling_newsDate": newsDate
            }
            return news

        except Exception as ex :
            print('에러발생2', ex)
            return None



# DB 연결 함수
def db_conn():
    
    # 로컬 피씨
    #conn = MongoClient('127.0.0.1')
    #db = conn.DB_CRAWLING
    
    # 테스트 서버 
    #conn = MongoClient('127.0.0.1')
    #db = conn.DBCRAWLING

    # 운영
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

# 메인 함수
def main():



    #TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_START_DATE + str(YESTERDAY_DATE) + TARGET_URL_END_DATE + str(YESTERDAY_DATE) + TARGET_URL_PAGENO + str(1)
    TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGENO + str(1)
                 #+ TARGET_URL_START_DATE + str(YESTERDAY_DATE) + TARGET_URL_END_DATE + str(YESTERDAY_DATE)

    print(TARGET_URL)

    # 페이지 수 파악
    target_pageNo = check_page_count(TARGET_URL)
    #target_pageNo = 91
    #print("폐이지수파악 끝 "+str(target_pageNo))

    db = db_conn()

    # 운영
    collection = db.NEWS_HANSOL_WORDS

    # 로컬
    #collection = db.NEWS_HANSOL

    es = es_conn()

    for i in range(0, target_pageNo):
        print(str(i+1)+"번쨰 ")
        #TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_START_DATE + str(YESTERDAY_DATE) + TARGET_URL_END_DATE + str(YESTERDAY_DATE) + TARGET_URL_PAGENO + str(i+1)

        TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGENO + str(i + 1)

        print(TARGET_URL)
        urls = get_detail_url_from_list(TARGET_URL)


        for url in urls:
            content = get_content_from_link(url)

            if not content:
                print("패스")
            else:
                # print("content 첫번째 : ", content)
                # print(type(content))
                # print(json.dumps(content))
                # print(type(json.dumps(content)))
                #content_json = json.dumps(content)
                content_json = content
                # print(content_json)
                
                # 엘라스틱 데이터 입력
                es.index(index="crawling_testtt_words", body=content_json,
                         id=content["crawling_url"].split("/")[-1].replace(".html", ""))

                # print("content 두번쨰 : ", content)
                # 디비 데이터 입력
                collection.insert_one(content)





if __name__ == '__main__':
    main()