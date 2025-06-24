-- Mava Supabase Sync Database Schema
-- This file contains the SQL to create all required tables for the Mava sync application

-- Enable UUID extension for better ID handling
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Customers table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    discord_author_id TEXT,
    client TEXT,
    name TEXT,
    avatar_url TEXT,
    discord_joined_at TIMESTAMP WITH TIME ZONE,
    wallet_address TEXT,
    discord_roles JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '[]',
    notes JSONB DEFAULT '[]',
    user_ratings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);

-- 2. Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(id),
    client TEXT,
    status TEXT,
    priority TEXT,
    source_type TEXT,
    category TEXT,
    assigned_to TEXT,
    -- Discord-specific fields
    discord_thread_id TEXT,
    interaction_identifier TEXT,
    is_discord_thread_deleted BOOLEAN DEFAULT FALSE,
    discord_users JSONB DEFAULT '[]',
    -- AI and automation
    ai_status TEXT,
    is_ai_enabled_in_flow_root BOOLEAN DEFAULT FALSE,
    is_button_in_flow_root_clicked BOOLEAN DEFAULT FALSE,
    force_button_selection BOOLEAN DEFAULT FALSE,
    -- User interaction
    is_user_rating_requested BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    mentions JSONB DEFAULT '[]',
    -- Timing information
    first_customer_message_created_at TIMESTAMP WITH TIME ZONE,
    first_agent_message_created_at TIMESTAMP WITH TIME ZONE,
    -- Tags (stored as array)
    tags JSONB DEFAULT '[]',
    -- System fields
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    disabled BOOLEAN DEFAULT FALSE,
    -- Raw data preservation
    raw_data JSONB
);

-- 3. Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES tickets(id),
    sender TEXT,
    sender_reference_type TEXT,
    from_customer BOOLEAN DEFAULT FALSE,
    content TEXT,
    is_picture BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    message_type TEXT,
    message_status TEXT,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    read_by JSONB DEFAULT '[]',
    mentions JSONB DEFAULT '[]',
    pre_submission_identifier TEXT,
    foreign_identifier TEXT,
    action_log_from TEXT,
    action_log_to TEXT,
    replied_to TEXT,
    client TEXT,
    attachments JSONB DEFAULT '[]',
    reactions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);

-- 4. Ticket attributes table
CREATE TABLE IF NOT EXISTS ticket_attributes (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES tickets(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);

-- 5. Customer attributes table
CREATE TABLE IF NOT EXISTS customer_attributes (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_ticket_id ON messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_ticket_attributes_ticket_id ON ticket_attributes(ticket_id);
CREATE INDEX IF NOT EXISTS idx_customer_attributes_customer_id ON customer_attributes(customer_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_attributes ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
-- These policies allow the service role to perform all operations on the tables

-- Customers table policy
CREATE POLICY "Service role can manage customers" ON customers
    FOR ALL USING (auth.role() = 'service_role');

-- Tickets table policy
CREATE POLICY "Service role can manage tickets" ON tickets
    FOR ALL USING (auth.role() = 'service_role');

-- Messages table policy
CREATE POLICY "Service role can manage messages" ON messages
    FOR ALL USING (auth.role() = 'service_role');

-- Ticket attributes table policy
CREATE POLICY "Service role can manage ticket_attributes" ON ticket_attributes
    FOR ALL USING (auth.role() = 'service_role');

-- Customer attributes table policy
CREATE POLICY "Service role can manage customer_attributes" ON customer_attributes
    FOR ALL USING (auth.role() = 'service_role');

-- Add comments for documentation
COMMENT ON TABLE customers IS 'Customer profiles and metadata from Mava API';
COMMENT ON TABLE tickets IS 'Support tickets from Mava API';
COMMENT ON TABLE messages IS 'Individual messages within tickets';
COMMENT ON TABLE ticket_attributes IS 'Custom attributes for tickets';
COMMENT ON TABLE customer_attributes IS 'Custom attributes for customers'; 