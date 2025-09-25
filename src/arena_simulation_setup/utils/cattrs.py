from __future__ import annotations

import abc
import typing

from copy import deepcopy

import attr
import cattrs

converter = cattrs.Converter()


class Idempotent:
    """
    A class that ensures its instances are idempotent.
    """

    @classmethod
    def converter(cls, *args, **kwargs):
        """
        If the value is already an instance of the class, return it.
        Otherwise, create a new instance of the class with the value.
        """
        if args and isinstance(args[0], cls):
            return args[0]
        return cls(*args, **kwargs)

    @classmethod
    def converter_clone(cls, *args, **kwargs):
        """
        If the value is already an instance of the class, return a deepcopy of it.
        If not, create a new instance of the class with the value.
        """
        if args and isinstance(args[0], cls):
            return deepcopy(args[0])
        return cls(*args, **kwargs)


T = typing.TypeVar('T')


def idempotent(cls: typing.Type[T]) -> typing.Type[Idempotent, T]:
    """
    Make class idempotent.
    """
    if not issubclass(cls, Idempotent):
        return type(cls.__name__, (Idempotent, cls), {})
    return cls


ParseableT = typing.TypeVar('ParseableT', bound='Parseable')


class Parseable(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def parse(cls: typing.Type[ParseableT], value: typing.Any) -> ParseableT:
        raise NotImplementedError("Subclasses must implement parse method")


def register_parse(cls: typing.Type[ParseableT]) -> typing.Type[ParseableT]:

    def try_parse(data):
        if isinstance(data, cls):
            return data
        try:
            return converter.structure_attrs_fromdict(deepcopy(data), cls)
        except Exception:
            return cls.parse(data)

    converter.register_structure_hook(
        cls,
        lambda data, _: try_parse(data)
    )
    return cls


T = typing.TypeVar('T')
V = typing.TypeVar('V')


def attrs_sequence(type_: typing.Type[V] = typing.Type[typing.Any]):
    del type_

    def decorator(cls: typing.Type[T]):
        fields = attr.fields(cls)
        field_names = [field.name for field in fields]
        num_fields = len(field_names)

        def __len__(self) -> int:
            return num_fields

        def __iter__(self) -> typing.Iterator[V]:
            for name in field_names:
                yield getattr(self, name)

        @typing.overload
        def __getitem__(self, key: int) -> V: ...

        @typing.overload
        def __getitem__(self, key: slice) -> tuple[V, ...]: ...

        def __getitem__(self, key: typing.Union[int, slice]) -> typing.Union[V, tuple[V, ...]]:
            if isinstance(key, slice):
                return tuple(self)[key]
            if isinstance(key, int):
                if key < 0:
                    key += num_fields
                if 0 <= key < num_fields:
                    field_name = field_names[key]
                    return getattr(self, field_name)
                raise IndexError("Attribute index out of range")

            raise TypeError(f"Attribute indices must be integers or slices, not {type(key).__name__}")

        setattr(cls, '__len__', __len__)
        setattr(cls, '__iter__', __iter__)
        setattr(cls, '__getitem__', __getitem__)

        return cls
    return decorator


__all__ = [
    "Parseable",
    "register_parse",
    "converter"
]
