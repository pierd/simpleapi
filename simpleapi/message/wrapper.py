# -*- coding: utf-8 -*-

from simpleapi.message.common import json

__all__ = ('wrappers', 'Wrapper', 'DefaultWrapper')


class WrappersSingleton(object):
    """This singleton takes care of all registered wrappers. You can easily
    register your own wrapper for use in both the Namespace and python client.
    """

    _wrappers = {}

    def __new__(cls):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        return it

    def register(self, name, wrapper, override=False):
        """
            Register the given wrapper
        """
        if not isinstance(wrapper(None, ), Wrapper):
            raise TypeError(u"You can only register a Wrapper not a %s" % wrapper)

        if name in self._wrappers and not override:
            raise AttributeError(u"%s is already a valid wrapper type, try a new name" % name)

        self._wrappers[name] = wrapper

    def copy(self):
        return dict(**self._wrappers)

    def __contains__(self, value):
        return value in self._wrappers

    def __getitem__(self, name):
        return self._wrappers.get(name)

    def __setitem__(self, *args):
        raise AttributeError

wrappers = WrappersSingleton()


class Wrapper(object):
    """The baseclass wrapper you can use as a basis for your own wrapper"""

    def __init__(self, sapi_request):
        self.sapi_request = sapi_request
        self.session = getattr(sapi_request, 'session', None)

    def _build(self, error, result):
        return self.build(error=error, result=result)

    def _parse(self, items):
        return self.parse(items=items)

    def parse(self, items):
        raise NotImplementedError

    def build(self, error, result):
        raise NotImplementedError


class DefaultWrapper(Wrapper):
    def parse(self, items):
        return items

    def build(self, error, result):
        r = {}
        if error:
            r['success'] = False
        else:
            r['success'] = True
        if error:
            r['error'] = error
        if result is not None:
            r['result'] = result
        return r


class ExtJSWrapper(Wrapper):
    @staticmethod
    def build_error(error):
        assert isinstance(error, (basestring, tuple, list))

        if isinstance(error, basestring) or (isinstance(error, (tuple, list)) and len(error) == 1):
            return {
                'msg': isinstance(error, (tuple, list)) and error[0] or error
            }
        elif isinstance(error, (tuple, list)) and len(error) > 0:
            errmsg, error = error[0], error[1]
            assert isinstance(errmsg, basestring)
            assert isinstance(error, dict)

            return {
                'msg': errmsg,
                'error': error,
            }

    def parse(self, items):
        return items

    def build(self, error, result):
        r = {}
        if error:
            r['success'] = False
        else:
            r['success'] = True
        if error:
            r.update(self.build_error(error))

        if result is not None:
            for key, value in self.build_result(result):
                r[key] = value

        return r

class ExtJSFormWrapper(ExtJSWrapper):
    def build_result(self, result):
        yield ('data', result)

class ExtJSStoreWrapper(ExtJSWrapper):
    def build_result(self, result):
        yield ('rows', result)
        yield ('results', len(result))

class ExtJSDirectWrapper(Wrapper):
    def build(self, error, result):
        if hasattr(self.session._internal, 'extdirect'):
            db = self.session._internal.extdirect[0]
            self.session._internal.extdirect = \
                self.session._internal.extdirect[1:]
        else:
            db = {}
        if db['formHandler'] == True:
            r = {
                'type': db['type'],
                'tid': db['tid'],
                'action': db['action'],
                'method': db['method'],
                'result': {}
            }

            if error:
                r['result'].update(ExtJSWrapper.build_error(error))
                r['result']['success'] = False
            else:
                r['result']['success'] = True
                r['result']['data'] = result

            return r
        else:
            if error:
                error = ExtJSWrapper.build_error(error)
                return {
                    'type': 'exception',
                    'message': error['msg'],
                    'where': 'n/a'
                }
            else:
                return {
                    'result': result,
                    'type': db['type'],
                    'tid': db['tid'],
                    'action': db['action'],
                    'method': db['method'],
                }

    def parse(self, items):
        if len(items) == 1:
            # check for a batch request
            key, value = items.items()[0]
            if value == '':
                data = json.loads(key)
                if isinstance(data, dict):
                    yield self.parse_item(data)
                elif isinstance(data, (tuple, list)):
                    for item in data:
                        yield self.parse_item(item)
                else:
                    raise ValueError(u'Unsupported input format.')
            else:
                raise ValueError(u'Unsupported input format.')
        else:
            s = self.parse_item(items)
            yield s

    def parse_item(self, data):
        if data.has_key('extMethod'):
            # formHandler true
            d = {
                '_call': data.pop('extMethod', ''),
            }

            tid = data.pop('extTID', '')
            action = data.pop('extAction', '')
            method = d['_call']
            type = data.pop('extType', '')

            if not hasattr(self.session._internal, 'extdirect'):
                self.session._internal.extdirect = []

            db = {}
            db['formHandler'] = True
            db['type'] = type
            db['action'] = action
            db['method'] = method
            db['tid'] = tid
            self.session._internal.extdirect.append(db)

            d.update(data)
            return d
        else:
            # formHandle false
            d = {
                '_call': data.pop('method', ''),
            }

            if data.get('data') and len(data['data']) > 0 and \
                not isinstance(data['data'][0], dict):
                raise ValueError(u'data must be a hashable/an array of key/value arguments')

            tid = data.pop('tid', '')
            action = data.pop('action', '')
            method = d['_call']
            type = data.pop('type', '')

            if not hasattr(self.session._internal, 'extdirect'):
                self.session._internal.extdirect = []

            db = {}
            db['formHandler'] = False
            db['type'] = type
            db['action'] = action
            db['method'] = method
            db['tid'] = tid
            self.session._internal.extdirect.append(db)

            data = data.get('data')
            if data:
                data = data[0]
            else:
                data = {}
            d.update(data)
            return d

wrappers.register('default', DefaultWrapper)
wrappers.register('extjsform', ExtJSFormWrapper)
wrappers.register('extjsstore', ExtJSStoreWrapper)
wrappers.register('extjsdirect', ExtJSDirectWrapper)
