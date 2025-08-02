# eatwhattoday
今天吃什么，解决天下一大难题，涵盖所有常见菜，并进行分类、标记，提供筛选搜索功能。

原生html/js/css，响应式页面支持电脑和手机打开，无任何外部依赖，打开即用，部署简单。


## 在线访问

cloudflare: https://eatwhattoday.zgjx6.workers.dev/index.html?imgProxy=/proxy-image/

## 部署

### 本地部署

直接下载 index.html 并访问即可

### nginx 部署

由于下厨房的图片限制referer，所以需要对图片进行反向代理

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

然后访问 http://localhost/index.html?imgProxy=/proxy-image/

### cloudflare 部署

部署命令:

```shell
cd cloudflare
cp ../index.html public/index.html
npx wrangler deploy
```
