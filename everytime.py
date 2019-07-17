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


def make_link():
    page = 1
    links = []
    start_time = time.time()
    while True:
        driver.get('https://daejin.everytime.kr/384377/p/'+str(page))
        try:
            WebDriverWait(driver, 200).until(EC.presence_of_all_elements_located((By.ID, "writeArticleButton")))
        except TimeoutException:
            continue
        req = driver.page_source
        soup = BeautifulSoup(req, 'html.parser')
        linkList = soup.findAll("a", href=re.compile("(\/384377\/v\/........)"))
        # 마지막 페이지인지 확인
        if len(linkList) < 20:
            break

        # 테스트용
        # if page == 4:
        #     break

        for link in linkList:
            links.append(link.attrs['href'])
        print(page)

        # 한번에 한페이지씩 크롤링하기 위해 추가
        while True:
            if not links:
                break
            crawling(links.pop())

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
        title_time = str(after.month)+'/'+str(after.day)+' '+str(after.hour)+':'+str(after.minute)
    elif '방금' in title_time:
        now = datetime.now()
        title_time = str(now.month)+'/'+str(now.day)+' '+str(now.hour)+':'+str(now.minute)

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
