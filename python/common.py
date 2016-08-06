# nguyenvankhoi - TIL
# Sat Aug  6 16:51:03 JST 2016


class lazyproperty(object):

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


def lazy(func):
    _dict = {}

    def wrapper(*args, **kwargs):
        if func.__name__ not in _dict:
            _dict[func.__name__] = func(*args, **kwargs)
            return _dict[func.__name__]
    return wrapper


def lazyproperty2(func):
    name = '_lazy_' + func.__name__

    @property
    def wapper(self):
        if hasattr(self, name):
            return getattr(self, name)
        else:
            value = func(self)
            setattr(self, name, value)
            return value
    return wapper


class Sington(type):

    def __init__(self, *args, **kwargs):
        self._instance = None
        super(Sington, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super(Sington, self).__call__(*args, **kwargs)
            return self._instance


def Sington2(_class):
    _instance = {}

    def wraper(*args, **kwargs):
        if _class not in _instance:
            _instance[_class] = _class(*args, **kwargs)
            return _instance[_class]
    return wraper


class BaseClass(object):
    _fields = []

    def __init__(self, *args, **kwargs):
        if len(args) != len(self._fields):
            raise TypeError('Expected {} arguments'.format(len(args)))

        for name, value in zip(self._fields, args):
            setattr(self, name, value)

        # set extra args
        extra_args = set(kwargs.keys()) - set(self._fields)
        print extra_args
        for name in extra_args:
            setattr(self, name, kwargs.pop(name))
        if kwargs:
            raise TypeError('Dublicate value for {}'.format(','.join(kwargs)))


def log_getattribute(cls):
    origin_getattribute = cls.__getattribute__

    def new_getattibute(self, name):
        print ('getting:', name)
        return origin_getattribute(self, name)
    cls.__getattribute__ = new_getattibute
    return cls


if __name__ == '__main__':

    class LazyTest(object):

        @lazyproperty
        def test(self):
            print 'this is code will be run only once'
            return 1

        @lazy
        def test2(self):
            print 'this is code will be run only once'
            return 1

        @lazyproperty2
        def test3(self):
            print 'this is code will be run only once'
            return 1

    class BaseClassTest(BaseClass):
        _fields = ['hihi', 'hehe', 'haha']

    @log_getattribute
    class A(object):

        def __init__(self, x):
            self.x = x

        def spam(self):
            pass

    class SingtonTest:
        __metaclass__ = Sington

        def __init__(self, test):
            self.test = test

    @Sington2
    class SingtonTest2:

        def __init__(self, test):
            self.test = test
