import requests
import json

BASE_URL = 'http://localhost:8000/api/auth'

def test_user_endpoints():
    # 1. Login to get token
    login_data = {
        'username': 'admin',
        'password': 'testpass1234'
    }
    
    print("1. Testing login...")
    response = requests.post(f'{BASE_URL}/login/', json=login_data)
    print(f"Login response: {response.status_code}")
    print(response.text)
    
    if response.status_code == 200:
        token = response.json()['access']
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 2. Test edit user
        print("\n2. Testing edit user...")
        edit_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'student',
            'name': 'Test User',
            'nisn': '12345'
        }
        response = requests.put(f'{BASE_URL}/edit/1/', json=edit_data, headers=headers)
        print(f"Edit user response: {response.status_code}")
        print(response.text)
        
        # 3. Test delete user
        print("\n3. Testing delete user...")
        response = requests.delete(f'{BASE_URL}/delete/2/', headers=headers)
        print(f"Delete user response: {response.status_code}")
        print(response.text)
    
if __name__ == '__main__':
    test_user_endpoints() 