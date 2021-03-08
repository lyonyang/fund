

![tornado](./document/tornado.png)



## 介绍

一个基金管理系统 , 基于 [Tornado](https://github.com/tornadoweb/tornado) , 构建一个成熟的 [Tornado](https://github.com/tornadoweb/tornado) **脚手架**

技术栈 : Tornado + MySQL + MongoDB + Redis + Celery + Nginx + Supervisor

联系我一起交流 , **QQ : 547903993** , **QQ群 : 590092348**

## 维护

### 脚手架

- [x] `Tornado` 封装 : 配置 , 日志 , API
- [x] `MySQL` 异步化 : Peewee + Peewee-async  
- [x] `MongoDB` 异步化 : mongoengine + motor
- [x] `Redis` 异步化 : aioredis
- [x] `Celery` 支持 , 异步任务与定时任务
- [x] `Supervisor` 部署
- [x] 详细请求日志
- [ ] `API监控`
- [ ] `ES` 全文搜索
- [ ] `Docker` 
- [ ] 考虑 `executor` 提升为类属性

### 基金功能

- [x] 登录 , 注册
- [x] 基金交易记录
- [x] 基金实时数据监控 , 收益计算
- [ ] 自选基金
- [ ] 基金排行
- [ ] 基金实时交易模拟

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
│   └── db          数据库等异步化
├── cache           缓存相关
├── celerys         Celery相关
│   ├── crontabs    定时任务
│   ├── tasks       异步任务
│   └── server      Celery入口
├── deploy          部署相关文件
├── docs            API文档相关
├── document        脚手架设计参考
├── lib             库 
├── script          项目相关脚本
├── utils           工具包
├── build.py        打包加密脚本
├── config.py       配置文件
├── manage.py       数据库迁移相关
└── run.py          项目启动文件
```

## 开始

切换到项目根目录

### 启动

```bash
$ python run.py
```

记得配置好数据库相关配置, 以及数据表迁移哟~

```bash
# Linux 后台启动
$ nohup python3 run.py > run.log 2>&1 &
```

### Celery

```bash
# 先启动 Celery Beat
$ celery beat -A celerys.server --loglevel=info

# 后启动 Celery Worker
$ celery worker -A celerys.server --loglevel=info
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



