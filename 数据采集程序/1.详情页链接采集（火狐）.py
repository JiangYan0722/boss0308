import time
import openpyxl
from selenium.webdriver.common.by import By
import pandas as pd
from tools import *
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import requests
import random
import json
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm  # 导入tqdm库
from concurrent.futures import ThreadPoolExecutor  # 导入线程池

links = []

# 指定要读取的文件名
specified_file = '指定文件.csv'  # 替换为您实际的文件名
data_folder = '../数据/'
path = os.path.join(data_folder, specified_file)

# 读取指定文件
if os.path.exists(path):
    df = pd.read_csv(path)

    # 将数据写入Excel文件
    excel_file = f'../xlsx/{specified_file[:-4]}.xlsx'
    df.to_excel(excel_file, index=False)
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb['Sheet1']
    # 获取总行数
    dim = sheet.dimensions.split(':')
    for i in range(2, int(dim[1][1:]) + 1):
        links.append(sheet[f'A{i}'].value)
else:
    print(f"文件 {specified_file} 不存在。")

# 在文件顶部动态读取cookie文件列表
cookie_folder = '../cookie'
BOSS_COOKIE_FILES = [os.path.join(cookie_folder, f) for f in os.listdir(cookie_folder) if f.endswith('.txt')]

def load_cookies(driver, cookie_file):
    """加载指定cookie文件"""
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        # 先访问与cookie相关的域名以设置cookie
        driver.get('https://www.zhipin.com')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        for cookie in cookies:
            # 处理过期时间格式
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
    except Exception as e:
        print(f"加载cookie失败: {str(e)}")

def get_driver(proxy=None):
    """创建Firefox WebDriver实例并加载随机cookie"""
    service = Service(executable_path='D:/Software_work/Python312/geckodriver.exe')  # 使用geckodriver
    options = Options()
    options.headless = True  # 设置无头模式
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Firefox(service=service, options=options)
    
    # 随机选择cookie文件
    cookie_file = random.choice(BOSS_COOKIE_FILES)
    load_cookies(driver, cookie_file)
    
    return driver

def get_new_proxy():
    """通过API获取新的代理IP"""
    try:
        response = requests.get("http://www.xiongmaodaili.com/xiongmao-web/api/glip?secret=a5eba7e1d43d8630e713712a2199572a&orderNo=GL20250219082927NXfIvHlh&count=1&isTxt=0&proxyType=1&returnAccount=1")
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        if data["code"] == "0":
            ip = data["obj"][0]["ip"]
            port = data["obj"][0]["port"]
            return f"{ip}:{port}"
        else:
            print(f"获取代理失败: {data['msg']}")
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except ValueError:
        print("解析JSON失败")
    return None

def process_link(link):
    """处理单个链接的函数"""
    data = []
    proxy = get_new_proxy()
    driver = get_driver(proxy)
    driver.get(link)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    # 检测403错误
    if driver.title == "403 Forbidden":
        print("检测到403错误，检查特定元素")
        try:
            # 检查特定的XPATH元素
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="code31"]/div[1]/p[2]/span[2]/a'))
            )
            if element:
                print("找到特定元素，点击该元素")
                element.click()
                WebDriverWait(driver, 5).until(EC.staleness_of(element))
        except:
            print("未找到特定元素，切换代理")
            driver.close()
            proxy = get_new_proxy()
            driver = get_driver(proxy)
            driver.get(link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    # 检测登录提示
    try:
        login_prompt = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/div[1]/div/div/div[1]/div[1]/p[2]/span[2]/a'))
        )
        if login_prompt:
            print("检测到登录提示，切换代理")
            driver.close()
            proxy = get_new_proxy()
            driver = get_driver(proxy)
            driver.get(link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    except:
        pass

    jishuqi = 0
    while True:
        rawdata = driver.find_elements(by=By.XPATH, value="//a[@class='job-card-left']")
        jishuqi += 1
        if jishuqi == 10:
            break
        if rawdata != []:
            break

    # 改进内容为空判断逻辑
    try:
        empty_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#wrap > div.page-job-wrapper > div.page-job-inner > div > div.job-list-wrapper > div.search-job-result.job-result-empty > div > div > p"))
        )
        if empty_message.text == '没有找到相关职位，打开 APP，查看全部职位库，优质职位随心聊。':
            print(link, '内容为空')
            return None  # 返回None表示内容为空
    except:
        pass

    for j in rawdata:
        data.append(j.get_attribute('href'))

    driver.close()
    return data  # 返回采集到的数据

start_time = time.time()  # 记录开始时间
unfinished_links = []  # 用于存储未完成的链接
total_links = len(links)  # 总链接数
successful_count = 0  # 成功采集的链接数
empty_count = 0  # 内容为空的链接数

# 使用线程池并行处理链接
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(tqdm(executor.map(process_link, links), total=len(links), desc="处理链接", unit="个链接"))

# 处理结果
for result in results:
    if result is None:
        empty_count += 1  # 增加内容为空的计数
    else:
        successful_count += 1  # 增加成功采集的计数

# 将未完成的链接写入文件
if unfinished_links:
    with open('未完成链接.txt', 'w', encoding='utf-8') as f:
        for link in unfinished_links:
            f.write(link + '\n')

end_time = time.time()  # 记录结束时间
elapsed_time = end_time - start_time  # 计算用时

# 输出统计信息
print(f"总链接数: {total_links}")
print(f"成功采集的链接数: {successful_count}")
print(f"内容为空的链接数: {empty_count}")
print(f"未完成的链接数: {len(unfinished_links)}")
print(f"总用时: {elapsed_time:.2f}秒")