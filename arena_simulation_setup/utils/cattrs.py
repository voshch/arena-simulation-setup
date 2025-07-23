import cattrs
import typing
import abc

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
        except Exception as e:
            import sys
            print(f"Failed to parse {cls.__name__} with data: {data}", file=sys.stderr)
            return cls.parse(data)

    converter.register_structure_hook(
        cls,
        lambda data, _: try_parse(data)
    )
    return cls


__all__ = [
    "Parseable",
    "register_parse",
    "converter"
]
