#!/usr/bin/env python
#
# copyright:
#   2016    pscjtwjdjtAhnbjm/dpn
# license:
#   GPLv3

import decorator
import inspect


class LazyString:
    def __init__(self, f):
        self.f = f

    def __call__(self):
        return self.f()

    def __str__(self):
        return str(self())

    def __repr__(self):
        return "{}{}".format\
                ( type(self).__name__
                , str(inspect.signature(self.f))
                )

    def __add__(self, other):
        if not isinstance(other, (str, type(self))):
            return NotImplemented
        def f(l=self, r=other):
            r1 = r() if isinstance(r, type(l)) else r
            l1 = l()
            return l1 + r1
        #f = lambda l=self, r=other: str(l) + str(r)
        return type(self)(f)

    def __radd__(self, other):
        if not isinstance(other, (str, type(self))):
            return NotImplemented
        def f(l=other, r=self):
            l1 = l() if isinstance(l, type(r)) else l
            r1 = r()
            return l1 + r1
        #f = lambda l=other, r=self: str(l) + str(r)
        return type(self)(f)

    def __iter__(self):
        yield self
        children = self.f.__defaults__ or ()
        for d in children:
            if isinstance(d, LazyString):
                yield from d
            else:
                yield d

    def leaves(self):
        yield from (n for n in self if
                    not isinstance(n, LazyString)
                    or not n.f.__defaults__
                   )

    def copy(self, f=None):
        f = self.f if f is None else f
        return type(self)(f)

    @staticmethod
    def modify_defaults(f, defaults):
        """Return a copy of the function `f` with
           :py:attr:`~definition.__defaults__` set to `defaults`
        """
        @decorator.decorator
        def wrapper(f, *args, **kwargs):
            return f(*args, **kwargs)
        wrapped = wrapper(f)
        wrapped.__defaults__ = defaults
        return wrapped

    def memoize_self(self):
        return LazyStringMemo(self)

    def memoize(self, wrap = lambda lazy_string: lazy_string.memoize_self()):
        if not self.f.__defaults__:
            defaults = self.f.__defaults__
        else:
            defaults = (    d.memoize(wrap=wrap)
                       if isinstance(d, LazyString) else
                            d
                       for d in self.f.__defaults__
                       )
            defaults = tuple(defaults)
        if defaults == self.f.__defaults__:
            f = self.f
        else:
            f = self.modify_defaults(self.f, defaults)
        if f == self.f:
            lazy_string = self
        else:
            lazy_string = self.copy(f)
        return wrap(lazy_string)

    def pprint(self, signature=True):
        def format_data(item, depth, signature):
            name = type(item).__name__
            if isinstance(item, LazyString):
                details_full = str(inspect.signature(item.f))
                details_trim = "(...)"
                if not signature and len(details_trim) < len(details_full):
                    details = details_trim
                else:
                    details = details_full
            else:
                details = repr(item)
            return (depth, name, details)
        def format_lazy(lazy_string, depth=0, signature=True):
            data = [format_data(lazy_string, depth, signature)]
            if not lazy_string.f.__defaults__:
                return data
            depth += 1
            for d in lazy_string.f.__defaults__:
                if isinstance(d, LazyString):
                    data.extend(format_lazy(d, depth, signature))
                else:
                    data.append(format_data(d, depth, signature))
            return data
        def string_lazy(data):
            rows = [((" " * depth * 4) + name, details)
                    for (depth, name, details) in  data
                   ]
            span = max(len(i[0]) for i in rows)
            fill = 4 - ((span - 1) % 4 + 1)
            fill = fill + 4 if fill <= 2 else fill
            span = span + fill
            text = ""
            for name, details in rows:
                text += "{:<{}}{}\n".format(name, span, details)
            return text.rstrip()
        data = format_lazy(self, signature=signature)
        text = string_lazy(data)
        print(text)


class Composition(type):
    def __call__(self, *args, **kwargs):
        if not kwargs and len(args) == 1 and isinstance(args[0], self):
            return args[0]
        if not kwargs and len(args) == 1 and isinstance(args[0], self.__mro__[1:-1]):
            source = args[0]
        else:
            source = self.__mro__[1](*args, **kwargs)
        return super().__call__(source)

    def __init__(self, name, bases, namespace):
        def __getattr__(self, name):
            return getattr(self.source, name)
        def __new__(cls, source=None):
            __new__inner = namespace.get\
                    ( "__new__"
                    , super(self, cls).__new__
                    )
            return __new__inner(cls)
        def __init__(self_inner, source=None):
            __init__inner = namespace.get\
                ( "__init__"
                , super(self, self_inner).__init__.__func__
                )
            if source is not None:
                self_inner.source = source
            else:
                assert hasattr(self_inner, "source")
            return __init__inner(self_inner)
        def add_function(f, when_present=False, when_absent=True):
            if f.__name__ in namespace and not when_present:
                return
            if f.__name__ not in namespace and not when_absent:
                return
            f.__qualname__ = "{}.{}".format(name, f.__name__)
            setattr(self, f.__name__, f)
        add_function(__getattr__)
        add_function(__new__, when_present=True, when_absent=False)
        add_function(__init__, when_present=True, when_absent=False)
        return super().__init__(name, bases, namespace)


# Since python has no concept of 'casting', composition is used in addition to
# subtyping. Without composition, conversions to and from LazyStringMemo can
# not preserve the id() of the underlying LazyString objects.  LazyStringMemo's
# __init__ would have to decompose input LazyString objects to the underlying
# functions before calling super(). Converting the results back to LazyString
# would create new objects. Composition ensures a LazyString object wrapped
# into LazyStringMemo will, when unwrapped, return the *same* LazyString
# object.
class LazyStringMemo(LazyString, metaclass=Composition):
    def __init__(self):
        self.data = None
        self.evaluated = False

    def __call__(self):
        if not self.evaluated:
            self.data = self.source()
            self.evaluated = True
        return self.data

    def __repr__(self):
        if self.evaluated:
            return "{}(...) -> {!r}".format\
                    ( type(self).__name__
                    , self.data
                    )
        else:
            return super().__repr__()

    def __add__(self, other):
        if self.evaluated:
            return self.data + other
        else:
            return super().__add__(other)

    def __radd__(self, other):
        if self.evaluated:
            return other + self.data
        else:
            return super().__radd__(other)


class ContextStringValueError(ValueError):
    def __init__(self, c="", l=None, r=None):
        super().__init__(c,l,r)
        self.l = l
        self.c = c
        self.r = r
        self.__str_result = None
        self.__str_cached = False
        self.__sum_result = None
        self.__sum_cached = False

    def __iter__(self):
        def f(self):
            if self.l:
                yield self.l
            if isinstance(self.c, ContextStringValueError):
                yield from self.c
            else:
                yield self.c
            if self.r:
                yield self.r
        return f(self)

    def sum(self):
        if not self.__sum_cached:
            if isinstance(self.c, ContextStringValueError):
                s = self.c.sum()
            else:
                s = self.c
            if self.r is not None:
                s = s + self.r
            if self.l is not None:
                s = self.l + s
            self.__sum_result = s
            self.__sum_cached = True
        return self.__sum_result

    def __str__(self):
        if not self.__str_cached:
            s = str(self.c)
            if self.r is not None:
                s = s + str(self.r)
            if self.l is not None:
                s = str(self.l) + s
            self.__str_result = s
            self.__str_cached = True
        return self.__str_result

    def add(self, lhs, rhs):
        return type(self)(self, lhs, rhs)

    def pop(self):
        return self.c


class ContextString(LazyString):
    def __init__(self, f, l=True, r=True):
        super().__init__(f)
        self.l = l
        self.r = r

    def copy(self, f=None, l=None, r=None):
        f = self.f if f is None else f
        l = self.l if l is None else l
        r = self.r if r is None else r
        return type(self)(f, l, r)

    def memoize_self(self):
        return ContextStringMemo(self)

    def __call__(self, lhs="", rhs=""):
        assert isinstance(lhs, str)
        assert isinstance(rhs, str)
        return self.f(lhs=lhs, rhs=rhs)

    def __bind(self, lhs="", rhs=""):
        assert isinstance(lhs, str)
        assert isinstance(rhs, str)
        try:
            return self(lhs, rhs)
        except ContextStringValueError as e:
            def f(lhs, rhs, l=lhs, c=self, r=rhs):
                return c(lhs + l, r + rhs)
            return type(self)(f, l=self.l, r=self.r)

    def __str_or_lazy(self):
        try:
            value = self()
        except ContextStringValueError as e:
            # May cause double lazy string evaluation if the contained objects
            # cyclically rereference the original error. Avoid via memoization.
            value = e.sum()
        if not isinstance(value, ContextString):
            return value
        else:
            return value.__str_or_lazy()

    def __str__(self):
        try:
            value = self()
        except ContextStringValueError as e:
            return str(e)
        else:
            return str(value)

    def __add__(self, other):
        # self + other
        if isinstance(other, ContextString):
            if self.r and other.l:
                return self.__add_context_overlap(other)
            else:
                return self.__add_context_separate(other)
        elif isinstance(other, str):
            if self.r:
                return self.__add_str_overlap(other)
            else:
                return self.__add_str_separate(other)
        elif isinstance(other, LazyString):
            if self.r:
                return self.__add_lazy_overlap(other)
            else:
                return self.__add_lazy_separate(other)
        else:
            return NotImplemented

    def __add_lazy_overlap(self, other):
        # ?--[self/context]--> + [other/lazy]
        def f(l=self, r=other):
            return l + r()
        #f = lambda l=self, r=other: l(rhs=str(r)) + str(r)
        return type(other)(f)

    def __add_lazy_separate(self, other):
        # ?--[self/context] + [other/lazy]
        def f(lhs, rhs, l=self, r=other):
            try:
                return l(lhs=lhs) + r
            except ContextStringValueError as e:
                raise e.add(None, r) from None
        return type(self)(f, l=self.l, r=False)

    def __add_str_overlap(self, other):
        # ?--[self/context]--> + [other/str]
        try:
            return self(rhs=other) + other
        except ContextStringValueError:
            def f(lhs, rhs, l=self, r=other):
                try:
                    return l(lhs, r + rhs) + r
                except ContextStringValueError as e:
                    raise e.add(None, r) from None
            return type(self)(f, self.l, self.r)

    def __add_str_separate(self, other):
        # ?--[self/context] + [other/str]
        def f(lhs, rhs, l=self, r=other):
            try:
                return l(lhs=lhs) + r
            except ContextStringValueError as e:
                raise e.add(None, r) from None
        return type(self)(f, l=self.l, r=False)

    def __add_context_overlap(self, other):
        # ?--[self/context]--> + <--[other/context]--?
        def contains_lazy(context_string):
            match = lambda d:   (       isinstance(d, LazyString)
                                and not isinstance(d, ContextString)
                                )
            return any(match(d) for d in context_string)

        def f0(l0=self, r0=other):
            def wrap(lazy_string):
                assert isinstance(lazy_string, LazyString)
                if isinstance(lazy_string, ContextString):
                    return lazy_string
                else:
                    return lazy_string.memoize_self()

            l0 = l0.memoize(wrap=wrap)
            r0 = r0.memoize(wrap=wrap)

            lhs = str(l0)
            rhs = str(r0)

            l1 = l0.__bind(rhs=rhs)
            if not isinstance(l1, ContextString):
                return l1 + r0

            r1 = r0.__bind(lhs=lhs)
            if not isinstance(r1, ContextString):
                return l0 + r1

            if not l1.r or not r1.l:
                return l1 + r1

            def f1(lhs, rhs, l=l1, r=r1):
                try:
                    l1 = l(lhs=lhs, rhs=rhs)
                except ContextStringValueError as e0:
                    try:
                        r1 = r(lhs=lhs, rhs=rhs)
                    except ContextStringValueError as e1:
                        r1 = e1
                    raise e0.add(None, str(r1)) from None
                try:
                    r1 = r(lhs=lhs, rhs=rhs)
                except ContextStringValueError as e0:
                    try:
                        l1 = l(lhs=lhs, rhs=rhs)
                    except ContextStringValueError as e1:
                        l1 = e1
                    raise e0.add(str(l1), None) from None
                return l1 + r1

            return type(l0)(f1, r1.l, l1.r)

        if contains_lazy(self) or contains_lazy(other):
            return LazyString(f0)
        else:
            return f0()

    def __add_context_separate(self, other):
        # ?--[self/context]    +    [other/context]--?
        # ?--[self/context]--> +    [other/context]--?
        # ?--[self/context]    + <--[other/context]--?
        def f(lhs, rhs, l=self, r=other):
            #print("__add_context_separate_delegator('{}', '{}')".format(lhs, rhs))
            try:
                l1 = l(lhs=lhs) if (l.l and not l.r) else l
            except ContextStringValueError as e:
                def f(lhs=lhs, rhs=rhs, l=e, r=r):
                    try:
                        return r(lhs=lhs + str(l), rhs=rhs)
                    except ContextStringValueError as e:
                        return str(e)
                value = LazyString(f)
                raise e.add(None, value) from None
            try:
                r1 = r(rhs=rhs) if (r.r and not r.l) else r
            except ContextStringValueError as e:
                def f(lhs=lhs, rhs=rhs, l=l, r=e):
                    try:
                        return l(lhs=lhs, rhs=str(r) + rhs)
                    except ContextStringValueError as e:
                        return str(e)
                value = LazyString(f)
                raise e.add(value, None) from None
            #print("{:#x}/{} + {:#x}/{}".format(
            #    id(l1), type(l1).__name__, id(r1), type(r1).__name__)
            #)
            return l1 + r1
        return type(self)(f, self.l, other.r)

    def __radd__(self, other):
        # other + self
        # should be handled in __add__
        assert not isinstance(other, ContextString)
        if isinstance(other, str):
            if self.l:
                return self.__radd_str_overlap(other)
            else:
                return self.__radd_str_separate(other)
        elif isinstance(other, LazyString):
            if self.l:
                return self.__radd_lazy_overlap(other)
            else:
                return self.__radd_lazy_separate(other)
        else:
            return NotImplemented

    def __radd_lazy_overlap(self, other):
        # [other/lazy] + <--[self/context]--?
        def f(l=other, r=self):
            return l() + r
        return type(other)(f)

    def __radd_lazy_separate(self, other):
        # [other/lazy] + [self/context]--?
        def f(lhs, rhs, l=other, r=self):
            try:
                return l + r(rhs=rhs)
            except ContextStringValueError as e:
                raise e.add(l, None) from None
        return type(self)(f, l=False, r=self.r)

    def __radd_str_overlap(self, other):
        # [other/str] + <--[self/context]--?
        try:
            return other + self(lhs=other)
        except ContextStringValueError:
            def f(lhs, rhs, l=other, r=self):
                try:
                    return l + r(lhs + l, rhs)
                except ContextStringValueError as e:
                    raise e.add(l, None) from None
            return type(self)(f, self.l, self.r)

    def __radd_str_separate(self, other):
        # [other/str] + [self/context]--?
        def f(lhs, rhs, l=other, r=self):
            try:
                return l + r(rhs=rhs)
            except ContextStringValueError as e:
                raise e.add(l, None) from None
        return type(self)(f, l=False, r=self.r)


class ContextStringMemo(ContextString, metaclass=Composition):
    def __init__(self):
        self.data_raised = {}
        self.data_return = {}

    def __call__(self, lhs="", rhs=""):
        key = (lhs, rhs)
        try:
            raise self.data_raised[key]
        except KeyError:
            pass
        try:
            return self.data_return[key]
        except KeyError:
            pass
        try:
            data_return = self.source(lhs, rhs)
            self.data_return[key] = data_return
            return data_return
        except ContextStringValueError as data_raised:
            self.data_raised[key] = data_raised
            raise data_raised from None


def lazy_string(f):
    return LazyString(f)


def context_string(l=True, r=True):
    def context_string(f, l=l, r=r):
        return ContextString(f, l, r)
    return context_string
