"""
tools.py — Defines what actions the Groq AI can take, and executes them.

Two parts:
  1. TOOLS list  → tells Groq what tools exist and what they do
                   Groq reads the "description" fields to decide WHEN to use each tool
  2. execute_tool() → actually runs the tool when Groq calls it
                      bridges AI decisions → real DB/KB actions
"""

import json
from database import get_customer, create_ticket, get_tickets, update_customer_status
from knowledge_base import search


# ─── Tool Definitions (sent to Groq so it knows what tools are available) ────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_info",
            "description": (
                "Retrieve customer account details using their phone number. "
                "Always call this first when a caller asks about their account, "
                "balance, status, or anything account-specific."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number in E.164 format e.g. +1234567890"
                    }
                },
                "required": ["phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the FAQ and policy knowledge base to answer customer questions. "
                "Use this for questions about billing, subscriptions, technical issues, "
                "refunds, passwords, privacy, or any general how-to question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's question or topic to search for"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": (
                "Create a support ticket when the customer has an unresolved issue "
                "that needs follow-up, escalation, or human agent involvement. "
                "Always confirm with the customer before creating."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    },
                    "issue": {
                        "type": "string",
                        "description": "Clear description of the customer's issue"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level: high for urgent/service outages, low for general queries"
                    }
                },
                "required": ["phone", "issue", "priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_tickets",
            "description": (
                "Retrieve all past support tickets for a customer. "
                "Use this when customer asks about an existing ticket or previous issues."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    }
                },
                "required": ["phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_account_status",
            "description": (
                "Update a customer's account status. "
                "Use 'active' to reactivate, 'suspended' if requested by authorized staff, "
                "'cancelled' for account closure requests."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "suspended", "cancelled"],
                        "description": "New account status"
                    }
                },
                "required": ["phone", "status"]
            }
        }
    }
]


# ─── Tool Executor (runs the tool and returns result to Groq) ─────────────────

def execute_tool(name: str, arguments: str) -> str:
    """
    Called by groq_agent.py when Groq decides to use a tool.

    Groq returns: tool name + JSON arguments string
    This function: parses args → calls the right DB/KB function → returns result as string

    The result is fed back into the conversation so Groq can use it in its answer.
    """
    args = json.loads(arguments)

    if name == "get_customer_info":
        result = get_customer(args["phone"])
        if result:
            return json.dumps(result, default=str)  # default=str handles datetime objects
        return "Customer not found in database."

    elif name == "search_knowledge_base":
        return search(args["query"])

    elif name == "create_support_ticket":
        ticket_id = create_ticket(args["phone"], args["issue"], args["priority"])
        return f"Support ticket created successfully. Ticket ID: {ticket_id}. The customer will be contacted within 24 hours."

    elif name == "get_customer_tickets":
        tickets = get_tickets(args["phone"])
        if tickets:
            return json.dumps(tickets, default=str)
        return "No previous support tickets found for this customer."

    elif name == "update_account_status":
        result = update_customer_status(args["phone"], args["status"])
        if result:
            return f"Account status successfully updated to '{args['status']}' for {result.get('name', 'customer')}."
        return "Customer not found. Could not update account status."

    return f"Unknown tool '{name}'. No action taken."
