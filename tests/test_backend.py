import pytest

from backend.main import AlreadyExists


def test_create_endpoint(backend):
    # without json
    assert (backend.post('/p', )).status_code == 422
    # bad link
    with backend.post('/p', json={'link': 'bad_link', 'short_name': 'shortlink'}) as res:
        assert res.status_code == 422
        # check message
        assert 'link' in res.json()['detail'][0]['loc']
    # bad short_name
    with backend.post('/p', json={'link': 'http://example.com', 'short_name': 'shortlink' * 100}) as res:
        assert res.status_code == 422
        # check message
        assert 'short_name' in res.json()['detail'][0]['loc']


def test_create_endpoint_success(dummy_backend):
    with dummy_backend.post('/p', json={'link': 'http://example.com', 'short_name': 'shortlink'}) as res:
        assert res.status_code == 201


@pytest.mark.parametrize('backend_with_sql_exc', [(AlreadyExists, )], indirect=True)
def test_create_endpoint_unique_error(backend_with_sql_exc):
    with backend_with_sql_exc.post('/p', json={'link': 'http://example.com', 'short_name': 'shortlink'}) as res:
        assert res.status_code == 400
        assert 'already in db' in res.json()['detail']


@pytest.mark.parametrize('backend_with_custom_response', [(None,)], indirect=True)
def test_get_short_name_endpoint_not_found(backend_with_custom_response):
    with backend_with_custom_response.get('/p/no_such_name') as res:
        assert res.status_code == 404


@pytest.mark.parametrize('backend_with_custom_response', [({'id': 1, 'link': 'http://example.com'},)], indirect=True)
def test_get_short_name_endpoint_found(backend_with_custom_response):
    with backend_with_custom_response.get('/p/link', allow_redirects=False) as res:
        assert res.status_code == 307


@pytest.mark.parametrize('backend_with_custom_response', [({'count': 42},)], indirect=True)
def test_get_statistics(backend_with_custom_response):
    with backend_with_custom_response.get('/stat/someshortname') as res:
        assert res.status_code == 200
        assert res.json() == {'short_name': 'someshortname', 'count': 42}


@pytest.mark.parametrize('backend_with_custom_response',
                         [([{'short_name': 'name1', 'count': 42},
                            {'short_name': 'name2', 'count': 24},
                            {'short_name': 'name3', 'count': 1}],)], indirect=True)
def test_get_statistics_sum(backend_with_custom_response):
    with backend_with_custom_response.get('/stat') as res:
        assert res.status_code == 200
        assert res.json() == [
            {'short_name': 'name1', 'count': 42},
            {'short_name': 'name2', 'count': 24},
            {'short_name': 'name3', 'count': 1},
        ]
