"""
服务器启动脚本
在启动 uvicorn 之前设置正确的事件循环策略
"""
import sys
import asyncio

# ============================================================================
# 必须在导入任何其他模块之前设置事件循环策略
# ============================================================================
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✅ 已设置 WindowsProactorEventLoopPolicy")

# 现在启动 uvicorn
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # 使用 loop="asyncio" 参数，并且暂时禁用 reload 来测试
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,  # 暂时禁用 reload 进行测试
        loop="asyncio"  # 使用 asyncio 循环
    )
