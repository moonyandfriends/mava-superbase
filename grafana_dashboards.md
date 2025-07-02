# Grafana Dashboards for Mava Support Analytics

This document provides SQL queries and dashboard configurations for visualizing Mava support ticket data in Grafana.

## Database Connection Setup

### Supabase PostgreSQL Connection
- **Host**: `nhahlrzbvsjrajizjgfg.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **Username**: `postgres`
- **Password**: Use your Supabase service key
- **SSL Mode**: `require`

## Dashboard 1: Support Ticket Overview

### Panel 1: Total Tickets by Status
```sql
SELECT 
  status,
  COUNT(*) as ticket_count
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY status
ORDER BY ticket_count DESC;
```

### Panel 2: Tickets Created Over Time (Last 30 Days)
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as tickets_created
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Panel 3: Priority Distribution
```sql
SELECT 
  priority,
  COUNT(*) as count
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY priority
ORDER BY 
  CASE priority
    WHEN 'HIGH' THEN 1
    WHEN 'MEDIUM' THEN 2
    WHEN 'LOW' THEN 3
    ELSE 4
  END;
```

### Panel 4: Response Time Metrics
```sql
SELECT 
  AVG(EXTRACT(EPOCH FROM (first_agent_message_created_at - first_customer_message_created_at))/3600) as avg_response_hours,
  MIN(EXTRACT(EPOCH FROM (first_agent_message_created_at - first_customer_message_created_at))/3600) as min_response_hours,
  MAX(EXTRACT(EPOCH FROM (first_agent_message_created_at - first_customer_message_created_at))/3600) as max_response_hours
FROM tickets 
WHERE first_agent_message_created_at IS NOT NULL 
  AND first_customer_message_created_at IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days';
```

## Dashboard 2: Customer Analytics

### Panel 1: Top Customers by Ticket Volume
```sql
SELECT 
  c.name,
  c.discord_author_id,
  COUNT(t.id) as ticket_count
FROM customers c
JOIN tickets t ON c.id = t.customer_id
WHERE t.created_at >= NOW() - INTERVAL '30 days'
GROUP BY c.id, c.name, c.discord_author_id
ORDER BY ticket_count DESC
LIMIT 10;
```

### Panel 2: Customer Satisfaction (if ratings exist)
```sql
SELECT 
  AVG(CAST(attr.content AS FLOAT)) as avg_rating
FROM customer_attributes attr
JOIN customers c ON attr.customer_id = c.id
WHERE attr.attribute = 'rating' 
  AND attr.content ~ '^[0-9]+(\.[0-9]+)?$'
  AND c.updated_at >= NOW() - INTERVAL '30 days';
```

### Panel 3: Customer Activity Heatmap
```sql
SELECT 
  EXTRACT(DOW FROM t.created_at) as day_of_week,
  EXTRACT(HOUR FROM t.created_at) as hour_of_day,
  COUNT(*) as ticket_count
FROM tickets t
WHERE t.created_at >= NOW() - INTERVAL '30 days'
GROUP BY day_of_week, hour_of_day
ORDER BY day_of_week, hour_of_day;
```

## Dashboard 3: Agent Performance

### Panel 1: Tickets Assigned by Agent
```sql
SELECT 
  assigned_to,
  COUNT(*) as assigned_tickets,
  COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_tickets
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND assigned_to IS NOT NULL
GROUP BY assigned_to
ORDER BY assigned_tickets DESC;
```

### Panel 2: Agent Response Times
```sql
SELECT 
  assigned_to,
  AVG(EXTRACT(EPOCH FROM (first_agent_message_created_at - first_customer_message_created_at))/3600) as avg_response_hours
FROM tickets 
WHERE assigned_to IS NOT NULL
  AND first_agent_message_created_at IS NOT NULL
  AND first_customer_message_created_at IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY assigned_to
ORDER BY avg_response_hours;
```

### Panel 3: Agent Workload Over Time
```sql
SELECT 
  DATE(created_at) as date,
  assigned_to,
  COUNT(*) as tickets_assigned
FROM tickets 
WHERE assigned_to IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), assigned_to
ORDER BY date, assigned_to;
```

## Dashboard 4: Message Analytics

### Panel 1: Message Volume Over Time
```sql
SELECT 
  DATE(m.created_at) as date,
  COUNT(*) as message_count
FROM messages m
WHERE m.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(m.created_at)
ORDER BY date;
```

### Panel 2: Customer vs Agent Messages
```sql
SELECT 
  DATE(m.created_at) as date,
  SUM(CASE WHEN m.from_customer = true THEN 1 ELSE 0 END) as customer_messages,
  SUM(CASE WHEN m.from_customer = false THEN 1 ELSE 0 END) as agent_messages
FROM messages m
WHERE m.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(m.created_at)
ORDER BY date;
```

### Panel 3: Average Messages per Ticket
```sql
SELECT 
  AVG(message_count) as avg_messages_per_ticket
FROM (
  SELECT 
    ticket_id,
    COUNT(*) as message_count
  FROM messages
  WHERE created_at >= NOW() - INTERVAL '30 days'
  GROUP BY ticket_id
) as ticket_messages;
```

## Dashboard 5: Category and Source Analysis

### Panel 1: Tickets by Category
```sql
SELECT 
  category,
  COUNT(*) as ticket_count
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND category IS NOT NULL
GROUP BY category
ORDER BY ticket_count DESC;
```

### Panel 2: Tickets by Source Type
```sql
SELECT 
  source_type,
  COUNT(*) as ticket_count
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY source_type
ORDER BY ticket_count DESC;
```

### Panel 3: Discord Thread Analysis
```sql
SELECT 
  COUNT(*) as total_discord_tickets,
  COUNT(CASE WHEN is_discord_thread_deleted = true THEN 1 END) as deleted_threads,
  COUNT(CASE WHEN is_discord_thread_deleted = false THEN 1 END) as active_threads
FROM tickets 
WHERE source_type = 'DISCORD'
  AND created_at >= NOW() - INTERVAL '30 days';
```

## Dashboard 6: Real-time Monitoring

### Panel 1: Open Tickets by Priority
```sql
SELECT 
  priority,
  COUNT(*) as open_tickets
FROM tickets 
WHERE status != 'CLOSED'
GROUP BY priority
ORDER BY 
  CASE priority
    WHEN 'HIGH' THEN 1
    WHEN 'MEDIUM' THEN 2
    WHEN 'LOW' THEN 3
    ELSE 4
  END;
```

### Panel 2: Recent Activity (Last 24 Hours)
```sql
SELECT 
  'New Tickets' as activity_type,
  COUNT(*) as count
FROM tickets 
WHERE created_at >= NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
  'New Messages' as activity_type,
  COUNT(*) as count
FROM messages 
WHERE created_at >= NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
  'Closed Tickets' as activity_type,
  COUNT(*) as count
FROM tickets 
WHERE updated_at >= NOW() - INTERVAL '24 hours'
  AND status = 'CLOSED';
```

### Panel 3: SLA Breach Risk
```sql
SELECT 
  COUNT(*) as tickets_at_risk
FROM tickets 
WHERE status != 'CLOSED'
  AND created_at <= NOW() - INTERVAL '48 hours'
  AND priority = 'HIGH';
```

## Advanced Analytics Queries

### Customer Lifetime Value
```sql
SELECT 
  c.name,
  COUNT(t.id) as total_tickets,
  AVG(EXTRACT(EPOCH FROM (t.updated_at - t.created_at))/86400) as avg_ticket_duration_days,
  MAX(t.created_at) as last_activity
FROM customers c
JOIN tickets t ON c.id = t.customer_id
GROUP BY c.id, c.name
ORDER BY total_tickets DESC;
```

### Ticket Resolution Time by Category
```sql
SELECT 
  category,
  AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_resolution_hours,
  COUNT(*) as total_tickets
FROM tickets 
WHERE status = 'CLOSED'
  AND category IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY category
ORDER BY avg_resolution_hours;
```

### Agent Efficiency Metrics
```sql
SELECT 
  assigned_to,
  COUNT(*) as total_assigned,
  COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as resolved,
  ROUND(
    COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) * 100.0 / COUNT(*), 2
  ) as resolution_rate,
  AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_resolution_hours
FROM tickets 
WHERE assigned_to IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY assigned_to
ORDER BY resolution_rate DESC;
```

## Grafana Dashboard Configuration Tips

### Variables to Add
1. **Time Range**: `$__timeFilter(created_at)`
2. **Agent Filter**: `assigned_to`
3. **Category Filter**: `category`
4. **Priority Filter**: `priority`

### Panel Settings
- **Refresh**: 5m for real-time dashboards, 1h for historical
- **Time Range**: Last 24 hours for real-time, Last 30 days for trends
- **Visualization Types**:
  - Bar charts for distributions
  - Line charts for time series
  - Heatmaps for activity patterns
  - Stat panels for KPIs
  - Tables for detailed data

### Alerting Rules
1. **High Priority Tickets**: Alert when >5 high priority tickets are open
2. **Response Time**: Alert when average response time >4 hours
3. **SLA Breach**: Alert when tickets older than 48 hours are still open
4. **Agent Overload**: Alert when any agent has >10 assigned tickets

## Setup Instructions

1. **Add Supabase as a PostgreSQL data source in Grafana**
2. **Import these queries as new panels**
3. **Create dashboards using the panel configurations above**
4. **Set up alerts based on the suggested thresholds**
5. **Configure refresh intervals based on your needs**

This setup will give you comprehensive visibility into your Mava support operations, customer satisfaction, agent performance, and operational efficiency. 