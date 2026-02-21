import requests
import json

# Test registration endpoint
def test_register():
    url = "http://localhost:8000/api/v1/auth/register"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "testuserapi",
        "email": "testapi@example.com",
        "password": "password123"
    }
    
    print("Testing registration endpoint...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Registration successful!")
            return response.json()
        else:
            print(f"✗ Registration failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

# Test login endpoint
def test_login(username, password):
    url = "http://localhost:8000/api/v1/auth/login"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "username": username,
        "password": password
    }
    
    print("\nTesting login endpoint...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, data=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Login successful!")
            return response.json()
        else:
            print(f"✗ Login failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

# Test me endpoint
def test_me(access_token):
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\nTesting me endpoint...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Me endpoint successful!")
            return response.json()
        else:
            print(f"✗ Me endpoint failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== Testing API Endpoints ===")
    
    # Test registration
    register_response = test_register()
    
    if register_response:
        # Test login with the same credentials
        login_response = test_login("testuserapi", "password123")
        
        if login_response:
            # Test me endpoint with the access token
            access_token = login_response.get("access_token")
            if access_token:
                test_me(access_token)
    
    print("\n=== Test completed ===")
