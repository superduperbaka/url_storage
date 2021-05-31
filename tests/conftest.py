import pytest

from starlette.testclient import TestClient
from backend.main import SqlClient, SqlResultProxy, app, get_db


class DummySqlClient(SqlClient):

    def connect(self, dsn: str, **kwargs):
        pass

    def disconnect(self):
        pass

    async def execute(self, sql_stmt) -> SqlResultProxy:
        pass


class DummySqlClientWithExc(SqlClient):

    def __init__(self, exc):
        self.exc = exc

    def connect(self, dsn: str, **kwargs):
        pass

    def disconnect(self):
        pass

    async def execute(self, sql_stmt) -> SqlResultProxy:
        raise self.exc


class CustomSqlClient(SqlClient):
    def __init__(self, result):
        self.result = result

    def connect(self, dsn: str, **kwargs):
        pass

    def disconnect(self):
        pass

    async def execute(self, sql_stmt) -> SqlResultProxy:
        return self.result


class CustomSqlResultProxy(SqlResultProxy):
    def fetch_one(self):
        return self.sa_proxy

    def fetch_all(self):
        return self.sa_proxy


@pytest.fixture()
def backend() -> TestClient:
    client = TestClient(app)
    return client


@pytest.fixture()
def dummy_backend() -> TestClient:
    app.dependency_overrides[get_db] = DummySqlClient
    client = TestClient(app)
    return client


@pytest.fixture()
def backend_with_sql_exc(request):
    custom = DummySqlClientWithExc(request.param[0])
    app.dependency_overrides[get_db] = lambda: custom
    client = TestClient(app)
    return client


@pytest.fixture()
def backend_with_custom_response(request):
    custom = CustomSqlClient(CustomSqlResultProxy(request.param[0]))
    app.dependency_overrides[get_db] = lambda: custom
    client = TestClient(app)
    return client
