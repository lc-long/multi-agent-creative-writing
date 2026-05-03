"""
测试阿里云百炼API连接
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def test_api():
    """测试API连接"""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )
    
    model = os.getenv("OPENAI_MODEL", "qwen-turbo")
    
    print(f"测试阿里云百炼API...")
    print(f"模型: {model}")
    print(f"API Base: {os.getenv('OPENAI_API_BASE')}")
    print("-" * 50)
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "你好！请用一句话介绍你自己。"},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        print(f"API响应: {content}")
        print("-" * 50)
        print("✅ API连接成功！")
        
        # 打印usage信息
        if response.usage:
            print(f"Token使用: {response.usage.prompt_tokens} (输入) + {response.usage.completion_tokens} (输出) = {response.usage.total_tokens} (总计)")
        
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    exit(0 if success else 1)
