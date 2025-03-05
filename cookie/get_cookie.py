import time
from selenium import webdriver
import json

browser = webdriver.Edge()
browser.get(f'https://www.zhipin.com/web/geek/job?query=%E6%AC%A3%E6%97%BA%E8%BE%BE%E7%94%B5%E5%AD%90&city=101180100')
# 程序打开网页后60秒内 “你自己手动登陆账户”
time.sleep(15)

with open('bosscookies5.txt', 'w') as f:
    # 将 cookies 保存为 json 格式
    f.write(json.dumps(browser.get_cookies()))
    print(browser.session_id)
browser.close()