from typing import Any

import factory
from factory import enums
from factory.alchemy import SQLAlchemyOptions
from factory.base import Factory, FactoryMetaClass, StubObject, T
from factory.errors import UnknownStrategy
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.util import await_only, greenlet_spawn

from app.db.base import async_session_maker


def default_session_maker():
    return async_session_maker


class AsyncFactoryMetaClass(FactoryMetaClass):  # type: ignore[misc]
    async def __call__(cls, **kwargs: Any) -> T | StubObject:  # noqa: N805
        if cls._meta.strategy == enums.BUILD_STRATEGY:
            return await cls.build(**kwargs)

        if cls._meta.strategy == enums.CREATE_STRATEGY:
            return await cls.create(**kwargs)

        if cls._meta.strategy == enums.STUB_STRATEGY:
            return cls.stub(**kwargs)

        raise UnknownStrategy(
            f"Unknown '{cls.__name__}.Meta.strategy': {cls._meta.strategy}"
        )


class AsyncSQLAlchemyOptions(SQLAlchemyOptions):
    def _build_default_options(self):
        return [
            *super()._build_default_options(),
            factory.base.OptionDefault(
                "async_session_maker_factory", default_session_maker, inherit=True
            ),
        ]


class AsyncFactory(Factory, metaclass=AsyncFactoryMetaClass):
    _options_class = AsyncSQLAlchemyOptions

    class Meta:
        abstract = True

    @classmethod
    async def create(cls, **kwargs: Any) -> T:
        return await greenlet_spawn(cls._generate, enums.CREATE_STRATEGY, kwargs)

    @classmethod
    async def create_batch(cls, size: int, **kwargs: Any) -> list[T]:
        return [await cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def _create(cls, model_class: type[Any], *args: Any, **kwargs: Any) -> T:
        return await_only(cls._asave(model_class, *args, **kwargs))

    @classmethod
    async def clear(cls):
        _session_maker = cls._meta.async_session_maker_factory()
        model = cls._meta.model
        try:
            async with _session_maker() as session, session.begin():
                await session.execute(delete(model))
        except SQLAlchemyError:
            await session.rollback()
            raise

    @classmethod
    async def _asave(cls, model_class, *args, **kwargs):
        _session_maker = cls._meta.async_session_maker_factory()
        async with (
            _session_maker() as session,
            session.begin(),
        ):
            obj = model_class(*args, **kwargs)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
        return obj
