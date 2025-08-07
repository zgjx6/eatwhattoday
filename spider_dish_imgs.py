import os
import re
import requests

# 配置
img_host = "https://i2.chuimg.com/"
img_param = "?imageView2/1/w/150/h/150/interlace/1/q/75"
html_file = "index.html"
imgs_dir = "imgs"

# 确保 imgs 目录存在
os.makedirs(imgs_dir, exist_ok=True)
white_list_img_set = {'preview.png'}

# 读取 HTML 文件
try:
  with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()
except FileNotFoundError:
  print(f"错误：找不到文件 {html_file}")
  exit(1)

# 构造正则表达式，匹配 ${img_host}xxxxx${img_param}
# 注意：$ 在正则中是特殊字符，需要转义；{} 也是模板字符串，也要转义
pattern = re.escape('${img_host}') + r'(.*?)' + re.escape('${img_param}')

matches = re.findall(pattern, content)

if not matches:
  print("未找到匹配的图片链接。")
else:
  print(f"找到 {len(matches)} 个图片需要处理。")

# 下载去重后的图片
downloaded, errored, deleted = 0, 0, 0
matches = set(matches) | white_list_img_set
for filename in matches:  # 去重
  filepath = os.path.join(imgs_dir, filename)
  if os.path.exists(filepath):
    continue

  img_url = img_host + filename + img_param
  print(f"正在下载: {img_url}")
  try:
    response = requests.get(img_url, timeout=10)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
      f.write(response.content)
    print(f"✅ 下载成功: {filename}")
    downloaded += 1
  except requests.RequestException as e:
    print(f"❌ 下载失败 {filename}: {e}")
    errored += 1

for root, dirs, filenames in os.walk(imgs_dir):
  for filename in filenames:
    if filename not in matches:
      os.remove(os.path.join(root, filename))
      deleted += 1
      print(f"❌ 文件已删除 {filename}")
os.system('git add imgs')
print(f"\n完成！成功下载 {downloaded} 张图片，失败 {errored} 张图片，删除 {deleted} 张图片")
