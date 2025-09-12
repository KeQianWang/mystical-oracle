"""
Mystical Oracle API Usage Examples
API使用示例
"""

import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8001"

def test_user_registration():
    """测试用户注册"""
    print("=== 用户注册 ===")
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "nickname": "测试用户"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    if response.status_code == 200:
        return user_data["username"], user_data["password"]
    else:
        return None, None

def test_user_login(username, password):
    """测试用户登录"""
    print("\n=== 用户登录 ===")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None

def test_get_user_info(token):
    """测试获取用户信息"""
    print("\n=== 获取用户信息 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_chat(token):
    """测试聊天功能"""
    print("\n=== 聊天测试 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    chat_data = {"query": "你好，我想了解一下我的运势"}
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_chat_history(token):
    """测试聊天历史记录"""
    print("\n=== 聊天历史记录 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取聊天会话列表
    response = requests.get(f"{BASE_URL}/chat/sessions", headers=headers)
    print(f"会话列表状态码: {response.status_code}")
    print(f"会话列表响应: {response.json()}")
    
    # 获取聊天历史
    response = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    print(f"历史记录状态码: {response.status_code}")
    print(f"历史记录响应: {response.json()}")

def test_chat_stats(token):
    """测试聊天统计"""
    print("\n=== 聊天统计 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/chat/stats", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def main():
    """主函数"""
    print("🔮 Mystical Oracle API 测试")
    print("=" * 50)
    
    # 1. 用户注册
    username, password = test_user_registration()
    
    if username is None:
        print("❌ 用户注册失败")
        return
    
    # 2. 用户登录
    token = test_user_login(username, password)
    
    if token is None:
        print("❌ 用户登录失败")
        return
    
    # 3. 获取用户信息
    test_get_user_info(token)
    
    # 4. 测试聊天功能
    test_chat(token)
    
    # 5. 测试聊天历史记录
    test_chat_history(token)
    
    # 6. 测试聊天统计
    test_chat_stats(token)
    
    print("\n🎉 API 测试完成！")

if __name__ == "__main__":
    main()