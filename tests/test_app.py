import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Изменение контрастности' in response.data

def test_file_upload_no_file(client):
    """Тест загрузки без файла"""
    response = client.post('/process', data={})
    assert response.status_code == 400
    assert b'error' in response.data

def test_download_invalid_file(client):
    """Тест скачивания несуществующего файла"""
    response = client.get('/download/nonexistent.jpg')
    assert response.status_code == 404
