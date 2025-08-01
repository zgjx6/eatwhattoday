# eatwhattoday
今天吃什么，解决天下一大难题，涵盖所有常见菜，并进行分类、标记，提供筛选搜索功能。

原生html/js/css，响应式页面支持电脑和手机打开，无任何外部依赖，打开即用，部署简单。


## 在线访问

cloudflare: https://eatwhattoday.zgjx6.workers.dev/

## 部署

### 本地部署

直接下载 index.html 并访问即可

### nginx 部署

由于下厨房的图片限制referer，所以不能直接返回index.html，需要对图片进行反向代理

首先需要替换图片域名，可以手动也可以用以下命令

```shell
sed -i 's|https://i2.chuimg.com|/proxy-image|g' /opt/app/off/download/eatwhattoday/index.html
```

修改nginx.conf中server部分，添加如下代理：

```
    location / {
            # 项目路径
            root /eatwhattoday/;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
        }
    location /proxy-image/ {
        proxy_pass https://i2.chuimg.com/;
        proxy_set_header Referer "https://i2.chuimg.com/";
        proxy_set_header Host i2.chuimg.com;
        proxy_ssl_server_name on;
        proxy_buffering on;
    }
```

### cloudflare 部署

部署命令:

```shell
pwd
ls -al
cp index.html cloudflare/public/index.html
cd cloudflare
sed -i 's|https://i2.chuimg.com|/proxy-image|g' public/index.html
npx wrangler deploy
```
