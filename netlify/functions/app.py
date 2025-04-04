from flask import Flask
import sys
import os

# アプリケーションのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Flaskアプリケーションをインポート
from app import app as flask_app

# Netlify Functionsのハンドラー関数
def handler(event, context):
    """Netlify Functionsのハンドラー関数"""
    path = event.get('path', '').lstrip('/')
    http_method = event.get('httpMethod', '')
    headers = event.get('headers', {})
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')

    # Flaskアプリケーションに渡すための環境を設定
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': f'/{path}',
        'QUERY_STRING': '&'.join([f'{k}={v}' for k, v in query_string.items()]) if query_string else '',
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'HTTP_CONTENT_TYPE': headers.get('content-type', ''),
        'HTTP_ACCEPT': headers.get('accept', ''),
        'HTTP_USER_AGENT': headers.get('user-agent', ''),
        'HTTP_COOKIE': headers.get('cookie', ''),
        'wsgi.input': body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'https',
        'SERVER_NAME': 'netlify',
        'SERVER_PORT': '443',
    }

    # Flaskアプリケーションを実行
    response = flask_app(environ)

    # レスポンスを整形
    status_code = int(response.status.split(' ')[0])
    headers = {k: v for k, v in response.headers}
    body = response.data.decode('utf-8')

    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body,
    }
