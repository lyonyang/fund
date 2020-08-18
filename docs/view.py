#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import jwt
import datetime
import inspect
import itertools
import traceback
import tornado.web
from typing import Any
from lib.dt import dt
from api.status import Code, Message
from base import current_config


def before_request(f):
    """
    Add global middleware of before request.
    """
    RequestHandler._before_request_funcs.append(f)
    return f


def after_request(f):
    """Add global middleware of after request."""
    RequestHandler._after_request_funcs.append(f)
    return f


class RequestHandler(tornado.web.RequestHandler):
    __doc__ = ""

    current_user_id = None

    _docs_params = {}
    _docs_headers = {}

    # 全局请求中间件
    _before_request_funcs = []
    _after_request_funcs = []

    def __init__(self, application, request, **kwargs):
        super(RequestHandler, self).__init__(application, request, **kwargs)
        # 局部请求中间件
        self.before_request_funcs = []
        self.after_request_funcs = []

    def set_default_headers(self):
        allow_origin = current_config.cors_allow_origin
        if isinstance(current_config.cors_allow_origin, list):
            allow_origin = ','.join(current_config.cors_allow_origin)

        allow_headers = current_config.cors_allow_headers
        if isinstance(current_config.cors_allow_headers, list):
            allow_headers = ','.join(current_config.cors_allow_headers)

        allow_method = current_config.cors_allow_method
        if isinstance(current_config.cors_allow_method, list):
            allow_method = ','.join(current_config.cors_allow_method)

        self.set_header("Access-Control-Allow-Origin", allow_origin)
        self.set_header("Access-Control-Allow-Headers", allow_headers)
        self.set_header('Access-Control-Allow-Methods', allow_method)

    @property
    def user_id(self):
        return self.current_user_id

    @property
    def app(self):
        """tornado.web.Application"""
        return self.application

    def prepare(self):
        for func in (self._before_request_funcs + self.before_request_funcs):
            func_args = inspect.getfullargspec(func).args
            if len(func_args):
                func(self)
            else:
                func()
        self.before_request()

    def on_finish(self):
        for func in (self._after_request_funcs + self.after_request_funcs):
            func_args = inspect.getfullargspec(func).args
            if len(func_args):
                func(self)
            else:
                func()
        self.after_request()

    def before_request(self):
        """
        Called at the beginning of a request before.
        """
        pass

    def after_request(self):
        """
        Called after the end of a request.
        """
        pass

    def write_fail(self, code=Code.ERROR, msg=Message.ERROR, data=""):
        return self.write({'return_code': code, 'return_data': data, 'return_msg': msg})

    def write_success(self, data={}, code=Code.SUCCESS, msg=Message.SUCCESS):
        return self.write({'return_code': code, 'return_data': data, 'return_msg': msg})

    def get_arg(self, name, default=None, strip=True):
        param = self._docs_params.get(self.request.method.lower(), {}).get(name, {})  # type: Param
        argument = self.get_argument(name, default="", strip=strip) or default  # type: String
        if param.get('required') and not argument:
            self.set_status(400, 'Bad Request!')
            raise tornado.web.Finish()
        return argument

    def get_arg_int(self, name, default=None, strip=True):
        try:
            str_arg = self.get_arg(name, default=default, strip=strip)
            argument = int(str_arg) if str_arg else str_arg
        except:
            self.set_status(400, 'Bad Request!')
            raise tornado.web.Finish()
        return argument

    def get_arg_datetime(self, name, default=None, strip=True):
        try:
            datetime_string = self.get_arg(name, default=default, strip=strip)
            if datetime_string is None:
                return None

            return dt.str_to_dt(datetime_string)
        except:
            self.set_status(400, 'Bad Request!')
            raise tornado.web.Finish()

    def get_docs_token(self):
        return self.token_encode(0)

    def token_encode(self, user_id):
        """Generate token."""

        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=current_config.docs_token_expire_days),
            'iat': datetime.datetime.utcnow(),
            'iss': 'Lyon',
            'data': {
                'user_id': user_id,
                'login_time': datetime.datetime.now().strftime("%Y-%m-%D %H:%M:%S")
            }
        }
        secret_key = current_config.docs_token_secret_key
        token = jwt.encode(
            payload,
            secret_key,
            algorithm='HS256'
        ).decode('utf-8')
        return token

    def token_decode(self, auth_token):
        """Decode token."""

        try:
            # verify_exp
            payload = jwt.decode(auth_token, current_config.docs_token_secret_key,
                                 options={'verify_exp': current_config.docs_token_verify_expire})
            data = payload['data']
            return data
        except Exception:
            return None

    def _log(self):
        """self.finish() will second call."""
        pass

    def log_request(self):
        date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        code = self.get_status() or "-"
        code = str(code)
        request_time = 1000.0 * self.request.request_time()
        msg = '%s - - [%s] "%s" %s %.2fms' % (self.request.remote_ip, date_string,
                                              '%s %s %s' % (
                                                  self.request.method, self.request.uri, self.request.version),
                                              code, request_time)

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

        self.app.logger.info(msg)

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
                self.app.logger.warning(format, *args)
        else:
            self.app.logger.error(  # type: ignore
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
            self.app.logger.error("Cannot send error response after headers written")
            if not self._finished:
                # If we get an error between writing headers and finishing,
                # we are unlikely to be able to finish due to a
                # Content-Length mismatch. Try anyway to release the
                # socket.
                try:
                    self.finish()
                except Exception:
                    self.app.logger.error("Failed to flush partial response", exc_info=True)
            return
        self.clear()

        reason = kwargs.get("reason")
        if "exc_info" in kwargs:
            exception = kwargs["exc_info"][1]
            if isinstance(exception, tornado.web.HTTPError) and exception.reason:
                reason = exception.reason
        self.set_status(status_code, reason=reason)
        try:
            self.write_error(status_code, **kwargs)
        except Exception:
            self.app.logger.error("Uncaught exception in write_error", exc_info=True)
        if not self._finished:
            self.finish()

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.
        """
        self.app.logger.error(traceback.format_exc())
        self.finish({'return_code': Code.ERROR, 'return_msg': Message.ERROR, 'return_data': {}})

    async def options(self):
        return self.write_success(data={
            'Method': 'Options',
            'Uri': self.request.uri,
            'Version': self.request.version,
            'Remote_ip': self.request.remote_ip,
        })


class DocsHandler(RequestHandler):
    async def get(self):
        from docs import route
        search = self.get_argument('search', default="")
        docs_token = self.get_cookie('docs_token', default="")
        if not docs_token:
            return self.redirect('/tornado_docs/login')

        data = self.token_decode(docs_token)
        if not data:
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
        if username == current_config.docs_username and password == current_config.docs_password:
            return self.write_success({'docs_token': self.get_docs_token()})
        return self.write_fail(Code.USERNAME_OR_PASSWORD_INVALID, Message.USERNAME_OR_PASSWORD_INVALID)


class DocsMarkdownHandler(RequestHandler):
    async def get(self):
        # TODO: 生成Markdown文档
        pass
