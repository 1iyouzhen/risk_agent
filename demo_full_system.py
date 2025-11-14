#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整系统演示脚本
展示登录、查询、多轮对话的完整流程
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def demo_login():
    """演示登录功能"""
    print_section("1. 用户登录")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ 登录成功！")
        print(f"  用户: {data['user']['username']}")
        print(f"  角色: {data['user']['role']}")
        print(f"  Token: {data['token'][:20]}...")
        return data['token']
    else:
        print("✗ 登录失败")
        return None

def demo_single_query(token, query):
    """演示单次查询"""
    print(f"\n查询: {query}")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/chat/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "history": []}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功")
        print(f"  检索证据: {len(data.get('hits', []))} 条")
        print(f"  有效性: {'是' if data.get('valid') else '否'}")
        print(f"\n回答:")
        print(data.get('answer', '无回答')[:300] + "...")
        return data
    else:
        print(f"✗ 查询失败: {response.status_code}")
        return None

def demo_multi_turn_conversation(token):
    """演示多轮对话"""
    print_section("3. 多轮对话演示")
    
    conversation = []
    queries = [
        "查询三木集团的风险状况",
        "它的主要风险因素是什么？",
        "应该如何应对这些风险？"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n第{i}轮对话:")
        print(f"用户: {query}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "history": conversation}
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            print(f"助手: {answer[:150]}...")
            
            # 更新对话历史
            conversation.append({"role": "user", "content": query})
            conversation.append({"role": "assistant", "content": answer})
        
        time.sleep(1)  # 避免请求过快

def demo_config_check(token):
    """演示配置查询"""
    print_section("4. 系统配置检查")
    
    response = requests.get(
        f"{BASE_URL}/api/config/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        config = data.get('config', {})
        
        print("LLM配置:")
        llm = config.get('llm', {})
        print(f"  模型: {llm.get('model')}")
        print(f"  API配置: {'✓' if llm.get('api_key_configured') else '✗'}")
        
        print("\n嵌入模型:")
        embed = config.get('embedding', {})
        print(f"  提供商: {embed.get('provider')}")
        print(f"  模型: {embed.get('model')}")
        
        print("\nRAG配置:")
        rag = config.get('rag', {})
        print(f"  Top-K: {rag.get('top_k')}")
        print(f"  最小分数: {rag.get('min_score')}")
        
        print("\nNeo4j:")
        neo4j = config.get('neo4j', {})
        print(f"  状态: {'✓ 可用' if neo4j.get('available') else '✗ 不可用'}")
        
        print("\n数据库:")
        db = config.get('database', {})
        print(f"  路径: {db.get('path')}")
        print(f"  存在: {'✓' if db.get('exists') else '✗'}")

def main():
    print("\n" + "="*60)
    print("  金融AI风险评估系统 - 完整功能演示")
    print("="*60)
    print("\n请确保后端服务已启动: python auth_server.py")
    input("\n按回车键开始演示...")
    
    # 1. 登录
    token = demo_login()
    if not token:
        print("\n演示终止：登录失败")
        return
    
    time.sleep(1)
    
    # 2. 单次查询
    print_section("2. 单次查询演示")
    demo_single_query(token, "查询三木集团的最新风险状况")
    time.sleep(1)
    demo_single_query(token, "分析农产品行业的系统性风险")
    
    time.sleep(1)
    
    # 3. 多轮对话
    demo_multi_turn_conversation(token)
    
    time.sleep(1)
    
    # 4. 配置检查
    demo_config_check(token)
    
    print_section("演示完成")
    print("\n✓ 所有功能演示完毕！")
    print("\n提示:")
    print("  - 打开 index.html 体验完整Web界面")
    print("  - 访问 http://localhost:8000/docs 查看API文档")
    print("  - 查看 html_reports/ 目录获取生成的报告")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ 错误: 无法连接到后端服务")
        print("  请先启动后端: python auth_server.py")
    except KeyboardInterrupt:
        print("\n\n演示已中断")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
