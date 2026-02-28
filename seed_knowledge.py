"""
seed_knowledge.py — One-time script to load FAQs into the vector knowledge base.

Run this BEFORE starting the app:
  python seed_knowledge.py

Add as many FAQs, policies, or product docs as you need.
The more you add, the smarter the agent becomes at answering questions.
"""

from knowledge_base import add_documents

faqs = [
    {
        "id": "1",
        "text": "To reset your password, go to the login page and click 'Forgot Password'. "
                "You will receive an email with reset instructions within 5 minutes. "
                "If you don't receive it, check your spam folder.",
        "metadata": {"category": "account"}
    },
    {
        "id": "2",
        "text": "Billing cycles run on the 1st of each month. "
                "Late payments incur a 5% fee after a 10-day grace period. "
                "You can pay via credit card, bank transfer, or PayPal.",
        "metadata": {"category": "billing"}
    },
    {
        "id": "3",
        "text": "To cancel your subscription, call support or visit account settings. "
                "Cancellations take effect at the end of the current billing period. "
                "You will not be charged again after cancellation.",
        "metadata": {"category": "subscription"}
    },
    {
        "id": "4",
        "text": "Premium accounts include priority support, unlimited usage, and access to "
                "advanced features. Premium costs $29.99/month and can be upgraded from account settings.",
        "metadata": {"category": "plans"}
    },
    {
        "id": "5",
        "text": "Suspended accounts are caused by missed payments or policy violations. "
                "To reactivate a suspended account due to missed payment, pay the outstanding balance "
                "and contact support. Reactivation takes up to 24 hours.",
        "metadata": {"category": "account"}
    },
    {
        "id": "6",
        "text": "Refunds are available within 30 days of purchase for unused services. "
                "Contact support with your order ID and reason for refund. "
                "Refunds are processed within 5-7 business days.",
        "metadata": {"category": "billing"}
    },
    {
        "id": "7",
        "text": "Technical support is available 24/7 via phone. "
                "Billing support hours are Monday to Friday, 9am to 6pm EST. "
                "For urgent issues, use the priority support line.",
        "metadata": {"category": "support"}
    },
    {
        "id": "8",
        "text": "To update your account details such as email, address, or payment method, "
                "log into your account and go to Settings > Profile. "
                "Changes take effect immediately.",
        "metadata": {"category": "account"}
    },
    {
        "id": "9",
        "text": "If you are experiencing connection issues, first try restarting your device. "
                "Clear your browser cache and cookies. "
                "If the issue persists, contact technical support with your account ID.",
        "metadata": {"category": "technical"}
    },
    {
        "id": "10",
        "text": "Data is backed up daily and stored securely with 256-bit encryption. "
                "We comply with GDPR and CCPA regulations. "
                "You can request a copy of your data at any time from account settings.",
        "metadata": {"category": "privacy"}
    },
]

if __name__ == "__main__":
    add_documents(faqs)
    print("✅ Knowledge base seeded successfully with", len(faqs), "FAQ entries.")
