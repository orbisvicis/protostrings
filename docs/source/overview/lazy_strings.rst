Lazy Strings
============

Lazy strings are intended to represent lazy, impure units of computation:

>>> @lazy_string
... def ls():
...     return v*15
... 
>>> v = "@@"
>>> str(ls)
'@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
>>> v = "+"
>>> str(ls)
'+++++++++++++++'


As previously intimated, lazy strings interact with standard strings:

>>> v = "."
>>> ls1 = ls + "  and then there were none"
>>> type(ls1)
<class 'protostrings.LazyString'>
>>> str(ls1)
'...............  and then there were none'


Memoizing a lazy string prevents side-effects, effectively "locking in" the value:

>>> @lazy_string
... def ls():
...     print("ls(): entering")
...     return v*5
... 
>>> lsm = ls.memoize()
>>> str(lsm)
ls(): entering
'.....'
>>> str(lsm)
'.....'
>>> v = "my"
>>> str(lsm)
'.....'


Combining :py:mod:`protostrings` in effect builds a static tree with nodes stored in each wrapped function's :py:attr:`~definition.__defaults__`. The :py:meth:`~.LazyString.pprint` method provides a human-readable method for visualizing the structure. The boolean ``signature`` argument controls the visibility of each lazy string's signature, eliding to "(...)".

>>> ("foo" + ((ls + "123") + (ls + "123") + "bar") + "baz").pprint(False)
LazyString                          (...)
    LazyString                      (...)
        str                         'foo'
        LazyString                  (...)
            LazyString              (...)
                LazyString          (...)
                    LazyString      ()
                    str             '123'
                LazyString          (...)
                    LazyString      ()
                    str             '123'
            str                     'bar'
    str                             'baz'


And of course, memoization is recursive:

>>> ("foo" + ((ls + "123") + (ls + "123") + "bar") + "baz").memoize().pprint(False)
LazyStringMemo                          (...)
    LazyStringMemo                      (...)
        str                             'foo'
        LazyStringMemo                  (...)
            LazyStringMemo              (...)
                LazyStringMemo          (...)
                    LazyStringMemo      ()
                    str                 '123'
                LazyStringMemo          (...)
                    LazyStringMemo      ()
                    str                 '123'
            str                         'bar'
    str                                 'baz'

Additional, less interesting, methods are also provided:

:py:meth:`~.LazyString.__iter__`
  Iterates over the :py:mod:`protostrings` tree nodes in depth-first order (recursively).

:py:meth:`~.LazyString.leaves`
  Iterates over the :py:mod:`protostrings` tree leaves in depth-first order (recursively) - therefore, in order of appearance.

:py:meth:`~.LazyString.copy`
  Returns a shallow copy of the :py:mod:`protostrings`. This method has the same signature as the initializer, allowing individual arguments to be overridden.

:py:meth:`~.LazyString.memoize_self`
  Override this method to control the memoization target.

Please note that additional user-provided keyword arguments will be interpreted as tree nodes:

>>> @lazy_string
... def ls(a=22, b=33, c=44, d=None, e="word"):
...   return "({})".format(v*5)
>>> ls.pprint(False)
LazyString      (...)
    int         22
    int         33
    int         44
    NoneType    None
    str         'word'
