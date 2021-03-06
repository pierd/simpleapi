# -*- coding: utf-8 -*-

try:
    import json
except ImportError:
    try:
        from django.utils import simplejson as json
    except Exception, e:
        import simplejson as json

__all__ = ('json', 'SAException')


class SAException(Exception):
    def __init__(self, msg=None, code=-1):
        super(Exception, self).__init__()
        self.code = code
        self._message = msg

    def _get_message(self):
        return self._message

    def _set_message(self, message):
        self._message = message

    message = property(_get_message, _set_message)

    def __repr__(self):
        return self.message

    def get_error_dict(self):
        return {'code': self.code, 'message': self.message}
