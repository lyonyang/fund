# 基金管理系统

## TODO

数据存储优化


## 部署

### 后台启动

```bash
nohup python3 run.py > run.log 2>&1 &
```

### Nginx

Nginx安装位置 : `/usr/locl/nginx`

启动 :  `/usr/local/sbin/nginx -c /usr/local/nginx/conf/nginx.conf`

重启 : `/usr/local/sbin/nginx -s reload`

### Supervisor部署

启动Supervisor : `supervisord  -c /mydata/projects/fund/deploy/supervisor/default.conf`

启动Tornado服务 : `supervisorctl start fund`

重启Tornado服务 : `supervisorctl restart fund`


## Async/Await

关于 `async` 与 `await` , 这两者使用对象必须是 `Awaitable` 对象




