"""
Unit tests for communications server
Author: Muhammad Bhutta
"""

import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from solver_server.communications.server import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    """Test home endpoint returns correct info"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'
    assert data['author'] == 'Muhammad Bhutta'


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'solver-server'


def test_solve_endpoint_accepts_post(client):
    """Test that solve endpoint accepts POST requests"""
    test_data = {
        "sections": "test_csv",
        "faculty": "test_csv",
        "preferences": "test_csv"
    }
    
    response = client.post('/solve',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


def test_solve_endpoint_rejects_get(client):
    """Test that solve endpoint rejects GET requests"""
    response = client.get('/solve')
    assert response.status_code == 405  # Method Not Allowed


def test_solve_with_empty_data(client):
    """Test error handling with empty data"""
    response = client.post('/solve',
                          data=json.dumps({}),
                          content_type='application/json')
    
    # Should still return 200 with stub response
    assert response.status_code == 200


def test_solve_with_no_data(client):
    """Test error handling with no JSON data"""
    response = client.post('/solve',
                          data="not json",
                          content_type='application/json')
    
    assert response.status_code == 400


def test_solve_returns_required_fields(client):
    """Test that response contains all required fields"""
    test_data = {
        "sections": "test",
        "faculty": "test"
    }
    
    response = client.post('/solve',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    data = json.loads(response.data)
    assert 'status' in data
    assert 'message' in data
    assert 'violations' in data
    assert 'warnings' in data
    assert 'recommendations' in data
    assert 'timestamp' in data