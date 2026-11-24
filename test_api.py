"""Unit tests for User Management API endpoints."""
import unittest
import json
import os
import tempfile
from app import app, init_db


class APITestCase(unittest.TestCase):
    """Test cases for REST API endpoints."""

    def setUp(self):
        """Set up test client and temporary database."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['USE_SQLITE'] = '1'
        os.environ['SQLITE_DB'] = self.db_path
        
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_get_users_empty(self):
        """Test GET /api/users returns empty list initially."""
        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['users'], [])

    def test_create_user(self):
        """Test POST /api/users creates a new user."""
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'address': '123 Main St',
            'phonenumber': '555-0100',
            'password': 'securepass123'
        }
        response = self.client.post('/api/users',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['email'], 'john@example.com')
        self.assertIn('id', data)
        self.assertNotIn('password', data)

    def test_create_user_missing_fields(self):
        """Test POST /api/users with missing required fields."""
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        response = self.client.post('/api/users',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_user_by_id(self):
        """Test GET /api/users/<id> returns specific user."""
        # Create a user first
        user_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'address': '456 Oak Ave',
            'phonenumber': '555-0200',
            'password': 'password123'
        }
        create_response = self.client.post('/api/users',
                                          data=json.dumps(user_data),
                                          content_type='application/json')
        user_id = json.loads(create_response.data)['id']

        # Get the user
        response = self.client.get(f'/api/users/{user_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Jane Smith')
        self.assertEqual(data['email'], 'jane@example.com')

    def test_get_user_not_found(self):
        """Test GET /api/users/<id> with non-existent ID."""
        response = self.client.get('/api/users/9999')
        self.assertEqual(response.status_code, 404)

    def test_delete_user(self):
        """Test DELETE /api/users/<id> removes user."""
        # Create a user
        user_data = {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'address': '789 Pine Rd',
            'phonenumber': '555-0300',
            'password': 'mypassword'
        }
        create_response = self.client.post('/api/users',
                                          data=json.dumps(user_data),
                                          content_type='application/json')
        user_id = json.loads(create_response.data)['id']

        # Delete the user
        response = self.client.delete(f'/api/users/{user_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)

        # Verify user is deleted
        get_response = self.client.get(f'/api/users/{user_id}')
        self.assertEqual(get_response.status_code, 404)

    def test_delete_user_not_found(self):
        """Test DELETE /api/users/<id> with non-existent ID."""
        response = self.client.delete('/api/users/9999')
        self.assertEqual(response.status_code, 404)

    def test_get_all_users(self):
        """Test GET /api/users returns all users."""
        # Create multiple users
        users = [
            {'name': 'User1', 'email': 'user1@test.com', 'address': 'Addr1', 
             'phonenumber': '111-1111', 'password': 'pass1'},
            {'name': 'User2', 'email': 'user2@test.com', 'address': 'Addr2', 
             'phonenumber': '222-2222', 'password': 'pass2'},
        ]
        for user in users:
            self.client.post('/api/users',
                           data=json.dumps(user),
                           content_type='application/json')

        # Get all users
        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 2)

    def test_password_not_returned(self):
        """Test that password is never returned in API responses."""
        user_data = {
            'name': 'Secure User',
            'email': 'secure@example.com',
            'address': '999 Safe St',
            'phonenumber': '555-9999',
            'password': 'supersecret'
        }
        response = self.client.post('/api/users',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertNotIn('password', data)


if __name__ == '__main__':
    unittest.main()
