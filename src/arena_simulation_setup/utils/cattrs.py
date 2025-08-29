import abc
import typing

import attr
import cattrs

converter = cattrs.Converter()

ParseableT = typing.TypeVar('ParseableT', bound='Parseable')


class Parseable(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def parse(cls: typing.Type[ParseableT], value: typing.Any) -> ParseableT:
        raise NotImplementedError("Subclasses must implement parse method")


def register_parse(cls: typing.Type[ParseableT]) -> typing.Type[ParseableT]:

    def try_parse(data):
        try:
            return converter.structure_attrs_fromdict(data, cls)
            
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
