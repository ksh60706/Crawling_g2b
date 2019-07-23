from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
import requests
from elasticsearch import Elasticsearch
import json
import datetime

from konlpy.tag import Kkma

# 어제 날짜 구하기
YESTERDAY_DATE = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d")

# 유동적으로 변할 URL 주소 설정
TARGET_URL_BEFORE_KEYWORD = "http://www.donga.com/news/search?check_news=1&more=1&sorting=1&v1=&v2=&range=1"
TARGET_URL_KEYWORD = "&query="
# 날짜 형식 (YYYYMMDD)
TARGET_URL_START_DATE = "&search_date=1&v1="
TARGET_URL_END_DATE = "&v2="
TARGET_URL_PAGE_NO = "&p="

MONGO_USER_NAME = "IDCRAWLING"
MONGO_USER_PASSWORD = "Hanhdwas200!"

# 검색 키워드
target_keyword = "한솔제지"

kkma = Kkma()


# 정규화 처리
def clean_text(text):
    # cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    #cleaned_text = re.sub("<.+?>", "", text, 0).strip()
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
    try:
        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        total_tag = soup.select("div.searchCont > h2 > span")[0].text
        total_cnt = total_tag.split(" ")[1]

        total = ( int(total_cnt) // 15 ) + 1
        print(total)
        return total
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

    try:

        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("p.tit > a"):
            url = link.get("href")
            yield url

    except Exception as ex:
        print("페이지 상세 URL 파악 에러 발생", ex)
        return None

# 페이지 상세 데이터 함수
def get_content_from_link(URL):
    '''
    :param URL: 상세페이지 url
    :return:  크롤링 내용
    '''

    content = ""
    #f = open("C:\\Users\KSH\PycharmProjects\Crawling_g2b\형태소분석.txt", "w")
    #f.write("시작 : ")
    try:
        html = requests.get(URL).text
        soup = BeautifulSoup(html, "html.parser")

        title = soup.select_one("div.article_title > h1.title").text


        '''
        for item in content_tag:
            string_item = str(item.find_all(text=True))
            content = normalize_spaces(string_item)
            #content = normalize_spaces(content + clean_text(string_item))
        print("콘텐츠는 : ",content)
        '''


        #for i in kkma.pos(normalize_spaces(soup.select_one("div.article_txt").text)):
        #for i in kkma.nouns(normalize_spaces(soup.select_one("div.article_txt").text)):
        #    f.write(str(i)+"\n")
        #f.write(kkma.pos(normalize_spaces(soup.select_one("div.article_txt").text)))

        #content = normalize_spaces(soup.select_one("div.article_txt").text).split(" ")
        content = kkma.nouns(normalize_spaces(soup.select_one("div.article_txt").text))

        newsDate_tag = soup.select("div.title_foot > span.date01")[0].text
        #newsDate = datetime.datetime.strptime( newsDate_tag.replace("입력 ","")+":00", "%Y-%m-%d %H:%M:%S")
        newsDate = newsDate_tag.replace("입력 ","")+":00"
        news = {
            "crawling_type": "뉴스",
            "crawling_company": "동아일보",
            "crawling_keyword": target_keyword,
            "crawling_title": title,
            "crawling_url": URL,
            "crawling_content": content,
            "crawling_newsDate": newsDate
        }
        #f.close()
        return news

    except Exception as ex:
        print("상세 내용 파악 에러 발생", ex)
        return None

# 메인 함수
def main():


    # 페이지 수 확인
    TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword
    target_pageNo = check_page_count(TARGET_URL)
    #target_pageNo = 1

    #TARGET_URL = ""

    # 디비연결
    db = db_conn()
    collection = db.NEWS_HANSOL_WORDS

    # 엘라스틱서치 연결
    es = es_conn()

    # 상세 URL 가져오기
    for i in range(0, target_pageNo):
        print(str(i+1)+"번째 ")

        TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGE_NO + str(15*i + 1)

        print(TARGET_URL)
        urls = get_detail_url_from_list(TARGET_URL)

        for url in urls:
            content = get_content_from_link(url)

            # 엘라스틱 데이터 입력
            content_json = json.dumps(content)
            es.index(index="crawling_testtt_words", body=content_json, id=content["crawling_url"].split("/all/")[1].replace('/','-'))

            # 디비 데이터 입력
            collection.insert_one(content)

            # 형태소 분석
            #print(kkma.pos(content[]))




if __name__ == '__main__':
    main()