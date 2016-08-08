Context Strings
===============

Context strings are intended to represent eager, pure units of computation whose results depend on surrounding context - values to the left or right. The underlying function is evaluated with this context as two keyword arguments, ``lhs`` and ``rhs``. Without sufficient context a :py:exc:`.ContextStringValueError` exception can be raised, containing a fallback value. To reduce overhead, context strings must declare which sides require context - the default is both left and right.

>>> @context_string(r=False)
... def cs_left(lhs, rhs):
...     data = "inner"
...     if not lhs:
...         raise ContextStringValueError(data)
...     if lhs[-1] == "(":
...         return "{})".format(data)
...     else:
...         return data
... 
>>> "apply(" + cs_left + "[0]"
'apply(inner)[0]'
>>> "drab " + cs_left + " moods"
'drab inner moods'
>>> "" + cs_left
ContextString(lhs, rhs, l='', r=ContextString(lhs, rhs))
>>> str("" + cs_left)
'inner'

>>> @context_string()
... def cs_both(lhs, rhs):
...     data = "word"
...     if lhs and lhs[-1] != " ":
...         data = " " + data
...     if rhs and rhs[0] != " ":
...         data = data + " "
...     if not (lhs and rhs):
...         raise ContextStringValueError(data)
...     return data
... 
>>> "a drab" + cs_both + "then nothing"
'a drab word then nothing'
>>> "... " + cs_both + "..."
'... word ...'
>>> "a drab" + cs_both
ContextString(lhs, rhs, l='a drab', r=ContextString(lhs, rhs))
>>> str("a drab" + cs_both)
'a drab word'

>>> @context_string(l=False)
... def cs_right(lhs, rhs):
...     animals = { "cat"
...               , "dog"
...               , "bird"
...               , "squirrel"
...               }
...     inputs = set(rhs.split())
...     if len(inputs) <= 3:
...         data = "(Error: insufficient data)"
...         if rhs:
...             data = data + " "
...         raise ContextStringValueError(data)
...     if animals >= inputs:
...         return "zebra "
...     elif inputs & animals:
...         return "(does zebra count?) "
...     else:
...         return "(clearly not a list of animals) "
... 
>>> cs_right + "cat " + "dog " + "bird"
ContextString(lhs, rhs, l=ContextString(lhs, rhs, l=ContextString(lhs, rhs, l=ContextString(lhs, rhs), r='cat '), r='dog '), r='bird')
>>> str(cs_right + "cat " + "dog " + "bird")
'(Error: insufficient data) cat dog bird'
>>> cs_right + "cat " + "dog " + "bird " + "squirrel"
'zebra cat dog bird squirrel'
>>> cs_right + "cat " + "dog " + "bird " + "trident"
'(does zebra count?) cat dog bird trident'
>>> cs_right + "car " + "bus " "motorcycle " + "train"
'(clearly not a list of animals) car bus motorcycle train'


Side Effects
------------

Context strings are a subclass of lazy strings, allowing :py:meth:`.ContextString.__radd__` to override :py:meth:`.LazyString.__add__`. Though recursively evaluated over and over with partial inputs, any referenced lazy strings will themselves only be computed once per :py:func:`str`, thus allowing for predictable side-effects. Given the lazy and context strings from above, modified to emit logging statements, during evaluation each lazy string will be computed once and only once:

>>> test = (cs_left + ls) + cs_left + ls
>>> test.pprint(False)
ContextString               (...)
    ContextString           (...)
        ContextString       (...)
            ContextString   (...)
            LazyString      ()
        ContextString       (...)
    LazyString              ()
>>> str(test)  # same results if evaluated again
cs_left()    : entering
ls()         : entering
cs_left()    : entering
ls()         : entering
'inner@@@@@inner@@@@@'

>>> test = (cs_left + ls) + (cs_left + ls)
>>> test.pprint(False)
ContextString           (...)
    ContextString       (...)
        ContextString   (...)
        LazyString      ()
    ContextString       (...)
        ContextString   (...)
        LazyString      ()
>>> str(test)  # same results if evaluated again
cs_left()    : entering
ls()         : entering
cs_left()    : entering
ls()         : entering
'inner@@@@@inner@@@@@'

>>> test = cs_both + (cs_left + ls)
>>> test.pprint(False)
LazyString              (...)
    ContextString       (...)
    ContextString       (...)
        ContextString   (...)
        LazyString      ()
>>> str(test)  # same results if evaluated again
cs_both()    : entering
cs_left()    : entering
ls()         : entering
cs_both()    : entering
cs_left()    : entering
cs_both()    : entering
cs_both()    : entering
'word inner@@@@@'


Evaluation
----------

Though strings, lazy strings, and context strings interact naturally, the resulting type across all possible combinations may be any of the three. In other words, evaluating a lazy string or context string may result in a string, lazy string, or context string. As a rule of thumb, whenever an eager computation encounters a lazy computation, a lazy (deferred) computation is produced. The following table illustrates all possible combinations:

.. |c_l|    replace:: :math:`\strut\overleftarrow{context}`
.. |c_r|    replace:: :math:`\strut\overrightarrow{context}`
.. |c_b|    replace:: :math:`\strut\overleftrightarrow{context}`
.. |c_l_i|  replace:: :math:`\small\smash{\overleftarrow{\Rule{0em}{0.4em}{0em}\smash{\texttt{context}}}}\normalsize`
.. |c_r_i|  replace:: :math:`\small\smash{\overrightarrow{\Rule{0em}{0.4em}{0em}\smash{\texttt{context}}}}\normalsize`
.. |c_l_a|  replace:: :math:`\strut\overleftarrow{context}()`
.. |c_r_a|  replace:: :math:`\strut\overrightarrow{context}()`
.. |c_b_a|  replace:: :math:`\strut\overleftrightarrow{context}()`
.. |l|      replace:: :math:`\strut\vphantom{\overleftarrow{\mathcal{lazy}}}\mathcal{lazy}`
.. |s|      replace:: :math:`\strut\vphantom{\overleftarrow{\mathcal{str}}}\mathcal{str}`

.. rst-class:: fullwidth

+-------------------------+-------------------------+
| combination             | result(s)               |
+=========================+=========================+
| | |c_l| + |s|           | | |c_l|                 |
| | |c_l| + |l|           | |                       |
| | |c_l| + |c_l|         | |                       |
+-------------------------+-------------------------+
| | |c_l| + |c_r|         | | |c_b|                 |
| | |c_l| + |c_b|         | |                       |
+-------------------------+-------------------------+
| | |c_r| + |s|           | | |c_r|                 |
| |                       | | |c_r_a| + |s|         |
+-------------------------+-------------------------+
| | |c_r| + |l|           | | |l|                   |
+-------------------------+-------------------------+
| | |c_r| + |c_l|         | | |l|                   |
| |                       | | |c_r| + |c_l_a|       |
| |                       | | |c_r_a| + |c_l|       |
| |                       | | |c_r_a| + |c_l_a|     |
| |                       | | |c_b|                 |
+-------------------------+-------------------------+
| | |c_r| + |c_r|         | | |c_r|                 |
+-------------------------+-------------------------+
| | |c_r| + |c_b|         | | |l|                   |
| |                       | | |c_r| + |c_b_a|       |
| |                       | | |c_r_a| + |c_b|       |
| |                       | | |c_r_a| + |c_b_a|     |
| |                       | | |c_b|                 |
+-------------------------+-------------------------+
| | |c_b| + |s|           | | |c_b|                 |
| |                       | | |c_b_a| + |s|         |
+-------------------------+-------------------------+
| | |c_b| + |l|           | | |l|                   |
+-------------------------+-------------------------+
| | |c_b| + |c_l|         | | |l|                   |
| |                       | | |c_b| + |c_l_a|       |
| |                       | | |c_b_a| + |c_l|       |
| |                       | | |c_b_a| + |c_l_a|     |
| |                       | | |c_b|                 |
+-------------------------+-------------------------+
| | |c_b| + |c_r|         | | |c_b|                 |
+-------------------------+-------------------------+
| | |c_b| + |c_b|         | | |l|                   |
| |                       | | |c_b| + |c_b_a|       |
| |                       | | |c_b_a| + |c_b|       |
| |                       | | |c_b_a| + |c_b_a|     |
| |                       | | |c_b|                 |
+-------------------------+-------------------------+


Overlap
-------

Overlapping context strings such as |c_r_i| + |c_l_i| reference each other circularly: |c_r_i| requires |c_l_i|, which requires |c_r_i|, which requires |c_l_i|, and so on. In such cases each instance is evaluated (to :py:class:`str`) without context and bound to their counterpart; recursion is limited to a single layer:

.. math::

    a_1 + \ldots + a_i + \overrightarrow{context} &+ \overleftarrow{context} + a_{i+1} + \ldots + a_n = \\
    \Bigl[&\overrightarrow{context}.\_bind(str(\overleftarrow{context})) + a_{i+1} + \ldots + a_n\Bigr] +\\
    \Bigl[a_1 + \ldots + a_i  +\ &\overleftarrow{context}.\_bind(str(\overrightarrow{context}))\Bigr]


Exceptions
----------

:py:exc:`.ContextStringValueError` exceptions are like telescoping linked lists. Though structured like ternary trees they are constrained to lists by their methods. Adding or removing (:py:meth:`~.ContextStringValueError.add`, :py:meth:`~.ContextStringValueError.pop`) nodes returns new objects; this is so nodes can reference positions within the list without infinite recursion. Evaluation (:py:meth:`~.ContextStringValueError.__str__`, :py:meth:`~.ContextStringValueError.sum`) memoizes each node; each method maintains independent caches. Note however that :py:meth:`~.ContextStringValueError.sum` does not prevent re-evaluation of nodes within self-referential lists - such as a node containing a :py:class:`.LazyString` instance whose arguments refer back to another node within the list.

.. graphviz:: /_static/ContextStringValueError.graph.gv
    :alt: ContextStringValueErrorGraph
    :align: center

>>> list(protostrings.ContextStringValueError("widely")
...   .add("a","used")
...   .add("is","programming")
...   .add("Python","language")
... )
['Python', 'is', 'a', 'widely', 'used', 'programming', 'language']
