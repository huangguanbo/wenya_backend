"""通用类 API：每条 API 一个独立测试。"""


def test_api_health(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.get_json()['data']['status'] == 'ok'


def test_api_stats(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.get('/api/stats')
    assert res.status_code == 200
    assert 'total_writings' in res.get_json()['data']


def test_api_ai_status(client, make_user, login, real_ai_settings):
    make_user('alice')
    login('alice')
    res = client.get('/api/ai/status')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['scoring']['configured'] is True
    assert data['chat']['configured'] is True


def test_api_compliance_info(client):
    res = client.get('/api/compliance/info')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert 'privacy_policy_url' in data and 'terms_of_service_url' in data


def test_api_notifications(client, make_user, login):
    make_user('alice')
    login('alice')
    res = client.get('/api/notifications')
    assert res.status_code == 200
    assert 'notifications' in res.get_json()['data']


def test_api_challenges(client):
    res = client.get('/api/challenges')
    assert res.status_code == 200
    assert len(res.get_json()['data']['challenges']) > 0


def test_api_challenge_detail(client):
    lst = client.get('/api/challenges').get_json()['data']['challenges']
    cid = lst[0]['id']
    res = client.get(f'/api/challenges/{cid}')
    assert res.status_code == 200
    assert res.get_json()['data']['challenge']['id'] == cid


def test_api_materials(client):
    res = client.get('/api/materials')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert 'materials' in data and 'categories' in data


def test_static_content_apis_allow_anonymous(client):
    """挑战/素材接口为纯静态内容，未登录也应返回 200。"""
    for path in ('/api/challenges', '/api/materials', '/api/materials?category=quote'):
        assert client.get(path).status_code == 200, path


def test_user_scoped_api_rejects_anonymous(client):
    """放开匿名范围仅限静态内容，用户数据接口未登录仍需 401。"""
    assert client.get('/api/stats').status_code == 401
    assert client.get('/api/notifications').status_code == 401
