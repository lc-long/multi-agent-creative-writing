-- Multi-Agent Creative Writing System - Database Initialization Script
-- 用于PostgreSQL数据库初始化

-- 创建数据库（如果不存在）
-- 注意：这个脚本会在Docker容器启动时自动执行

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建会话表
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    theme TEXT NOT NULL,
    genre VARCHAR(50),
    constraints JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- 创建故事表
CREATE TABLE IF NOT EXISTS stories (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
    title VARCHAR(200),
    genre VARCHAR(50),
    synopsis TEXT,
    outline JSONB,
    world_setting JSONB,
    themes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stories_session_id ON stories(session_id);

-- 创建角色表
CREATE TABLE IF NOT EXISTS characters (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    story_id VARCHAR(36) NOT NULL REFERENCES stories(id),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    age INTEGER,
    personality TEXT,
    background TEXT,
    motivation TEXT,
    arc TEXT,
    relationships JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_characters_story_id ON characters(story_id);

-- 创建对话表
CREATE TABLE IF NOT EXISTS dialogues (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    story_id VARCHAR(36) NOT NULL REFERENCES stories(id),
    scene VARCHAR(200),
    participants JSONB,
    content JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dialogues_story_id ON dialogues(story_id);

-- 创建讨论记录表
CREATE TABLE IF NOT EXISTS discussions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
    round INTEGER NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_discussions_session_id ON discussions(session_id);
CREATE INDEX IF NOT EXISTS idx_discussions_round ON discussions(round);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例数据（可选）
-- INSERT INTO sessions (id, status, theme, genre) VALUES
-- ('sess_example', 'completed', '未来世界的AI觉醒', 'science_fiction');
