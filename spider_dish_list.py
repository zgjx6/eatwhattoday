import os
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import dashscope
import json
from typing import Dict, List

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
base_url = "https://www.xiachufang.com"
search_url = f"{base_url}/search/?keyword="


def analyze_dishes_with_qwen3(dishes: List[Dict]) -> List[Dict]:
  """批量分析菜肴信息"""
  dish_names = [dish["菜名"] for dish in dishes]
  prompt_template = """
    请分析以下菜肴列表，并以严格的 JSON 格式返回结果，返回一个数组，每个元素包含字段：菜名、菜系、特色、味道、用时、价格。

    要求：
    - 菜名：保持原菜名不变
    - 菜系：中国的八大菜系（如川菜、粤菜、鲁菜、苏菜、浙菜、闽菜、湘菜、徽菜）或其他地方知名菜系（如潮汕菜、客家菜等）、家常菜、国外菜系（如意大利菜、日本料理等），若无法判断则为空字符串。
    - 特色：指这道菜的独特烹饪方式或关键调料，如豆瓣酱、花雕酒、甜面酱、咖喱等，格式为数组，若无明显特色则为空数组。
    - 味道：显著的味型，如微辣、麻、鲜、酱香、酸甜等，格式为数组，若无则为空数组。
    - 用时：预估制作时间，单位为分钟，格式为数字加'm'，例如 '30m'，若无法判断则为空字符串。
    - 价格：预估家庭制作成本（人民币），不用添加单位，例如 '25'，若无法判断则为空字符串。

    只返回一个 JSON 数组，每道菜的数据为数组中的一个map，返回结果的顺序需要与输入的顺序一致，不要任何额外说明。

    菜肴列表：{dish_names}
    """.strip()

  results = []
  try:
    prompt = prompt_template.format(dish_names=dish_names)
    response = dashscope.Generation.call(model='qwen-plus', prompt=prompt, temperature=0.3, top_p=0.8, result_format='message')
    if response.status_code == 200:
      content = response.output.choices[0].message.content.strip()
      print(f"{dish_names} 的分析结果：{content}")
      try:
        start = content.find('[')
        end = content.rfind(']')
        if start == -1 or end == -1:
          raise ValueError("No JSON array found")
        json_str = content[start:end + 1]
        data = json.loads(json_str)

        # 确保返回的数据与输入菜肴对应
        for i, dish in enumerate(dishes):
          if i < len(data):
            analysis_result = data[i]
            dish.update({
              "菜系": analysis_result.get("菜系", "").strip(),
              "特色": analysis_result.get("特色", []),
              "味道": analysis_result.get("味道", []),
              "用时": analysis_result.get("用时", ""),
              "价格": analysis_result.get("价格", "")
            })
          results.append(dish)
      except (json.JSONDecodeError, ValueError) as e:
        print(f"解析大模型返回的 JSON 失败：{e}")
        for dish in dishes:
          results.append(dish)
    else:
      print(f"调用 Qwen3 失败：{response.code} {response.message}")
      # 如果调用失败，返回原始数据结构
      for dish in dishes:
        results.append(dish)
  except Exception as e:
    print(f"批量分析菜肴时发生异常: {e}")
    # 如果发生异常，返回原始数据结构
    for dish in dishes:
      results.append(dish)
  return results

def search_recipe_links_and_image(dish):
    links:dict = {k: v for k, v in dish["链接"].items() if k.strip() != ""}
    updated_links = links
    image_url = dish["图片"]
    search_keywords = [key for key in links.keys() if not links[key]] if links else [dish["菜名"]]
    for i, keyword in enumerate(search_keywords):
      response = query_response(keyword)
      soup = BeautifulSoup(response.text, 'html.parser')
      recipe_div = soup.find('div', class_='recipe')
      if recipe_div:
        a_tag = recipe_div.find('a')
        if a_tag and a_tag.get('href'):
          updated_links[keyword] = urljoin(base_url, a_tag['href']).split('?')[0]
          if i == 0 and not image_url:
            cover_div = a_tag.find('div', class_='cover')
            if cover_div:
              img_tag = cover_div.find('img')
              if img_tag and img_tag.get('data-src'):
                image_url = img_tag['data-src'].split('?')[0]
      print(f"{keyword} 搜索完成：{updated_links[keyword]}")
    return updated_links, image_url


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
      time.sleep(1)
      response = query_response(dish, retry=retry + 1)
  return response

def get_recipe_info(dish_list):
  # 第一步：批量分析所有菜肴
  analyzed_dishes = analyze_dishes_with_qwen3(dish_list)

  # 第二步：为每道菜搜索链接和图片
  for dish in analyzed_dishes:
    links, image = search_recipe_links_and_image(dish)
    dish["链接"] = links
    dish["图片"] = image

  return analyzed_dishes


if __name__ == "__main__":
  my_dish_list = [
    { "菜名": "兰州牛肉面", "菜系": "", "用时": "", "价格": "", "特色": [], "味道": [], "链接": { }, "图片": "" },
  ]
  info = get_recipe_info(my_dish_list)
  for item in info:
    print(str(item).replace("'", '"'), end=',\n')
