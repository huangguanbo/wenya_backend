"""认证类 API：每条 API 一个独立测试。"""

from tests.conftest import PASSWORD


def test_auth_login(client, make_user):
    make_user('alice')
    res = client.post('/api/auth/login', json={'username': 'alice', 'password': PASSWORD})
    assert res.status_code == 200
    assert res.get_json()['data']['user']['username'] == 'alice'


def test_auth_logout(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.post('/api/auth/logout')
    assert res.status_code == 200
    assert client.get('/api/auth/me').status_code == 401


def test_auth_change_password(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.post('/api/auth/change-password', json={'old_password': PASSWORD, 'new_password': 'NewPass456'})
    assert res.status_code == 200


def test_auth_profile_get(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.get('/api/auth/profile')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert 'user' in data and 'guardian' in data


def test_auth_profile_put(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.put('/api/auth/profile', json={'nickname': '小A', 'show_works_publicly': False})
    assert res.status_code == 200
    user = res.get_json()['data']['user']
    assert user['nickname'] == '小A'
    assert user['show_works_publicly'] is False


def test_auth_export_data(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.post('/api/auth/export-data')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['user']['username'] == 'alice'


def test_auth_me(client, make_user, login):
    make_user('bob')
    login('bob')
    res = client.get('/api/auth/me')
    assert res.status_code == 200
    assert res.get_json()['data']['user']['username'] == 'bob'
