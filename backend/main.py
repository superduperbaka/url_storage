import datetime as dt
import logging

from abc import ABCMeta, abstractmethod
from http import HTTPStatus
from typing import Any, List, Dict, Optional

import sqlalchemy
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from backend.schemas import CreateRequest, Statistics
from backend.db_schemas import create_link_entry, get_link_entry, create_redirect_entry, get_stat, get_stat_summary
from backend.settings_schemas import PostgreSQLSettings


class CustomExceptions(Exception):
    pass


class AlreadyExists(CustomExceptions):
    pass


class NoDbConnection(CustomExceptions):
    pass


class SqlResultProxy:

    def __init__(self, sa_proxy):
        self.sa_proxy = sa_proxy

    def fetch_one(self) -> Optional[Dict[str, Any]]:
        if value := self.sa_proxy.fetchone():
            return dict(value)

    def fetch_all(self) -> List[Dict[str, Any]]:
        return [dict(i) for i in self.sa_proxy.fetchall()]


class SqlClient(metaclass=ABCMeta):
    @abstractmethod
    def connect(self, dsn: str, **kwargs):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    async def execute(self, sql_stmt) -> SqlResultProxy:
        pass


class AsyncSa(SqlClient, metaclass=ABCMeta):
    _engine: sqlalchemy.ext.asyncio.engine.AsyncEngine

    def connect(self, dsn: str, **kwargs):
        self._engine = create_async_engine(dsn, echo=True)

    def disconnect(self):
        self._engine.dispose()

    async def execute(self, sql_stmt) -> SqlResultProxy:
        logging.debug(f'Executing \'{sql_stmt}\'.')
        async with self._engine.connect() as conn:
            try:
                result = await conn.execute(sql_stmt)
                await conn.commit()
                return SqlResultProxy(result)
            except IntegrityError:
                logging.exception(f'Integrity error occurred while executing \'{sql_stmt}\'.')
                await conn.rollback()
                raise AlreadyExists()


def get_db() -> SqlClient:
    return async_sql_client


async_sql_client = AsyncSa()
app = FastAPI()


@app.post('/p', status_code=HTTPStatus.CREATED)
async def create_short_name(req_data: CreateRequest, sql_client: AsyncSa = Depends(get_db)):
    sql_stmt = create_link_entry(link=req_data.link, short_name=req_data.short_name)
    try:
        await sql_client.execute(sql_stmt)
    except AlreadyExists:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f'Short link \'{req_data.short_name}\' already in db.',
        )


async def log_redirect(
        link_id: int,
        timestamp: dt.datetime,
        sql_client: SqlClient,
):
    sql_stmt = create_redirect_entry(link_id=link_id, timestamp=timestamp)
    await sql_client.execute(sql_stmt)


@app.get('/p/{short_name}', status_code=HTTPStatus.TEMPORARY_REDIRECT)
async def get_url(
        short_name: str,
        background_tasks: BackgroundTasks,
        sql_client: SqlClient = Depends(get_db),
):
    sql_stmt = get_link_entry(short_name=short_name)
    result = await sql_client.execute(sql_stmt)
    if result := result.fetch_one():
        background_tasks.add_task(
            func=log_redirect,
            link_id=result.get('id'),
            timestamp=dt.datetime.utcnow(),
            sql_client=sql_client,
        )
        return RedirectResponse(result.get('link'))
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Unknown short link \'{short_name}\'.'
        )


@app.get('/stat/{short_name}', response_model=Statistics)
async def statistics(short_name: str, sql_client: SqlClient = Depends(get_db)):
    sql_stmt = get_stat(short_name)
    result = await sql_client.execute(sql_stmt=sql_stmt)
    value = result.fetch_one()
    return Statistics(short_name=short_name, count=value.get('count'))


@app.get('/stat', response_model=List[Statistics])
async def statistics_sum(sql_client: SqlClient = Depends(get_db)):
    sql_stmt = get_stat_summary()
    result = await sql_client.execute(sql_stmt)
    return [Statistics(**i) for i in result.fetch_all()]


@app.on_event('startup')
async def startup():
    print('SLAJFLKASJFLAKSFJLASJFLJKASJ, ', PostgreSQLSettings().postgres_dsn)
    print('postgresql+asyncpg://postgres:somefancypass@localhost/postgres')
    import asyncio
    # await asyncio.sleep(20)
    async_sql_client.connect(dsn=PostgreSQLSettings().postgres_dsn)


@app.on_event('shutdown')
async def shutdown():
    async_sql_client.disconnect()
