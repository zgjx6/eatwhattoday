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
          updated_links[keyword] = urljoin(base_url, a_tag['href'])
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
      time.sleep(0.5)
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
  my_dish_list = [{ "菜名": "麻婆豆腐", "菜系": "川菜", "特色": [], "味道": ["麻", "微辣"], "用时": "30m", "链接": { "麻婆豆腐": "https://www.xiachufang.com/recipe/78140/" }, "图片": "https://i2.chuimg.com/f8f10c40efea45099c416a2ed9123d4a_1864w_1242h.jpg" },
                  { "菜名": "脆皮豆腐", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "脆皮豆腐": "https://www.xiachufang.com/recipe/104643213/" }, "图片": "https://i2.chuimg.com/e88fc12162e74eb38b1f4303d3205538_1078w_720h.jpg" },
                  { "菜名": "家常豆腐", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "家常豆腐": "https://www.xiachufang.com/recipe/104337555/" }, "图片": "https://i2.chuimg.com/2cb78ce84e6e49d0842635d13191f783_600w_480h.jpg" },
                  { "菜名": "金针菇豆腐煲", "菜系": "日料", "特色": [], "味道": [], "用时": "30m", "链接": { "金针菇豆腐煲": "https://www.xiachufang.com/recipe/105834401/" }, "图片": "https://i2.chuimg.com/6d4ec3f927ce42fdbe0f46d33b3db9ab_2560w_2560h.jpg" },
                  { "菜名": "红烧豆腐", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "红烧豆腐": "https://www.xiachufang.com/recipe/102333700/" }, "图片": "https://i2.chuimg.com/195d38a2880211e6a9a10242ac110002_600w_400h.jpg" },
                  { "菜名": "豆花/豆腐脑", "菜系": "川菜", "特色": [], "味道": [], "用时": "30m", "链接": { "豆花水煮牛肉": "https://www.xiachufang.com/recipe/106590753/", "咸豆腐脑": "", "甜豆腐脑": "" }, "图片": "https://i2.chuimg.com/64fe3d5a178b4c51a950797b3741da43_1080w_1920h.jpg" },
                  { "菜名": "酿豆腐", "菜系": "客家菜", "特色": [], "味道": [], "用时": "30m", "链接": { "酿豆腐": "https://www.xiachufang.com/recipe/105998181/" }, "图片": "https://i2.chuimg.com/cd8dda9b2c8d4ac0960cfa82ce17035a_3024w_2268h.jpg" },
                  { "菜名": "小葱拌豆腐", "菜系": "家常菜", "特色": [], "味道": [], "用时": "20m", "链接": { "小葱拌豆腐": "https://www.xiachufang.com/recipe/106151828/" }, "图片": "https://i2.chuimg.com/8cd29e0bc3e04fcfb653cce3079a879b_820w_1824h.jpg" },
                  { "菜名": "豆腐蒸蛋", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "肉末豆腐蒸蛋": "https://www.xiachufang.com/recipe/104057101/", "虾仁豆腐蒸水蛋": "https://www.xiachufang.com/recipe/101858672/" }, "图片": "https://i2.chuimg.com/f6e3072534214f18a6bf35b1555968ec_1125w_831h.jpg" },
                  { "菜名": "油豆腐/豆泡", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "油豆腐": "https://www.xiachufang.com/recipe/106104250/", "白菜焖豆泡": "https://www.xiachufang.com/recipe/106389253/", "肉末炒豆泡": "https://www.xiachufang.com/recipe/107467995/", "油豆泡塞肉": "https://www.xiachufang.com/recipe/104101699/" }, "图片": "https://i2.chuimg.com/c7fb26f96e964e9ea91c20cb975db229_1280w_960h.jpg" },
                  { "菜名": "豆筋烧五花肉", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "豆筋烧五花肉": "https://www.xiachufang.com/recipe/30252/" }, "图片": "https://i2.chuimg.com/ba3b27fc86f411e6b87c0242ac110003_490w_732h.jpg" },
                  { "菜名": "腐乳烧排骨", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "腐乳烧排骨": "https://www.xiachufang.com/recipe/267584/" }, "图片": "https://i2.chuimg.com/b7423282ac9411e6bc9d0242ac110002_1280w_853h.jpg" },
                  { "菜名": "青椒豆腐干", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "青椒豆腐干": "https://www.xiachufang.com/recipe/100345725/" }, "图片": "https://i2.chuimg.com/9d24fe74885a11e6b87c0242ac110003_640w_640h.jpg" },
                  { "菜名": "腐竹烧香菇", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "腐竹烧香菇": "https://www.xiachufang.com/recipe/102125564/" }, "图片": "https://i2.chuimg.com/18db9d597a67429f9e96d2bd923e5d6c_1500w_1124h.jpg" },
                  { "菜名": "油焖千张", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "油焖千张": "https://www.xiachufang.com/recipe/106404239/" }, "图片": "https://i2.chuimg.com/3e14f15cca264706bb7a2e933705a4b9_534w_300h.gif" },
                  { "菜名": "金针菇豆皮卷", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "金针菇豆皮卷": "https://www.xiachufang.com/recipe/104449303/" }, "图片": "https://i2.chuimg.com/fb8117b9567a4123b02d25ea179a9c88_3024w_4032h.jpg" },
                  { "菜名": "红烧素鸡", "菜系": "家常菜", "特色": [], "味道": [], "用时": "30m", "链接": { "红烧素鸡": "https://www.xiachufang.com/recipe/104431785/" }, "图片": "https://i2.chuimg.com/7bc11b15a04047ca8811a3ea669d5942_1242w_1242h.jpg" },]
  info = get_recipe_info(my_dish_list)
  print('[')
  for item in info:
    print(item, end=',\n')
  print(']')
