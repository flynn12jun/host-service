"""
LLM 连通性测试脚本
测试 LongCat 和 GLM 两个模型是否可用

使用方法：
    cd backend
    python test_llm.py
"""

import asyncio
import sys
import os

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import LLMService
from core.config import settings


async def test_model(model_name: str, api_key: str, base_url: str):
    """测试单个模型"""
    print(f"\n{'='*50}")
    print(f"测试模型: {model_name}")
    print(f"API Base URL: {base_url}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    print(f"{'='*50}")
    
    try:
        llm = LLMService(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        
        result = await llm.generate(
            system_prompt="你是一个友好的AI助手。请用一句话介绍自己。",
            user_prompt="你好，请简单介绍一下你自己。",
            response_format="text",
            max_tokens=100,
        )
        
        print(f"✅ 模型 {model_name} 调用成功！")
        print(f"响应内容: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 模型 {model_name} 调用失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("开始 LLM 连通性测试...")
    print(f"当前默认模型: {settings.DEFAULT_LLM_MODEL}")
    
    results = {}
    
    # 测试 LongCat
    if settings.LONGCAT_API_KEY:
        # 测试多个可能的模型名
        longcat_models = ["LongCat-2.0", "longcat-chat", "longcat"]
        for model in longcat_models:
            success = await test_model(
                model_name=model,
                api_key=settings.LONGCAT_API_KEY,
                base_url=settings.LONGCAT_BASE_URL,
            )
            results[f"LongCat ({model})"] = success
            if success:
                break  # 有一个成功就行
    else:
        print("\n⚠️  LONGCAT_API_KEY 未配置，跳过 LongCat 测试")
    
    # 测试 GLM
    if settings.ZHIPU_API_KEY:
        success = await test_model(
            model_name="glm-4",
            api_key=settings.ZHIPU_API_KEY,
            base_url=settings.ZHIPU_BASE_URL,
        )
        results["GLM (glm-4)"] = success
    else:
        print("\n⚠️  ZHIPU_API_KEY 未配置，跳过 GLM 测试")
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试结果汇总")
    print(f"{'='*50}")
    
    for model_name, success in results.items():
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"  {model_name}: {status}")
    
    # 给出建议
    print(f"\n{'='*50}")
    print("建议")
    print(f"{'='*50}")
    
    if any(results.values()):
        working_models = [k for k, v in results.items() if v]
        print(f"可用模型: {', '.join(working_models)}")
        print(f"建议在 .env 中设置: DEFAULT_LLM_MODEL={working_models[0].split('(')[1].rstrip(')') if '(' in working_models[0] else working_models[0]}")
    else:
        print("所有模型均不可用，请检查：")
        print("  1. API Key 是否正确")
        print("  2. Base URL 是否正确")
        print("  3. 网络是否连通")
        print("  4. 模型名称是否正确")


if __name__ == "__main__":
    asyncio.run(main())
