import urllib.request
from urllib.request import HTTPError
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import sys
from datetime import datetime

from pymongo import MongoClient


# 조선일보는 한페이지당 10개이지만
# pageno가 페이지 수로 바뀜 (pageno=1, 2, 3, 4, ...)
TARGET_URL_BEFORE_KEYWORD = "http://search.chosun.com/search/news.search?pageno="
TARGET_URL_KEYWORD = "&query="
#TARGET_URL_REST = "&orderby=news&naviarraystr=&kind=&cont1=&cont2=&cont5=&categoryname=&categoryd2=&c_scope=paging&sdate=&edate=&premium="
TARGET_URL_BEFORE_SDATE = "&orderby=news&naviarraystr=&kind=&cont1=&cont2=&cont5=&categoryname=&categoryd2=&c_scope=paging"
TARGET_URL_SDATE = "&sdate="
TARGET_URL_EDATE = "&edate="
TARGET_URL_REST = "&premium="

# db
conn = MongoClient('127.0.0.1')
db = conn.test_db
collect_test = db.collect_test


# db 입력용 변수
DB_KIND = "news"
DB_NEWS_KIND = "chosun"
DB_SEARCH_TITLE = "오크밸리"

# 클러스터링 함수
def clean_text(text):
    #cleaned_text = re.sub('[a-zA-Z]', '', text)
    #cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]','',cleaned_text)
    cleaned_text = re.sub('[\{\}\[\]\/?.,;:|\)*~!^\-_+<>@\#$%&\\\=\(\'\"]', '', text)
    return cleaned_text

# 목록에서 링크 가져오기
def get_link_from_news_title(page_num, URL, output_file):
    for i in range(page_num):
        current_page_num = i+1
        position = URL.index('=')


        URL_with_page_num = URL[: position+1] + str(current_page_num) \
                            + URL[position+1 :]
        print("url : ", URL_with_page_num)

        try:

            souce_code_from_URL = urllib.request.urlopen(URL_with_page_num)
            soup = BeautifulSoup(souce_code_from_URL, 'lxml', from_encoding='utf-8')


            for title in soup.find_all('dl', 'search_news'):
                title_link = title.select('dt > a')

                article_title = str(title_link[0].find_all(text=True))
                print("제목:",clean_text(article_title))
                article_URL = title_link[0]['href']

                content = get_text_from_link(article_URL, output_file)
                print("내용:",content)

                #collect_test.insert({'title':clean_text(article_title), 'content':content})
                collect_test.insert(
                    {
                        'search_title' : DB_SEARCH_TITLE,
                        'search_lvl1' : DB_KIND,
                        'search_lvl2' : DB_NEWS_KIND,
                        'search_lvl3' : '',
                        'article_title' : clean_text(article_title),
                        'article_content' : content
                    }
                )

        except HTTPError as e:
            print(e)




# 링크에서 제목과 내용 가져오기
def get_text_from_link(URL, output_file):

    try:
        print(URL)
        source_code_from_url = urllib.request.urlopen(URL)
        soup = BeautifulSoup(source_code_from_url, 'lxml', from_encoding='utf-8')
        #title_of_article = str(soup.select_one('h1#news_title_text_id').find_all(text=True))
        #print('제목은 : ', title_of_article)
        content_of_article = soup.select('div.par')
        #print('내용은 : ', content_of_article)
        content = ""

        for item in content_of_article:
            string_item = str(item.find_all(text=True))
            print("ITEM:", item)
            print("STRING_ITEM:", string_item)
            content = content + string_item
            content = clean_text(content)
            output_file.write(string_item)


        #print('내용 : ',content)
        #print('내용은 : ', clean_text(content))
        return content

    except:
        return None
    """
    except HTTPError as e:
        #print(e)
        return None
    """


# 메인 함수
def main(argv):
    """if len(argv) != 4:
        print("python [모듈이름] [키워드] [가져올 페이지 숫자] [결과 파일명]")
        return
    keyword = argv[1]
    page_num = int(argv[2])
    output_file_name = argv[3]
    """
    print("금일 날짜 : ", datetime.today().strftime("%Y.%m.%d"))

    todDate = datetime.today().strftime("%Y.%m.%d")
    keyword = '오크밸리'
    page_num = 28
    output_file_name = 'output_cho.txt'
    target_URL = TARGET_URL_BEFORE_KEYWORD + TARGET_URL_KEYWORD + quote(keyword) \
                  + TARGET_URL_BEFORE_SDATE + TARGET_URL_SDATE \
                 + TARGET_URL_EDATE \
                 + TARGET_URL_REST
    output_file = open(output_file_name, 'w')
    get_link_from_news_title(page_num, target_URL, output_file)
    output_file.close()


# 실행
if __name__ == "__main__":
    main(sys.argv)