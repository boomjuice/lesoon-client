import typing as t

from lesoon_common.utils.base import AttributeDict


def type_convert(convertor: t.Callable, key: str = 'body'):

    def wrapper(data: AttributeDict):
        setattr(data, key, convertor(getattr(data, key)))
        return data

    return wrapper
