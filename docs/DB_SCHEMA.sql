-- AAA Engine Database Schema
-- Postgres (Neon/Supabase free-tier)

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT UNIQUE,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE voiceprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  embedding FLOAT8[192],
  sample_count INT DEFAULT 1,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  phrase TEXT,
  token TEXT,
  expires_at TIMESTAMP,
  used BOOLEAN DEFAULT FALSE
);

CREATE TABLE auth_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  challenge_id UUID REFERENCES challenges(id),
  l2_label TEXT,
  l2_confidence FLOAT,
  l1_score FLOAT,
  result TEXT,
  layer_blocked INT,
  created_at TIMESTAMP DEFAULT now()
);
