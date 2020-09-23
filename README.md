# 基金管理系统

**有什么建议提 Issues , 这样我会快点处理哦, 或者联系我, QQ: 547903993**

本脚手架目标: 将构建一套完整的, 适合生产使用的框架, 包括缓存, 定时, 异步任务, 日志以及分布式支持, 长路漫漫, 死亡如风~

基于 `Tornado` 的一个基金管理网站 , 当然基金只是一个 `Demo` , 其目的是为了更好的交流 `Tornado`

技术栈 : Tornado + Peewee + Peewee-async + aioredis + motor + mongoengine + Nginx + Supervisor

## 项目结构

```
fund
├── api
│   ├── fund        基金相关API
│   ├── users       用户相关API
│   └── status      状态码
├── apps
│   ├── fund        基金相关Model
│   └── users       用户相关Model
├── base            Tornado App 封装
├── db              数据库等异步化
├── deploy          部署相关文件
├── docs            API文档相关
├── lib             库 
├── script          项目相关脚本
├── utils           工具包
├── build.py        打包加密脚本
├── config.py       配置文件
├── manage.py       数据库迁移相关
└── run.py          项目启动文件
```


## 部署

### 后台启动Tornado服务

```bash
nohup python3 run.py > run.log 2>&1 &
```

### Nginx

Nginx安装位置 : `/usr/locl/nginx`

启动 :  `/usr/local/sbin/nginx -c /usr/local/nginx/conf/nginx.conf`

重启 : `/usr/local/sbin/nginx -s reload`

### Supervisor

启动Supervisor : `supervisord  -c /mydata/projects/fund/deploy/supervisor/default.conf`

启动Tornado服务 : `supervisorctl start fund`

重启Tornado服务 : `supervisorctl restart fund`


### requirements.txt维护

先安装 `pipreqs`

```bash
$ pip install pipreqs
```
更新 `requirements.txt`

```bash
$ pipreqs . --force
```



