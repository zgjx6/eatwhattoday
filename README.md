# eatwhattoday
今天吃什么，解决天下一大难题，涵盖所有常见菜，并进行分类、标记，提供筛选搜索功能。

原生html/js/css，响应式页面支持电脑和手机打开，无任何外部依赖，打开即用，部署简单。


## 在线访问

netlify: https://eatwhattoday.netlify.app/

cloudflare: https://eatwhattoday.zgjx6.workers.dev/index.html

## 部署

### 本地部署

直接下载 index.html 并访问即可

### nginx 部署

```
    location / {
            # 项目路径
            root /eatwhattoday/;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
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
