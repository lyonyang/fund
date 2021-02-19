#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


__all__ = ['DocsHandler', 'DocsLoginHandler', 'DocsMarkdownHandler',
           'Param', 'define_api', 'route']

import json
import inspect
import functools
import importlib
import tornado.web
from base import config
from .view import DocsHandler, DocsLoginHandler, DocsMarkdownHandler


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        raise ImportError(msg)

    module = importlib.import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        raise ImportError(msg)


def check_param(params):
    if not isinstance(params, (list, tuple)):
        raise TypeError(_('params type must be a list or tuple not %s.' % type(params)))
    param_list = []
    for p in params:
        if isinstance(p, tuple):
            param_list.append(Param(*p))
        elif isinstance(p, Param):
            param_list.append(p)
        else:
            raise TypeError('Api params type %s should be Param object or tuple not %s.' % (p, type(p).__name__))
    return param_list


def define_api(url, params=None, headers=None, desc='', display=True):
    docs_params = list(params) if params else []
    docs_params.extend(config.DOCS_GLOBAL_PARAMS)
    docs_headers = list(headers) if headers else []
    docs_headers.extend(config.DOCS_GLOBAL_HEADERS)
    docs_params = check_param(docs_params)
    docs_headers = check_param(docs_headers)

    def decorator(handler):
        method = handler.__name__
        route.register(handler=handler, url=url, params=docs_params,
                       headers=docs_headers,
                       desc=desc, method=method,
                       display=display)

        @functools.wraps(handler)
        def request_handler(self, *args, **kwargs):
            self._docs_params[method] = {param['field_name']: param for param in docs_params}
            self._docs_headers[method] = {header['field_name']: header for header in docs_headers}
            return handler(self, *args, **kwargs)

        return request_handler

    return decorator


class Endpoint(object):
    def __init__(self, pattern, handler, method, headers, params, name_parent, desc=None):
        self.pattern = pattern
        self.callback = handler
        self.docstring = self.get_doc()
        self.desc = desc
        self.name_parent = name_parent.split('.')[-1].title()
        alias = config.INSTALL_HANDLERS_NAME.get(name_parent) or None
        if alias:
            self.name_parent = alias

        self.path = pattern
        self.methods = [method, ]
        self.params = {method: params}
        self.headers = {method: headers}

    def __str__(self):
        return self.docstring

    @property
    def allowed_methods(self):
        return self.methods

    @property
    def template_method_length(self):
        return len(self.allowed_methods)

    @property
    def template_title_length(self):
        return 12 - len(self.allowed_methods)

    @property
    def params_json(self):
        return self.get_params_json(self.params)

    @property
    def headers_json(self):
        return self.get_params_json(self.headers)

    def get_params_json(self, param_dict):
        data = {}
        for method, params in param_dict.items():
            tmp = []
            for p in params:
                tmp.append(p.kwargs)
            data[method] = tmp
        return json.dumps({'data': data})

    def get_doc(self):
        meta_doc = inspect.getdoc(self.callback)
        if meta_doc:
            return meta_doc.replace('\n', '<br>').replace(' ', '&nbsp;')
        return meta_doc


class Param(dict):
    """
    Parameters for building API documents.
    >>> Param('field_name', True, 'type', 'default_value', 'description')
    """

    def __init__(self, field_name, required, param_type, default='', description=''):
        """
        :param field_name:
        :param required:
        :param param_type: int, str, file
        :param default:
        :param description:
        """
        super(dict, self).__init__()
        self['field_name'] = field_name
        self['required'] = required
        if not isinstance(param_type, str):
            param_type = param_type.__name__
        self['param_type'] = param_type
        self['default'] = default
        self['description'] = description

    @property
    def kwargs(self):
        return {
            'field_name': self['field_name'],
            'required': self['required'],
            'param_type': self['param_type'],
            'default': self['default'],
            'description': self['description'],
        }


class _RouterMetaclass(type):
    """
    A singleton metaclass.
    """
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(_RouterMetaclass, self).__call__(*args, **kwargs)
        return self._instances[self]


class Router(metaclass=_RouterMetaclass):
    def __init__(self):
        self._registry = {}
        self.endpoints = []
        self.handlers_param = {}

    def register(self, **kwargs):
        handler = kwargs['handler']
        if self._registry.get(handler.__module__) is None:
            self._registry[handler.__module__] = [kwargs, ]
        else:
            self._registry[handler.__module__].append(kwargs)

    def get_handlers(self):
        """
        Return a list of URL patterns, given the registered handlers.
        """
        handlers_map = {}
        if config.DEBUG:
            handlers_map['/tornado_docs'] = DocsHandler
            handlers_map['/tornado_docs/'] = DocsHandler
            handlers_map['/tornado_docs/login'] = DocsLoginHandler
            handlers_map['/tornado_docs/login/'] = DocsLoginHandler
            handlers_map['/tornado_docs/markdown'] = DocsMarkdownHandler
            handlers_map['/tornado_docs/markdown/'] = DocsMarkdownHandler

        for handler in config.INSTALL_HANDLERS:
            import_string(handler + '.__name__')

        for module, param in self._registry.items():
            m = import_string(module)
            for p in param:
                func, regex, params, headers, desc, display = p['handler'], p['url'], p[
                    'params'], p['headers'], p['desc'], p['display']
                handler_name, method = func.__qualname__.split('.')
                # Class
                handler = getattr(m, handler_name)  # type: tornado.web.RequestHandler
                method = method.upper()
                if method not in handler.SUPPORTED_METHODS:
                    # Method is invalid
                    raise type('HttpMethodError', (Exception,), {})(_('%s is not an HTTP method.' % method))

                if not regex.startswith('/'):
                    regex = '/' + regex

                if regex in handlers_map and handler != handlers_map[regex]:
                    continue

                # Compatible with '/' and ''
                if regex.endswith('/'):
                    handlers_map[regex.rstrip('/')] = handler
                else:
                    handlers_map[regex + '/'] = handler

                handlers_map[regex] = handler

                if display:
                    for endpoint in self.endpoints:
                        if endpoint.path == regex:
                            if method not in endpoint.methods:
                                endpoint.methods.append(method)
                                endpoint.params[method], endpoint.headers[method] = params, headers
                                break
                    else:
                        endpoint = Endpoint(pattern=regex, handler=handler, method=method, headers=headers,
                                            params=params,
                                            name_parent=module, desc=desc)
                        if method != "OPTIONS":
                            endpoint.methods.append("OPTIONS")
                            endpoint.params["OPTIONS"], endpoint.headers["OPTIONS"] = [], []
                        self.endpoints.append(endpoint)
        return [(regex, handler) for regex, handler in handlers_map.items()]

    @property
    def handlers(self):
        if not hasattr(self, '_handlers'):
            self._handlers = self.get_handlers()
        return self._handlers


route = Router()
