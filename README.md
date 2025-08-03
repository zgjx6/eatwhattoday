# eatwhattoday
今天吃什么，解决天下一大难题，涵盖所有常见菜，共计1000余道常见菜系，并进行分类、标记，提供筛选搜索功能。

原生html/js/css，响应式页面支持电脑和手机打开，无任何外部依赖，打开即用，部署简单。


## 在线访问

netlify: https://eatwhattoday.netlify.app/index.html?imgProxy=/imgs/

cloudflare: https://eatwhattoday.zgjx6.workers.dev/index.html?imgProxy=/imgs/

预览：

![](imgs/preview.png)

## 部署

### 本地部署

直接下载 index.html 并访问即可

### nginx 部署

```
server {
    listen 80;
    server_name localhost;
    root /eatwhattoday;
    location / {
        index index.html;
        add_header Cache-Control public;
        autoindex off;
    }
}

```

然后访问 http://localhost/index.html

### cloudflare 部署

部署命令:

```shell
cd cloudflare
cp ../index.html public/index.html
npx wrangler deploy
```
