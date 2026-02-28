-- ============================================================
-- Call Center Database Schema
-- Run once: psql -U postgres -d callcenter -f schema.sql
-- ============================================================

-- Customers table: stores all customer account info
CREATE TABLE IF NOT EXISTS customers (
    id           SERIAL PRIMARY KEY,
    phone        VARCHAR(20)  UNIQUE NOT NULL,
    name         VARCHAR(100),
    email        VARCHAR(100),
    account_type VARCHAR(50)  DEFAULT 'standard',
    balance      NUMERIC(10,2) DEFAULT 0,
    status       VARCHAR(30)  DEFAULT 'active',
    created_at   TIMESTAMP    DEFAULT NOW()
);

-- Conversations table: stores every message per caller (memory across calls)
CREATE TABLE IF NOT EXISTS conversations (
    id         SERIAL PRIMARY KEY,
    phone      VARCHAR(20) NOT NULL,
    role       VARCHAR(20) NOT NULL,   -- 'user' or 'assistant'
    content    TEXT        NOT NULL,
    created_at TIMESTAMP   DEFAULT NOW()
);

-- Tickets table: support issues raised by customers
CREATE TABLE IF NOT EXISTS tickets (
    id         SERIAL PRIMARY KEY,
    phone      VARCHAR(20),
    issue      TEXT,
    priority   VARCHAR(20) DEFAULT 'medium',   -- low / medium / high
    status     VARCHAR(20) DEFAULT 'open',     -- open / in-progress / closed
    created_at TIMESTAMP   DEFAULT NOW()
);

-- ── Sample data ──────────────────────────────────────────────
INSERT INTO customers (phone, name, email, account_type, balance, status)
VALUES
  ('+1234567890', 'Alice Johnson', 'alice@email.com', 'premium',  250.00, 'active'),
  ('+0987654321', 'Bob Smith',     'bob@email.com',   'standard',   0.00, 'suspended'),
  ('+1122334455', 'Sara Lee',      'sara@email.com',  'standard',  75.00, 'active')
ON CONFLICT DO NOTHING;
