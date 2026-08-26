-- =========================================================
-- MyAnimeList Merchandise Finder - Supabase Database Schema
-- =========================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mal_username TEXT UNIQUE NOT NULL,
    mal_user_id INTEGER UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: anime_lists
CREATE TABLE IF NOT EXISTS anime_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mal_anime_id INTEGER NOT NULL,
    anime_title TEXT NOT NULL,
    anime_image_url TEXT,
    watch_status TEXT NOT NULL, -- watching, completed, plan_to_watch, dropped, on_hold
    score INTEGER,
    last_synced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, mal_anime_id)
);

-- Table: products
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anime_id INTEGER,
    anime_title TEXT NOT NULL,
    product_title TEXT NOT NULL,
    product_url TEXT NOT NULL,
    image_url TEXT,
    price NUMERIC(10, 2),
    currency TEXT DEFAULT 'USD',
    store TEXT NOT NULL, -- aliexpress, amazon, ebay, etsy, crunchyroll
    product_type TEXT NOT NULL, -- figure, clothing, accessory, replica, poster, plush
    asin_or_product_id TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_available BOOLEAN DEFAULT TRUE,
    UNIQUE(store, asin_or_product_id)
);

-- Table: search_cache
CREATE TABLE IF NOT EXISTS search_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anime_title TEXT NOT NULL,
    store TEXT NOT NULL,
    product_type TEXT NOT NULL,
    search_query TEXT NOT NULL,
    results_json JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(anime_title, store, product_type)
);

-- Table: user_favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_title TEXT NOT NULL,
    product_url TEXT NOT NULL,
    image_url TEXT,
    price NUMERIC(10, 2),
    currency TEXT DEFAULT 'USD',
    store TEXT NOT NULL,
    anime_title TEXT NOT NULL,
    product_type TEXT NOT NULL,
    favorited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

-- Table: user_activity
CREATE TABLE IF NOT EXISTS user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    product_id TEXT,
    action_type TEXT NOT NULL, -- viewed, clicked, favorited
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_anime_lists_user_id ON anime_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_products_anime_title ON products(anime_title);
CREATE INDEX IF NOT EXISTS idx_products_store ON products(store);
CREATE INDEX IF NOT EXISTS idx_search_cache_lookup ON search_cache(anime_title, store, product_type);
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
