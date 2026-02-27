import requests

# 创建会话对象
session = requests.Session()
session.timeout = 10
session.base_url = 'http://localhost:8010'

async def post(url, params=None, config=None):
    if params is None:
        params = {}
    if config is None:
        config = {}
    
    # 处理validCode参数
    valid_code = params.pop('validCode', None)
    
    # 构建请求头
    headers = config.get('headers', {})
    headers.setdefault('Content-Type', 'application/json')
    
    try:
        response = session.post(url, json=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise e

async def get(url, params=None, config=None):
    if params is None:
        params = {}
    if config is None:
        config = {}
    
    try:
        response = session.get(url, params=params, **config)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise e

async def upload(url, params=None, config=None):
    if params is None:
        params = {}
    if config is None:
        config = {}
    
    headers = config.get('headers', {})
    headers.setdefault('Content-Type', 'multipart/form-data')
    
    try:
        response = session.post(url, data={'params': params}, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise e
