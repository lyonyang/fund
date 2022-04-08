
# 后续做业务分层和优化以及微服务拆分

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

**启动**

```shell
$ /usr/local/sbin/nginx -c /usr/local/nginx/conf/nginx.conf
```

**重启**

```shell
$ /usr/local/sbin/nginx -s reload
```

### Supervisor

**启动 Supervisor**

```shell
$ supervisord  -c /mydata/projects/fund/deploy/supervisor/default.conf
```

**启动 Tornado 服务组**

```shell
$ supervisorctl start fund
```

**重启 Tornado 服务组**

```shell
$ supervisorctl restart fund
```


### 依赖维护

安装 `pipreqs`

```bash
$ pip install pipreqs
```
更新 `requirements.txt`

```bash
$ pipreqs . --force
```

## 使用说明

### load_config

`config` 为一个全局配置变量 , 在调用 `load_config` 时被初始化 , 您可以自行优化 , 如类似 `Flask` 构建一个全局上下文栈等方式优化

### make_app

创建应用首要的是加载 `config.py` , 随后会加载整个 `INSTALL_HANDLERS` , 即你的接口 , 来完成路由注册 , 以及文档构建

### Docs

`docs` 目录是核心 , 它提供了 `define_api` 装饰器 , 来帮你构建路由和文档 , 以及对原始 `Tornado.web.RequestHandler` 的封装

其中包括了 `executor` , 中间件 , 日志 , 异常捕捉 , Web API 文档等

**关于中间件**

这里是基于 `Tornado` 中的 `prepare` 以及 `on_finish` 来实现的 , 所以这样的中间件可能不是你所希望的 , 因为 `on_finish` 不应该接受一个 `Awaitable` 对象 , 如果我们使用 `IOLoop` 中的 `add_callback` , 虽然它可以加入到事件循环 , 但是它并不是我们想要的 "洋葱"

所以后续可能会考虑在 `define_api` 基础之上 , 去实现一个真正 "洋葱" 的中间件

## 致谢

最后 , 欢迎和我一起交流 , 无论是更好的想法 , 还是一些存在的问题 , 我都非常乐意去做得更好 ~
