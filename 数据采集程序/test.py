from time import sleep
from selenium import webdriver

driver = webdriver.Edge()

driver.get(r'https://www.baidu.com/')

sleep(5)
driver.close()