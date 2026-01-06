-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create default user for MVP
INSERT INTO users (id, email, display_name, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo@gentleman-coach.local',
    'Demo User',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;
