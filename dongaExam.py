"""
동아일보 특정 키워드를 포함하는 특정 날짜 이전 기사 내용 크롤러 (정확도순 검색)
python [모듈 이름] [키워드] [가져올 페이지 숫자] [결과 파일명]
한 페이지에 기사 15개
"""
import re
import sys
from bs4 import BeautifulSoup
import urllib.request
from urllib.request import HTTPError
from urllib.parse import quote

from pymongo import MongoClient

TARGET_URL_BEFORE_PAGE_NUM = "http://news.donga.com/search?p="
TARGET_URL_BEFORE_KEYWORD = "&query="
TARGET_URL_REST = '&check_news=1&more=1&sorting=1&search_date=&range=1'

# DB 연결
conn = MongoClient('127.0.0.1')
db = conn.test_db
collect_test = db.collect_test

# db 입력용 변수
DB_KIND = "news"
DB_NEWS_KIND = "donga"
DB_SEARCH_TITLE = "오크밸리"


# 클러스터링 함수
def clean_text(text):
    #cleaned_text = re.sub('[a-zA-Z]', '', text)
    #cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]','',cleaned_text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text

# 기사 검색 페이지에서 기사 제목에 링크된 기사 본문 주소 받아오기
def get_link_from_news_title(page_num, URL, output_file):
    for i in range(page_num):
        current_page_num = 1 + i*15
        position = URL.index('=')
        URL_with_page_num = URL[: position+1] + str(current_page_num) \
                            + URL[position+1 :]
        print("URL : ", URL_with_page_num)

        try:
            source_code_from_URL = urllib.request.urlopen(URL_with_page_num)
            soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')

            for title in soup.find_all('p', 'tit'):
                title_link = title.select('a')

                article_title = str(title_link[0].find_all(text=True))
                article_title = clean_text(article_title)
                print("제목 : ",article_title)
                article_URL = title_link[0]['href']

                article_content = get_text_from_link(article_URL, output_file)
                print("내용 : ", article_content)

                collect_test.insert(
                    {
                        'search_title': DB_SEARCH_TITLE,
                        'search_lvl1': DB_KIND,
                        'search_lvl2': DB_NEWS_KIND,
                        'search_lvl3': '',
                        'article_title': article_title,
                        'article_content': article_content
                    }
                )
        except:
            return None

# 기사 본문 내용 긁어오기 (위 함수 내부에서 기사 본문 주소 받아 사용되는 함수
def get_text_from_link(URL, output_file):
    source_code_from_url = urllib.request.urlopen(URL)
    soup = BeautifulSoup(source_code_from_url, 'lxml', from_encoding='utf-8')
    content_of_article = soup.select('div.article_txt')

    content = ""
    for item in content_of_article:
        string_item = str(item.find_all(text=True))
        content = clean_text(string_item)
        #print("STRING_ITEM:", string_item)

        output_file.write(string_item)

    return content

# 메인함수
def main(argv):
    """
    if len(argv) != 4:
        print("python [모듈이름] [키워드] [가져올 페이지 숫자] [결과 파일명]")
        return
    """
    #keyword = argv[1]
    #page_num = int(argv[2])
    #output_file_name = argv[3]
    keyword = '오크밸리'
    page_num = 17
    output_file_name = 'output_dong.txt'
    target_URL = TARGET_URL_BEFORE_PAGE_NUM + TARGET_URL_BEFORE_KEYWORD \
                    + quote(keyword) + TARGET_URL_REST
    output_file = open(output_file_name, 'w')
    get_link_from_news_title(page_num, target_URL, output_file)
    output_file.close()

if __name__ == '__main__':
    main(sys.argv)