import os
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import dashscope
import json
from typing import Dict, List
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
base_url = "https://www.xiachufang.com"
search_url = f"{base_url}/search/?keyword="

def main():
  prefix = "清炒"
  dishes = {
    "香菇": "", "金针菇": "", "杏鲍菇": "", "茶树菇": "", "鸡枞菌": "", "木耳": ""
  }
  for dish in dishes.keys():
    response = query_response(prefix + dish)
    if response:
      soup = BeautifulSoup(response.text, 'html.parser')
      recipe_div = soup.find('div', class_='recipe')
      if recipe_div:
        a_tag = recipe_div.find('a')
        if a_tag and a_tag.get('href'):
          link_url = urljoin(base_url, a_tag['href'])
          dishes[dish] = link_url
    print(f"{dish}: {dishes[dish]}")
  print(str(dishes).replace("'", '"').strip('{}'))


def query_response(dish, retry=0):
  url = search_url + dish
  response = None
  try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
  except Exception as e:
    print(f"搜索菜谱 '{dish}' 第{retry}次时出错: {e}")
    if retry < 2:
      time.sleep(0.5)
      response = query_response(dish, retry=retry + 1)
  return response


if __name__ == '__main__':
    main()
