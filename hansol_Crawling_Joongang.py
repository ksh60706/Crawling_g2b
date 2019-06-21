import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import sys
from pymongo import MongoClient
import requests
import lxml.html

TARGET_URL_BEFORE_KEYWORD = "http://nsearch.chosun.com/search/total.search?sort=1"
TARGET_URL_KEYWORD = "&query="
TARGET_URL_PAGENO = "&pn="


# 정규화 처리
def clean_text(text):
    # cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text


def normalize_spaces(text):
    '''
    연결되 있는 공백을 하나의 공백으로 변경
    :param text:
    :return:
    '''
    return re.sub(r'\s+', ' ', text).strip()


# 페이지 리스트 추출 함수
# 제목, 상세 페이지 URL, 내용
def get_detail_url_from_list(URL):
    '''
    :param URL: 검색결과 url
    :return: 상세 페이지의 URL
    '''
    URL = "http://nsearch.chosun.com/search/total.search?query=%ED%95%9C%EC%86%94&sort=1&pn=1"
    # print('def1')
    try:
        # print('def2')
        # source_code_from_URL = urllib.request.urlopen(URL)
        '''
        soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')
        print('def3')
        for content in soup.select('div.search_news_box > dl.search_news'):
            print('def4')
            print("소스 : "+str(content))
            # 제목
            content_title = content.select('dt > a')
            print("제목 : " + str(content_title))

            # 분류
            content_kind = content.select('dd.art_info > a')
            content_kind = str(content_kind[0].find_all(text=True))
            print("분류 : " + content_kind)

            # 상세 URL
            #content_URL =

            # 게시일
            content_date = content.select('dd.art_info > span.date')
            print("게시일 : " + content_date)

        soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')
        print('def3')
        for content in soup.find_all('div.search_news_box > dl.search_news'):
            print("소스 : " + str(content))
        '''

        response = requests.get(URL)
        root = lxml.html.fromstring(response.content)
        for a in root.cssselect('dl.search_news > dt > a'):
            url = a.get('href')
            yield url

    except Exception as ex:
        print("에러발생", ex)
        return None


# 페이지 상세 데이터 함수
def get_content_from_link(URL):
    '''
    :param URL: 상세페이지 url
    :return:  크롤링 내용
    '''
    print(URL)

    try:
        response = requests.get(URL)
        root = lxml.html.fromstring(response.content)
        print("제목 : ", root.cssselect('#news_title_text_id')[0].text_content())
        mainContent = ""
        for p in root.cssselect('.par'):
            mainContent = mainContent + p.text_content()
            mainContent = normalize_spaces(mainContent)

        # print("내용 : ", normalize_spaces(root.cssselect('.par').text_content()))
        print("내용 : ", mainContent)
        '''
        print("내용 : ", [
            normalize_spaces(p.text_content())
            for p in root.cssselect('.par')[0]
            if normalize_spaces(p.text_content()) != ''
        ])
        '''
        print("날짜 : ", normalize_spaces(root.cssselect('.news_date')[0].text_content()))
        news = {
            'kind': '조선일보',
            'title': root.cssselect('#news_title_text_id')[0].text_content(),
            'url': URL,
            'content': root.cssselect('.par')[0].text_content(),
            'newsDate': root.cssselect('.news_date')[0].text_content()
        }
        return news

    except Exception as ex:
        print('에러발생', ex)
        return None


# DB 연결 함수
def db_conn():
    conn = MongoClient('127.0.0.1')
    db = conn.DB_CRAWLING
    return db


# 메인 함수
def main():
    print('hello')
    target_keyword = ""
    target_pageNo = ""

    TARGET_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + target_keyword + TARGET_URL_PAGENO + target_pageNo

    urls = get_detail_url_from_list(TARGET_URL)

    db = db_conn()
    collection = db.news

    for url in urls:
        content = get_content_from_link(url)
        collection.insert_one(content)


if __name__ == '__main__':
    main()