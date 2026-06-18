"""A minimal singleton metaclass shared across the package."""

from __future__ import annotations


class Singleton(type):
    """Metaclass that caches one instance per class.

    Calling ``Cls(...)`` again returns the cached instance and does **not**
    re-run ``__init__``. Tests clear :attr:`_instances` to get fresh instances.
    """

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):  # noqa: ANN002, ANN003, ANN204
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
