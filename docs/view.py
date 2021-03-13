#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import string
import inspect
import datetime
import itertools
import tornado.web
import tornado.gen
import tornado.process
import concurrent.futures
from lib.dt import dt
from typing import Any, Awaitable
from api.status import Code, Message
from lib.token import jwt_decode, jwt_encode


def before_request(f):
    """
    Add global middleware of before request.
    """
    RequestHandler.before_request_funcs.append(f)
    return f


def after_request(f):
    """Add global middleware of after request."""
    RequestHandler.after_request_funcs.append(f)
    return f


class RequestHandler(tornado.web.RequestHandler):
    __doc__ = ""

    current_user_id = None

    _docs_params = {}
    _docs_headers = {}

    # Global Middleware
    before_request_funcs = []
    after_request_funcs = []

    executor = None

    def __init__(self, application, request, **kwargs):
        super(RequestHandler, self).__init__(application, request, **kwargs)

        if self.executor is None:
            self.__class__.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=(tornado.process.cpu_count() * application.config.get('EXECUTOR_THREAD_MULTIPLE', 5))
            )  # type: concurrent.futures.Executor

    @property
    def app(self):
        return self.application

    def set_default_headers(self):
        allow_origin = self.application.config.CORS_ALLOW_ORIGIN
        if isinstance(self.application.config.CORS_ALLOW_ORIGIN, list):
            allow_origin = ','.join(self.application.config.CORS_ALLOW_ORIGIN)

        allow_headers = self.application.config.CORS_ALLOW_HEADERS
        if isinstance(self.application.config.CORS_ALLOW_HEADERS, list):
            allow_headers = ','.join(self.application.config.CORS_ALLOW_HEADERS)

        allow_method = self.application.config.CORS_ALLOW_METHOD
        if isinstance(self.application.config.CORS_ALLOW_METHOD, list):
            allow_method = ','.join(self.application.config.CORS_ALLOW_METHOD)

        self.set_header("Access-Control-Allow-Origin", allow_origin)
        self.set_header("Access-Control-Allow-Headers", allow_headers)
        self.set_header('Access-Control-Allow-Methods', allow_method)

    @property
    def user_id(self):
        return self.current_user_id

    # type: tornado.web.RequestHandler.prepare
    async def prepare(self):
        if self.before_request_funcs:
            await tornado.gen.multi(self.before_request_funcs)
        await self.before_request()

    def add_callback(self, callback, *args, **kwargs):
        self.application.loop.add_callback(callback, *args, **kwargs)

    def on_finish(self):
        # async
        if self.application.config.get("ON_FINISH_ASYNC"):
            for func in self.after_request_funcs:
                func_args = inspect.getfullargspec(func).args
                if len(func_args):
                    self.add_callback(func, self)
                else:
                    self.add_callback(func)
        # sync
        else:
            for func in self.after_request_funcs:
                func_args = inspect.getfullargspec(func).args
                if len(func_args):
                    func(self)
                else:
                    func()
        if tornado.gen.is_future(self.after_request):
            self.add_callback(self.after_request)
        else:
            self.after_request()

    async def before_request(self) -> Awaitable:
        """
        Called at the beginning of a request before.
        """
        pass

    def after_request(self) -> Awaitable[None]:
        """
        Called after the end of a request.
        """
        pass

    def _get_argument(self, name, default, source, strip=True):
        args = self._get_arguments(name, source, strip=strip)
        if not args:
            return default
        return args[-1]

    def get_headers(self, name, default=None, strip=True):
        s = self.request.headers.get(name, default)
        if strip:
            s = s.strip()
        return s

    def get_arg(self, name, default=None, strip=True):
        param = self._docs_params.get(self.request.method.lower(), {}).get(name, {})  # type: Param
        argument = self.get_argument(name, default=default, strip=strip) or default  # type: String
        if param.get('required') and not argument:
            self.write_bad_request()
        return argument

    def get_arg_int(self, name, default=None, strip=True):
        try:
            str_arg = self.get_arg(name, default=default, strip=strip)
            argument = int(str_arg) if str_arg else str_arg
        except:
            self.write_bad_request()
        return argument

    def get_arg_datetime(self, name, default=None, strip=True):
        try:
            datetime_string = self.get_arg(name, default=default, strip=strip)
            if datetime_string is None:
                return None

            return dt.str_to_dt(datetime_string)
        except:
            self.write_bad_request()

    def _log(self):
        """self.finish() will second call."""
        # async
        if self.application.config.get("ON_FINISH_ASYNC", False):
            self.add_callback(self.log_request)
        # sync
        else:
            self.log_request()

    def log_request(self):
        date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        code = self.get_status() or "-"
        code = str(code)
        request_time = 1000.0 * self.request.request_time()

        header_params, body_params = '', ''

        if self.application.config.get("LOG_REQUEST_DETAIL", True):
            if hasattr(self, '_docs_headers'):
                headers = self._docs_headers.get(self.request.method.lower(), {}).keys()
                if headers:
                    header_params = '&'.join(
                        ['%s=%s' % (key, self.get_headers(key, default='')) for key in headers])
            if hasattr(self, '_docs_params'):
                keys = self._docs_params.get(self.request.method.lower(), {}).keys()
                if keys:
                    body_params = '&'.join(['%s=%s' % (key, self.get_argument(key, default='')) for key in keys])
        params = '%s - %s' % (header_params, body_params) if (header_params or body_params) else ''

        msg = '%s - - [%s] "%s" %s %.2fms - %s' % (self.request.remote_ip, date_string,
                                                   '%s %s %s' % (
                                                       self.request.method, self.request.uri, self.request.version),
                                                   code, request_time, params)

        fmt_str = '\033[%d;%dm%s\033[0m'
        if code[0] == "1":  # 1xx - Informational
            msg = fmt_str % (1, 0, msg)
        elif code[0] == "2":  # 2xx - Success
            msg = fmt_str % (0, 37, msg)
        elif code == "304":  # 304 - Resource Not Modified
            msg = fmt_str % (0, 36, msg)
        elif code[0] == "3":  # 3xx - Redirection
            msg = fmt_str % (0, 32, msg)
        elif code == "404":  # 404 - Resource Not Found
            msg = fmt_str % (0, 33, msg)
        elif code[0] == "4":  # 4xx - Client Error
            msg = fmt_str % (1, 31, msg)
        else:  # 5xx, or any other response
            msg = fmt_str % (1, 0, msg)

        self.application.logger.info(msg)

    @property
    def logger(self):
        return self.application.logger

    def log_exception(self, typ, value, tb):
        """Override to customize logging of uncaught exceptions.

        By default logs instances of `HTTPError` as warnings without
        stack traces (on the ``tornado.general`` logger), and all
        other exceptions as errors with stack traces (on the
        ``tornado.application`` logger).

        .. versionadded:: 3.1
        """
        if isinstance(value, tornado.web.HTTPError):
            if value.log_message:
                format = "%d %s: " + value.log_message
                args = [value.status_code, self._request_summary()] + list(value.args)
                self.application.logger.warning(format, *args)
        else:
            self.application.logger.error(  # type: ignore
                "Uncaught exception %s\n%r",
                self._request_summary(),
                self.request,
                exc_info=(typ, value, tb),
            )

    def send_error(self, status_code: int = 500, **kwargs: Any) -> None:
        """Sends the given HTTP error code to the browser.

        If `flush()` has already been called, it is not possible to send
        an error, so this method will simply terminate the response.
        If output has been written but not yet flushed, it will be discarded
        and replaced with the error page.

        Override `write_error()` to customize the error page that is returned.
        Additional keyword arguments are passed through to `write_error`.
        """
        if self._headers_written:
            self.logger.error("Cannot send error response after headers written")
            if not self._finished:
                # If we get an error between writing headers and finishing,
                # we are unlikely to be able to finish due to a
                # Content-Length mismatch. Try anyway to release the
                # socket.
                try:
                    self.finish()
                except Exception:
                    self.logger.error("Failed to flush partial response", exc_info=True)
            return
        self.clear()

        reason = kwargs.get("reason")
        if "exc_info" in kwargs:
            exception = kwargs["exc_info"][1]
            if isinstance(exception, tornado.web.HTTPError) and exception.reason:
                reason = exception.reason
        if status_code >= 500:
            self.set_status(200, reason=reason)
        try:
            # self.write_error(status_code, **kwargs)
            self.write_fail()
        except Exception:
            self.logger.error("Uncaught exception in write_error", exc_info=True)
        if not self._finished:
            self.finish()

    def write_fail(self, code=Code.System.ERROR, msg=Message.System.ERROR, data=""):
        """
        Request Fail. Return fail message.
        """
        return self.write({'return_code': code, 'return_data': "" or dict(), 'return_msg': msg})

    def write_success(self, data=None, code=Code.System.SUCCESS, msg=Message.System.SUCCESS):
        if data is None:
            data = dict()
        return self.write({'return_code': code, 'return_data': data, 'return_msg': msg})

    def write_bad_request(self):
        self.set_status(400, 'Bad Request!')
        raise tornado.web.Finish()

    async def options(self):
        return self.finish('OK')


class PageNotFound(RequestHandler):
    async def prepare(self) -> None:
        self.set_status(404, reason='Not Found')
        template = string.Template(
            '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            '<meta http-equiv="X-UA-Compatible"content="IE=edge">'
            '<meta name="viewport"content="width=device-width, initial-scale=1">'
            '<style>body{background-color:rgb(236,236,236);'
            'color:#CD9B9B;font:100%"Lato",sans-serif;font-size:1.8rem;'
            'font-weight:300}.center{text-align:center}.header{font-size:10rem;font-weight:700;'
            'margin:2%0 2%0;text-shadow:5px 5px 5px#7f8c8d}.error{margin:-50px 0 2%0;font-size:6rem;'
            'text-shadow:5px 5px 5px#7f8c8d;font-weight:500}</style>'
            '<title>$code $message</title></head><body><section class="center"><article><h1 class="header">$code</h1>'
            '<p class="error">$message</p></article></section></body></html>'
        )
        self.finish(
            template.substitute(code=404, message=self._reason)
        )


class DocsHandler(RequestHandler):
    async def get(self):
        from docs import route
        search = self.get_argument('search', default="")
        docs_token = self.get_cookie('docs_token', default="")
        if not docs_token:
            return self.redirect('/tornado_docs/login')

        payload = jwt_decode(docs_token, self.application.config.DOCS_TOKEN_SECRET_KEY,
                             verify_exp=self.application.config.DOCS_TOKEN_VERIFY_EXPIRE)
        if not payload or not payload.get('data'):
            return self.redirect('/tornado_docs/login')

        endpoints = []
        if search:
            for end in route.endpoints:
                if search in end.name_parent or search in end.path:
                    endpoints.append(end)
        else:
            endpoints = route.endpoints

        endpoints = itertools.groupby(endpoints, key=lambda x: x.name_parent)
        endpoints = [(name_parent, list(group)) for name_parent, group in endpoints]
        context = {
            'endpoints': endpoints,
            'query': search,
            'lower': lambda x: x.lower()
        }

        return self.render('templates/docs/home.html', **context)


class DocsLoginHandler(RequestHandler):
    async def get(self):
        return self.render('templates/docs/login.html')

    async def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        if username == self.application.config.DOCS_USERNAME and password == self.application.config.DOCS_PASSWORD:
            data = {
                'login_time': datetime.datetime.now().strftime("%Y-%m-%D %H:%M:%S")
            }
            docs_token = jwt_encode(data, self.application.config.DOCS_TOKEN_SECRET_KEY,
                                    expires=self.application.config.DOCS_TOKEN_EXPIRE_DAYS,
                                    issuer='Lyon')

            return self.write_success({'docs_token': docs_token})
        return self.write_fail(Code.User.USERNAME_OR_PASSWORD_INVALID, Message.User.USERNAME_OR_PASSWORD_INVALID)


class DocsMarkdownHandler(RequestHandler):
    async def get(self):
        # TODO: 生成Markdown文档
        pass
