import time
from selenium import webdriver
import json
from selenium.webdriver.edge.options import Options
import os
import pandas as pd
import sys


def getcookies(wangzhi,cunchupath):
    browser = webdriver.Edge()
    browser.get(wangzhi)
    # 程序打开网页后60秒内 “你自己手动登陆账户”
    time.sleep(60)

    with open(cunchupath, 'w') as f:
        # 将 cookies 保存为 json 格式
        f.write(json.dumps(browser.get_cookies()))
    browser.close()

def duqucookies(duqupath,driver):  # 参数为读取路径，和对应浏览器的driver
    driver.delete_all_cookies()
    with open(duqupath, 'r') as f:
        cookies_list = json.load(f)
        for cookie in cookies_list:
            if isinstance(cookie.get('expiry'), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)

def drivershengcheng(path,cookies = False ,tanchu = True,keepon = False):
    if tanchu == False:
        edge_options = Options()
        edge_options.add_argument('--headless')
        edge_options.add_argument('--disable-gpu')
        edge_options.add_experimental_option('detach',keepon)

        driver = webdriver.Edge(edge_options)  # 设置不弹出浏览器要记得加上options
        driver.get(path)
        if cookies != False:
            duqucookies(cookies, driver)
        time.sleep(3)
    else:
        edge_options = Options()
        edge_options.add_experimental_option('detach', keepon)

        driver = webdriver.Edge()
        driver.get(path)
        if cookies != False:
            duqucookies(cookies, driver)
        time.sleep(3)
    return driver

def xieru(file_path,data,mode):
    if not os.path.exists(file_path):
        # 如果文件不存在，创建文件
        with open(file_path, 'w') as f:
            pass  # 创建一个空文件
        print(f"文件已创建：{file_path}")
    if mode == 'a':
        existing_df = pd.read_excel(file_path)
        combined_df = pd.concat([existing_df, data], ignore_index=True)
        combined_df.to_excel(file_path, index=False)
    elif mode == 'w':
        data.to_excel(file_path, index=False)