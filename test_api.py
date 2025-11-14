#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本 - 验证后端服务功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """测试登录功能"""
    print("\n=== 测试登录 ===")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    return data.get("token")

def test_query(token, query):
    """测试查询功能"""
    print(f"\n=== 测试查询: {query} ===")
    response = requests.post(
        f"{BASE_URL}/api/chat/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "history": []}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"回答: {data.get('answer', '')[:200]}...")
    print(f"检索到 {len(data.get('hits', []))} 条证据")
    return data

def test_config(token):
    """测试配置查询"""
    print("\n=== 测试配置查询 ===")
    response = requests.get(
        f"{BASE_URL}/api/config/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"配置: {json.dumps(data, indent=2, ensure_ascii=False)}")

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

if __name__ == "__main__":
    print("开始测试API...")
    
    # 健康检查
    test_health()
    
    # 登录
    token = test_login()
    
    if token:
        # 查询配置
        test_config(token)
        
        # 测试查询
        test_query(token, "查询三木集团的风险状况")
        test_query(token, "分析农产品行业风险")
    
    print("\n测试完成！")
