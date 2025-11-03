-- 数据库初始化脚本
-- 创建pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建数据库（如果使用单独的数据库）
-- 注意：这个脚本会在PostgreSQL容器启动时自动执行
