-- Mava-Supabase Database Schema
-- This file contains all the SQL needed to set up the database for the Mava sync service

-- Enable UUID extension for better ID handling
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main tickets table
CREATE TABLE mava_tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT,
    client TEXT,
    status TEXT,
    priority TEXT,
    source_type TEXT,
    category TEXT,
    assigned_to TEXT,
    discord_thread_id TEXT,
    interaction_identifier TEXT,
    is_discord_thread_deleted BOOLEAN DEFAULT FALSE,
    discord_users JSONB DEFAULT '[]'::jsonb,
    ai_status TEXT,
    is_ai_enabled_in_flow_root BOOLEAN DEFAULT FALSE,
    is_button_in_flow_root_clicked BOOLEAN DEFAULT FALSE,
    force_button_selection BOOLEAN DEFAULT FALSE,
    is_user_rating_requested BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    mentions JSONB DEFAULT '[]'::jsonb,
    first_customer_message_created_at TIMESTAMP WITH TIME ZONE,
    first_agent_message_created_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 0,
    disabled BOOLEAN DEFAULT FALSE,
    raw_data JSONB
);

-- Customers table
CREATE TABLE mava_customers (
    id TEXT PRIMARY KEY,
    discord_author_id TEXT,
    client TEXT,
    name TEXT,
    avatar_url TEXT,
    discord_joined_at TIMESTAMP WITH TIME ZONE,
    wallet_address TEXT,
    discord_roles JSONB DEFAULT '[]'::jsonb,
    custom_fields JSONB DEFAULT '[]'::jsonb,
    notes JSONB DEFAULT '[]'::jsonb,
    user_ratings JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 0,
    raw_data JSONB
);

-- Messages table
CREATE TABLE mava_messages (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES mava_tickets(id) ON DELETE CASCADE,
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
    read_by JSONB DEFAULT '[]'::jsonb,
    mentions JSONB DEFAULT '[]'::jsonb,
    pre_submission_identifier TEXT,
    foreign_identifier TEXT,
    action_log_from TEXT,
    action_log_to TEXT,
    replied_to TEXT,
    client TEXT,
    attachments JSONB DEFAULT '[]'::jsonb,
    reactions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 0,
    raw_data JSONB
);

-- Ticket attributes table
CREATE TABLE mava_ticket_attributes (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES mava_tickets(id) ON DELETE CASCADE,
    attribute TEXT NOT NULL,
    content TEXT,
    raw_data JSONB
);

-- Customer attributes table
CREATE TABLE mava_customer_attributes (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES mava_customers(id) ON DELETE CASCADE,
    attribute TEXT NOT NULL,
    content TEXT,
    raw_data JSONB
);

-- Team members table
CREATE TABLE mava_team_members (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    type TEXT,
    client TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    is_custom_signature_enabled BOOLEAN DEFAULT FALSE,
    is_sound_notification_enabled BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    avatar TEXT,
    custom_signature TEXT,
    user_ratings JSONB DEFAULT '[]'::jsonb,
    pinned_attributes JSONB DEFAULT '[]'::jsonb,
    filter_configurations JSONB DEFAULT '[]'::jsonb,
    master_notifications JSONB DEFAULT '{}'::jsonb,
    device_token JSONB DEFAULT '[]'::jsonb,
    notifications JSONB DEFAULT '[]'::jsonb,
    two_factor_auth JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 0,
    raw_data JSONB
);

-- Clients/Organizations table
CREATE TABLE mava_clients (
    id TEXT PRIMARY KEY,
    name TEXT,
    creator TEXT,
    contracts JSONB DEFAULT '[]'::jsonb,
    origin JSONB DEFAULT '[]'::jsonb,
    members JSONB DEFAULT '[]'::jsonb,
    categories JSONB DEFAULT '[]'::jsonb,
    is_ai_enabled BOOLEAN DEFAULT FALSE,
    use_template_answers BOOLEAN DEFAULT FALSE,
    is_csat_enabled BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]'::jsonb,
    hooks JSONB DEFAULT '[]'::jsonb,
    user_ratings JSONB DEFAULT '[]'::jsonb,
    onboarding JSONB DEFAULT '{}'::jsonb,
    template_answers JSONB DEFAULT '[]'::jsonb,
    is_reopening_tickets_enabled BOOLEAN DEFAULT FALSE,
    stripe_customer_id TEXT,
    token TEXT,
    flow_root TEXT,
    archived_flows JSONB DEFAULT '[]'::jsonb,
    ai_settings TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 0,
    raw_data JSONB
);

-- Create indexes for better query performance
CREATE INDEX idx_mava_tickets_customer_id ON mava_tickets(customer_id);
CREATE INDEX idx_mava_tickets_status ON mava_tickets(status);
CREATE INDEX idx_mava_tickets_created_at ON mava_tickets(created_at);
CREATE INDEX idx_mava_tickets_updated_at ON mava_tickets(updated_at);
CREATE INDEX idx_mava_tickets_discord_thread_id ON mava_tickets(discord_thread_id);
CREATE INDEX idx_mava_tickets_client ON mava_tickets(client);

CREATE INDEX idx_mava_customers_discord_author_id ON mava_customers(discord_author_id);
CREATE INDEX idx_mava_customers_client ON mava_customers(client);
CREATE INDEX idx_mava_customers_created_at ON mava_customers(created_at);

CREATE INDEX idx_mava_messages_ticket_id ON mava_messages(ticket_id);
CREATE INDEX idx_mava_messages_created_at ON mava_messages(created_at);
CREATE INDEX idx_mava_messages_from_customer ON mava_messages(from_customer);
CREATE INDEX idx_mava_messages_sender ON mava_messages(sender);

CREATE INDEX idx_mava_ticket_attributes_ticket_id ON mava_ticket_attributes(ticket_id);
CREATE INDEX idx_mava_ticket_attributes_attribute ON mava_ticket_attributes(attribute);

CREATE INDEX idx_mava_customer_attributes_customer_id ON mava_customer_attributes(customer_id);
CREATE INDEX idx_mava_customer_attributes_attribute ON mava_customer_attributes(attribute);

CREATE INDEX idx_mava_team_members_email ON mava_team_members(email);
CREATE INDEX idx_mava_team_members_type ON mava_team_members(type);
CREATE INDEX idx_mava_team_members_client ON mava_team_members(client);
CREATE INDEX idx_mava_team_members_is_archived ON mava_team_members(is_archived);
CREATE INDEX idx_mava_team_members_created_at ON mava_team_members(created_at);
CREATE INDEX idx_mava_team_members_updated_at ON mava_team_members(updated_at);

CREATE INDEX idx_mava_clients_name ON mava_clients(name);
CREATE INDEX idx_mava_clients_creator ON mava_clients(creator);
CREATE INDEX idx_mava_clients_created_at ON mava_clients(created_at);
CREATE INDEX idx_mava_clients_updated_at ON mava_clients(updated_at);

-- Enable Row Level Security on all tables
ALTER TABLE mava_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_ticket_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_customer_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_clients ENABLE ROW LEVEL SECURITY;

-- Create policies for service role (allows the sync service to manage all data)
CREATE POLICY "Service role can manage mava_tickets" ON mava_tickets
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_customers" ON mava_customers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_messages" ON mava_messages
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_ticket_attributes" ON mava_ticket_attributes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_customer_attributes" ON mava_customer_attributes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_team_members" ON mava_team_members
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage mava_clients" ON mava_clients
    FOR ALL USING (auth.role() = 'service_role');

-- Create useful views for common queries

-- View for tickets with customer information
CREATE VIEW mava_tickets_with_customers AS
SELECT 
    t.*,
    c.name as customer_name,
    c.discord_author_id,
    c.avatar_url as customer_avatar_url
FROM mava_tickets t
LEFT JOIN mava_customers c ON t.customer_id = c.id;

-- View for tickets with message counts
CREATE VIEW mava_tickets_with_message_counts AS
SELECT 
    t.*,
    COUNT(m.id) as message_count,
    COUNT(CASE WHEN m.from_customer = TRUE THEN 1 END) as customer_message_count,
    COUNT(CASE WHEN m.from_customer = FALSE THEN 1 END) as agent_message_count
FROM mava_tickets t
LEFT JOIN mava_messages m ON t.id = m.ticket_id
GROUP BY t.id, t.customer_id, t.client, t.status, t.priority, t.source_type, 
         t.category, t.assigned_to, t.discord_thread_id, t.interaction_identifier,
         t.is_discord_thread_deleted, t.discord_users, t.ai_status, 
         t.is_ai_enabled_in_flow_root, t.is_button_in_flow_root_clicked,
         t.force_button_selection, t.is_user_rating_requested, t.is_visible,
         t.mentions, t.first_customer_message_created_at, t.first_agent_message_created_at,
         t.tags, t.created_at, t.updated_at, t.version, t.disabled, t.raw_data;

-- View for recent activity (tickets updated in last 7 days)
CREATE VIEW mava_recent_activity AS
SELECT 
    'ticket' as type,
    id,
    status,
    updated_at,
    customer_id
FROM mava_tickets 
WHERE updated_at >= NOW() - INTERVAL '7 days'
UNION ALL
SELECT 
    'message' as type,
    id,
    message_status as status,
    created_at as updated_at,
    ticket_id as customer_id
FROM mava_messages 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY updated_at DESC;

-- View for active team members
CREATE VIEW mava_active_team_members AS
SELECT 
    id,
    name,
    email,
    type,
    client,
    avatar,
    custom_signature,
    created_at,
    updated_at
FROM mava_team_members 
WHERE is_archived = FALSE
ORDER BY name;

-- View for client configuration summary
CREATE VIEW mava_client_summary AS
SELECT 
    id,
    name,
    creator,
    is_ai_enabled,
    use_template_answers,
    is_csat_enabled,
    is_reopening_tickets_enabled,
    array_length(members, 1) as member_count,
    array_length(categories, 1) as category_count,
    array_length(tags, 1) as tag_count,
    array_length(hooks, 1) as hook_count,
    created_at,
    updated_at
FROM mava_clients;

-- Create function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_mava_tickets_updated_at 
    BEFORE UPDATE ON mava_tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mava_customers_updated_at 
    BEFORE UPDATE ON mava_customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mava_messages_updated_at 
    BEFORE UPDATE ON mava_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mava_team_members_updated_at 
    BEFORE UPDATE ON mava_team_members 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mava_clients_updated_at 
    BEFORE UPDATE ON mava_clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE mava_tickets IS 'Main table storing Mava support ticket information';
COMMENT ON TABLE mava_customers IS 'Customer profiles and metadata from Mava';
COMMENT ON TABLE mava_messages IS 'Individual messages within tickets';
COMMENT ON TABLE mava_ticket_attributes IS 'Custom attributes associated with tickets';
COMMENT ON TABLE mava_customer_attributes IS 'Custom attributes associated with customers';

COMMENT ON VIEW mava_tickets_with_customers IS 'Tickets joined with customer information for easy querying';
COMMENT ON VIEW mava_tickets_with_message_counts IS 'Tickets with aggregated message statistics';
COMMENT ON VIEW mava_recent_activity IS 'Recent activity across tickets and messages for dashboard views'; 