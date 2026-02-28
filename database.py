"""
database.py — All PostgreSQL read/write operations.

Functions:
  get_customer()          → look up a customer by phone
  update_customer_status()→ change account status
  get_history()           → load past conversation messages
  save_turn()             → save one round of conversation
  create_ticket()         → open a new support ticket
  get_tickets()           → list all tickets for a customer
"""

import psycopg2
import psycopg2.extras
from config import DATABASE_URL


def get_conn():
    """Open a PostgreSQL connection. Uses RealDictCursor so rows behave like dicts."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ─── Customer ────────────────────────────────────────────────────────────────

def get_customer(phone: str):
    """
    Look up a customer by their phone number.
    Returns a dict like {"name":"Alice","status":"active","balance":250.0,...}
    Returns None if not found.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
            row = cur.fetchone()
            return dict(row) if row else None


def update_customer_status(phone: str, status: str):
    """
    Change a customer's account status (active / suspended / cancelled).
    Returns updated customer dict, or None if not found.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE customers SET status = %s WHERE phone = %s RETURNING *",
                (status, phone)
            )
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None


# ─── Conversation History ────────────────────────────────────────────────────

def get_history(phone: str, limit: int = 10) -> list:
    """
    Fetch the last `limit` messages for this caller.
    Returns a list of {"role": "user"|"assistant", "content": "..."} dicts.
    Used to give Groq memory of the current/past call.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT role, content
                FROM conversations
                WHERE phone = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (phone, limit))
            rows = cur.fetchall()
            # Reverse so oldest message is first (correct order for LLM context)
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def save_turn(phone: str, user_msg: str, assistant_msg: str):
    """
    After each exchange, save both the caller's message and the agent's reply.
    This is the core of cross-call memory — every turn is persisted.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (phone, role, content) VALUES (%s, %s, %s)",
                (phone, "user", user_msg)
            )
            cur.execute(
                "INSERT INTO conversations (phone, role, content) VALUES (%s, %s, %s)",
                (phone, "assistant", assistant_msg)
            )
            conn.commit()


# ─── Tickets ─────────────────────────────────────────────────────────────────

def create_ticket(phone: str, issue: str, priority: str = "medium") -> int:
    """
    Insert a new support ticket. Returns the ticket ID so the agent
    can tell the caller their reference number.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tickets (phone, issue, priority)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (phone, issue, priority))
            conn.commit()
            return cur.fetchone()["id"]


def get_tickets(phone: str) -> list:
    """
    Return all past support tickets for a customer.
    Helps the agent say "I can see you had a billing issue last week."
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM tickets WHERE phone = %s ORDER BY created_at DESC",
                (phone,)
            )
            return [dict(r) for r in cur.fetchall()]
