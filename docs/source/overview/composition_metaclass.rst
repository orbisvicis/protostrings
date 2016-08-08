Composition Metaclass
=====================

.. include:: <isoamsa.txt>

.. __: https://en.wikipedia.org/wiki/Composition_over_inheritance

The :py:class:`.Composition` metaclass helps to implement subtyping via `composition rather than inheritance`__. Inheritance still provides the method resolution order that defines the interface, however all operations that haven't been overloaded are forwarded to a contained object. Without composition, conversions within an object's type hierarchy (base instance |srarr| subtype instance |srarr| base instance) can not preserve the :py:func:`id` of the underlying object. While an instance's :py:attr:`~instance.__class__` attribute controls its type and thus method resolution order, modifying :py:attr:`~instance.__class__` does not affect non-method attributes, and therefore is not a true form of type 'casting'. A non-composed child instance can only recreate an equivalent base instance by calling the base class' initializer with cherry-picked parameters. On the other hand, composed instances can simply be unwrapped.

Classes which are instances of :py:class:`.Composition` have the following properties:


Instantiation
-------------

When instantiated with a single argument, and that argument is already an instance of the class, return that argument unmodified. Other than that, the arguments determine the contained object. When instantiated with a single argument, and that argument is an instance of the class' :py:attr:`~class.__mro__` (all the bases of the class, recursively), that argument becomes the contained object. Otherwise, instantiate the class' base with the provided arguments; the result becomes the contained object.


Initialization
--------------

The contained object is then passed to the initializers: :py:meth:`~object.__new__`, :py:meth:`~object.__init__`. However any user-provided initializers within the class' namespace will be wrapped by metaclass-provided initializers. The wrappers establish the composition environment, assigning the contained object to the instance attribute :py:attr:`~.instance.source`, before calling their wrapped counterparts *without passing along the contained object*. Missing initializers are resolved using standard attribute lookup; these will not be wrapped and should expect to receive a single optional argument, the contained object. This allows subtyping composition-style classes with standard python behaviour. Since neither :py:meth:`~object.__new__` nor :py:meth:`~object.__init__` meet this criteria, at some point in the hierarchy both initializers must be overridden. Obviously, additional initialization arguments are not possible (without complicated and non-standard parameter inspection).


Attribute Lookup
----------------

Attributes not found on the class are forwarded to the contained object.
