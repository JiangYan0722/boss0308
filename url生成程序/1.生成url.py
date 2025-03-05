import pandas as pd
from urllib.parse import quote

# 读取包含中文名称的文件
input_file_path = '1.3.2匹配到的上市公司名称.csv'  # 替换为你的输入文件路径
df = pd.read_csv(input_file_path)

# 设置要拆分的文件数量
n = 1000# 你可以根据需要修改n的值

# 读取城市代码文件
cities_file_path = '热门城市代码.csv'  # 替换为你的城市代码文件路径
cities_df = pd.read_csv(cities_file_path)

# 获取城市代码列表
cities = cities_df['城市代码'].tolist()

# 生成URL列表
urls = []
for company in df['匹配的上市公司名称'].tolist():
    for city in cities:
        encoded_company = quote(company, encoding='utf-8')  # 对中文名称进行URL编码
        url = f"https://www.zhipin.com/web/geek/job?query={encoded_company}&city={city}"
        urls.append(url)

# 将URL列表拆分成n份
chunk_size = len(urls) // n
if len(urls) % n != 0:
    chunk_size += 1

chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

# 将每份保存到CSV文件中
for i, chunk in enumerate(chunks):
    output_file_path = f'../数据/urls_part_{i+1}.csv'  # 输出文件路径
    pd.DataFrame(chunk, columns=['URL']).to_csv(output_file_path, index=False, encoding='utf_8_sig')
    print(f"Part {i+1} saved to {output_file_path}")