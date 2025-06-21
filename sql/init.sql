-- Global Memory Database Initialization Script
-- This script sets up the database schema for the Global Memory MCP Server

-- Enable the pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create uuid extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Episodic Memory Table (Experiences, Conversations, Events)
CREATE TABLE IF NOT EXISTS episodic_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    emotion VARCHAR(50),
    outcome VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    embedding VECTOR(384),  -- Dimension for all-MiniLM-L6-v2
    
    -- Indexes for performance
    CONSTRAINT valid_importance CHECK (importance_score >= 0 AND importance_score <= 1)
);

CREATE INDEX IF NOT EXISTS idx_episodic_agent_id ON episodic_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_episodic_user_id ON episodic_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memories(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic_memories(importance_score);
CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memories(session_id);

-- Semantic Memory Table (Facts, Concepts, Knowledge)
CREATE TABLE IF NOT EXISTS semantic_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    domain VARCHAR(100),
    relations JSONB DEFAULT '{}',
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    source_count INTEGER DEFAULT 1,
    contributors JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(384),
    
    -- Unique constraint on concept+domain combination
    CONSTRAINT unique_concept_domain UNIQUE(concept, domain)
);

CREATE INDEX IF NOT EXISTS idx_semantic_concept ON semantic_memories(concept);
CREATE INDEX IF NOT EXISTS idx_semantic_domain ON semantic_memories(domain);
CREATE INDEX IF NOT EXISTS idx_semantic_confidence ON semantic_memories(confidence_score);
CREATE INDEX IF NOT EXISTS idx_semantic_updated ON semantic_memories(updated_at);

-- Procedural Memory Table (Skills, Methods, How-to Knowledge)
CREATE TABLE IF NOT EXISTS procedural_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    procedure TEXT NOT NULL,
    steps JSONB DEFAULT '[]',
    prerequisites JSONB DEFAULT '[]',
    success_rate FLOAT DEFAULT 0.5 CHECK (success_rate >= 0 AND success_rate <= 1),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    contributors JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(384),
    
    -- Unique constraint on skill_name+domain combination
    CONSTRAINT unique_skill_domain UNIQUE(skill_name, domain)
);

CREATE INDEX IF NOT EXISTS idx_procedural_skill ON procedural_memories(skill_name);
CREATE INDEX IF NOT EXISTS idx_procedural_domain ON procedural_memories(domain);
CREATE INDEX IF NOT EXISTS idx_procedural_success ON procedural_memories(success_rate);
CREATE INDEX IF NOT EXISTS idx_procedural_usage ON procedural_memories(usage_count);

-- Memory Statistics Table
CREATE TABLE IF NOT EXISTS memory_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stats_metric ON memory_statistics(metric_name);
CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON memory_statistics(timestamp);

-- Agent Registry Table
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id VARCHAR(100) PRIMARY KEY,
    agent_type VARCHAR(50),
    capabilities JSONB DEFAULT '[]',
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    memory_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_type ON agent_registry(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_last_active ON agent_registry(last_active);

-- Memory Consolidation Log Table
CREATE TABLE IF NOT EXISTS consolidation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consolidation_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100),
    memories_processed INTEGER DEFAULT 0,
    memories_consolidated INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_consolidation_type ON consolidation_log(consolidation_type);
CREATE INDEX IF NOT EXISTS idx_consolidation_status ON consolidation_log(status);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for automatic timestamp updates
CREATE TRIGGER update_semantic_memories_updated_at 
    BEFORE UPDATE ON semantic_memories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_procedural_memories_updated_at 
    BEFORE UPDATE ON procedural_memories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial system statistics
INSERT INTO memory_statistics (metric_name, metric_value, metadata) VALUES
    ('total_memories', 0, '{"description": "Total number of memories stored"}'),
    ('queries_processed', 0, '{"description": "Total number of queries processed"}'),
    ('cross_agent_shares', 0, '{"description": "Total knowledge sharing events"}'),
    ('memory_consolidations', 0, '{"description": "Total memory consolidations performed"}')
ON CONFLICT DO NOTHING;

-- Create a view for memory overview
CREATE OR REPLACE VIEW memory_overview AS
SELECT 
    'episodic' as memory_type,
    COUNT(*) as total_count,
    AVG(importance_score) as avg_importance,
    COUNT(DISTINCT agent_id) as unique_agents,
    MAX(timestamp) as latest_memory
FROM episodic_memories
UNION ALL
SELECT 
    'semantic' as memory_type,
    COUNT(*) as total_count,
    AVG(confidence_score) as avg_importance,
    COUNT(DISTINCT contributors) as unique_agents,
    MAX(updated_at) as latest_memory
FROM semantic_memories
UNION ALL
SELECT 
    'procedural' as memory_type,
    COUNT(*) as total_count,
    AVG(success_rate) as avg_importance,
    COUNT(DISTINCT contributors) as unique_agents,
    MAX(updated_at) as latest_memory
FROM procedural_memories;

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Global Memory Database initialized successfully!';
    RAISE NOTICE 'Tables created: episodic_memories, semantic_memories, procedural_memories';
    RAISE NOTICE 'Extensions enabled: vector, uuid-ossp';
    RAISE NOTICE 'Indexes and triggers configured for optimal performance';
END $$;
