from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import csv
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException

# todo 날짜별로 구분해서 크롤링 가능하게


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=360x740')

driver = webdriver.Chrome('driver/chromedriver', chrome_options=options)
driver.set_window_size(360, 740)
driver.get('https://daejin.everytime.kr/login')
print('dirver up')
id = input('id: ')
pw = input('pw: ')
driver.find_element_by_name('userid').send_keys(id)
driver.find_element_by_name('password').send_keys(pw)
driver.find_element_by_class_name('submit').click()

start_date = input('date to start(2020-01-01): ')
s_year, s_month, s_day = map(int, start_date.split('-'))
start_datetime = datetime(s_year, s_month, s_day)
end_date = input('date to end(2020-01-01): ')
e_year, e_month, e_day = map(int, end_date.split('-'))
end_datetime = datetime(e_year, e_month, e_day)

# 테스트용
driver.find_element_by_name('userid').send_keys(id)
driver.find_element_by_name('password').send_keys(pw)
driver.find_element_by_class_name('submit').click()
s_year, s_month, s_day = map(int, start_date.split('-'))
start_datetime = datetime(s_year, s_month, s_day)
e_year, e_month, e_day = map(int, end_date.split('-'))
end_datetime = datetime(e_year, e_month, e_day)
post_datetime = None


def make_link():
    page = 1
    links = []
    start_time = time.time()

    is_loop_end = False
    while not is_loop_end:
        driver.get('https://daejin.everytime.kr/384377/p/' + str(page))
        try:
            WebDriverWait(driver, 200).until(EC.presence_of_all_elements_located((By.ID, "writeArticleButton")))
        except TimeoutException:
            continue
        req = driver.page_source
        soup = BeautifulSoup(req, 'html.parser')
        # todo time 태그 찾아서 오늘 날짜 이후로 일주일 단위 검색

        linkList = soup.findAll("a", href=re.compile("(\/384377\/v\/........)"))
        # # 마지막 페이지인지 확인
        # if len(linkList) < 20:
        #     break
        #
        # 테스트용
        # if page == 4:
        #     break

        for link in linkList:
            links.append(link.attrs['href'])
        print(page)



        # 한번에 한페이지씩 크롤링하기 위해 추가
        now = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
        for find_time in soup.findAll("time"):
            if '분 전' in find_time.text or '방금' in find_time.text:
                # 오늘 날짜에 올라온 데이터
                post_datetime = now
                now = post_datetime
            elif len(find_time.text) == 11:
                p_month, p_day = map(int, find_time.text[0:5].split('/'))
                post_datetime = datetime(2020, p_month, p_day)
                now = post_datetime
            else:
                p_year, p_month, p_day = map(int, find_time.text[0:9].split('/'))
                post_datetime = datetime(p_year, p_month, p_day)
                now = post_datetime
            if now <= start_datetime:
                if '분 전' in find_time.text or '방금' in find_time.text:
                    # 오늘 날짜에 올라온 데이터
                    post_datetime = now
                    crawling(links.pop())
                else:
                    p_month, p_day = map(int, find_time.text[0:5].split('/'))
                    post_datetime = datetime(2020, p_month, p_day)
                    now = post_datetime
                    crawling(links.pop())


            # elif now > start_datetime:
            #     pass
            #     if len(find_time.text) == 11:
            #         p_month, p_day = map(int, find_time.text[0:5].split('/'))
            #         post_datetime = datetime(2020, p_month, p_day)
            #         print(p_month, p_day)
            #     else:
            #         p_year, p_month, p_day = map(int, find_time.text[0:9].split('/'))
            #         post_datetime = datetime(p_year, p_month, p_day)
            #     crawling(links.pop())
            if post_datetime is not None:
                if post_datetime < end_datetime:
                    is_loop_end = True
        # while True:
        #
        #     if not links:
        #         break
        # crawling(links.pop())

        if time.time() - start_time > 3600:
            driver.delete_all_cookies()
            driver.get('https://daejin.everytime.kr/login')
            print('session clear')
            driver.find_element_by_name('userid').send_keys(id)
            driver.find_element_by_name('password').send_keys(pw)
            driver.find_element_by_class_name('submit').click()
            start_time = time.time()

        page += 1


def crawling(link):
    driver.get('https://daejin.everytime.kr' + str(link))
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#container > "
                                                                                              "div.articles > article"
                                                                                              " > a.article")))
    except TimeoutException:
        return
    req = driver.page_source
    soup = BeautifulSoup(req, 'html.parser')
    title_time = soup.find('div', {'class': 'profile'}).find('time').text
    # ~분전이라고 표시되는 개시물이 존재함
    if '분' in title_time:
        time_to_int = int(re.findall('\d+', title_time)[0])
        now = datetime.now()
        after = now + timedelta(minutes=-time_to_int)
        title_time = str(after.month) + '/' + str(after.day) + ' ' + str(after.hour) + ':' + str(after.minute)
    elif '방금' in title_time:
        now = datetime.now()
        title_time = str(now.month) + '/' + str(now.day) + ' ' + str(now.hour) + ':' + str(now.minute)

    title = soup.find('div', {'class': 'wrap articles'}).article.h2.text
    writeCSV('title', title, title_time)
    content = soup.find('div', {'class': 'wrap articles'}).article.a.p.text
    writeCSV('content', content)
    for commentObj in soup.find('div', {'class': 'comments'}).children:
        try:
            comment = commentObj.find('p').text
            comment_time = commentObj.find('time').text
            if '분' in comment_time:
                time_to_int = int(re.findall('\d+', comment_time)[0])
                now = datetime.now()
                after = now + timedelta(minutes=-time_to_int)
                comment_time = str(after.month) + '/' + str(after.day) + ' ' + str(after.hour) + ':' + str(after.minute)
            elif '방금' in comment_time:
                now = datetime.now()
                comment_time = str(now.month) + '/' + str(now.day) + ' ' + str(now.hour) + ':' + str(now.minute)

            writeCSV('comment', comment, comment_time)
        except AttributeError:
            pass

    print(link)


def writeCSV(text_type, content, date=None):
    f = open('output.csv', 'a', encoding='utf-8', newline='')
    wr = csv.writer(f)
    if date is None:
        wr.writerow([text_type, content])
    else:
        wr.writerow([text_type, content, date])


make_link()
print('끝')
driver.close()
