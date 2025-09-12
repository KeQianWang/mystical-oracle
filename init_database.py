"""
Mystical Oracle Database Initialization Script
数据库初始化脚本，用于创建数据库和表
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import create_tables, check_database_connection
from config.settings import config
from config.logger import server_logger


def main():
    """主函数"""
    print("🔮 Mystical Oracle 数据库初始化...")

    # 检查配置
    required_env_vars = [
        "MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE",
        "JWT_SECRET_KEY"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("请检查 .env 文件或设置相应的环境变量")
        sys.exit(1)

    # 检查数据库连接
    print("📡 检查数据库连接...")
    if not check_database_connection():
        print("❌ 数据库连接失败")
        print("请检查数据库配置和连接")
        sys.exit(1)

    print("✅ 数据库连接正常")

    # 创建数据库表
    print("🏗️  创建数据库表...")
    try:
        create_tables()
        print("✅ 数据库表创建成功")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        sys.exit(1)
    
    print("🎉 数据库初始化完成！")
    print("\n📋 可用的API接口:")
    print("- POST /auth/register - 用户注册")
    print("- POST /auth/login - 用户登录")
    print("- GET /auth/me - 获取当前用户信息")
    print("- PUT /auth/me - 更新用户信息")
    print("- POST /chat - 聊天对话")
    print("- GET /chat/sessions - 获取聊天会话列表")
    print("- GET /chat/history - 获取聊天历史记录")
    print("- GET /chat/session/{session_id}/history - 获取特定会话的历史")
    print("- PUT /chat/session/{session_id}/title - 更新会话标题")
    print("- DELETE /chat/session/{session_id} - 删除会话")
    print("- GET /chat/stats - 获取聊天统计")
    print("- GET /chat/recent - 获取最近聊天记录")
    print("- GET /health - 健康检查")
    print("- POST /add_urls - 添加网页到知识库")
    print("- GET /audio/{audio_id} - 获取音频文件")


if __name__ == "__main__":
    main()