### 反向代理

```
server {
 listen       80;
 server_name  localhost;

 location / {
 # root   html;
 # index  index.html index.htm;
   proxy_pass  http://127.0.0.1:8080
 }
}
```

### ssl配置
申请证书，可以从腾讯云申请免费证书https://console.cloud.tencent.com/ssl
上传证书到服务器
![证书位置](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202208081421732.png)
修改nginx.conf配置文件

```
    server {
        listen       443 ssl;
        server_name  gluten.cool;

        ssl_certificate      /usr/local/nginx/ssl/gluten.cool_bundle.pem;
        ssl_certificate_key  /usr/local/nginx/ssl/gluten.cool.key;

    #    ssl_session_cache    shared:SSL:1m;
        ssl_session_timeout  5m;

    #    ssl_ciphers  HIGH:!aNULL:!MD5;
    #    ssl_prefer_server_ciphers  on;

        location / {
 #           root   html;
  #          index  index.html index.htm;
           proxy_pass http://127.0.0.1:7777;
  }
    }
```
修改完成以后使用`.nginx -s reload`重启nginx就可以使用了
如果需要做http的重定向，那么需要修改http的配置,在http的配置中增加return方法
![重定向](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202208081424716.png)
