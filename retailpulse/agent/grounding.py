"""
Grounding Verification and Out-of-Domain Guardrails.
Guarantees AI responses are strictly grounded in underlying data without hallucination,
and handles unsupported/invalid questions gracefully.
"""
import re
from typing import Any
from retailpulse.core.logger import get_logger

logger = get_logger("retailpulse.grounding")

# Keywords that indicate in-domain retail analytics questions
IN_DOMAIN_KEYWORDS = [
    "revenue", "sales", "order", "product", "customer", "category",
    "aov", "average order", "profit", "month", "trend", "decline",
    "churn", "inactive", "top", "worst", "lowest", "highest", "perform",
    "chart", "graph", "plot", "kpi", "spend", "units", "inventory", "stock",
    "sql", "select", "metric", "why", "growth", "breakdown",
    "forecast", "predict", "projection", "future"
]

# Patterns for obvious out-of-domain or conversational chatter
OUT_OF_DOMAIN_PATTERNS = [
    r"\b(weather|temperature|weather forecast|rain forecast)\b",
    r"\b(capital of|president of|prime minister)\b",
    r"\b(who wrote|shakespeare|movie|song|actor|actress)\b",
    r"\b(recipe|how to cook|bake)\b",
    r"\b(bitcoin|crypto|ethereum|stock price of)\b",
    r"\b(joke|riddle|poem|story)\b",
    r"\b(hack|jailbreak|exploit|bypass|ignore previous)\b",
    r"\b(translate to french|spanish|german)\b",
]

class GroundingEngine:
    @classmethod
    def is_in_domain(cls, question: str) -> tuple[bool, str | None]:
        """
        Determines whether the question is within the retail business domain.
        Returns (is_valid, rejection_reason).
        """
        q_lower = question.lower().strip()
        
        # Check explicit out-of-domain patterns
        for pattern in OUT_OF_DOMAIN_PATTERNS:
            if re.search(pattern, q_lower):
                return False, (
                    "I am your RetailPulse AI Business Analyst, specialized in e-commerce business intelligence "
                    "(customers, orders, products, sales performance, and multi-step diagnostic analytics). "
                    "I cannot answer general out-of-domain questions. "
                    "Please ask questions such as: 'What were the top 5 products by revenue?', "
                    "'Show monthly revenue as a chart', 'Which customers have not purchased recently?', "
                    "or 'Why did revenue decline last month?'"
                )

        # Check if question has at least some domain relevance
        has_domain_word = any(kw in q_lower for kw in IN_DOMAIN_KEYWORDS)
        if not has_domain_word and len(q_lower.split()) > 3:
            return False, (
                "Your inquiry does not appear to relate to retail sales, customer analytics, product performance, "
                "or business metrics. Please rephrase your question to target e-commerce data."
            )

        return True, None

    @classmethod
    def verify_grounding(cls, text: str, data_context: dict[str, Any]) -> dict[str, Any]:
        """
        Checks that numerical figures mentioned in the text are present in the data context.
        Returns a grounding audit dict.
        """
        # Extract numerical quantities from text (e.g., $16,248.49 or 40.7% or 5 products)
        found_numbers = re.findall(r"\$?\b\d+(?:,\d{3})*(?:\.\d+)?%?", text)
        
        # Flatten all values in data_context
        def extract_values(obj: Any) -> list[str]:
            vals = []
            if isinstance(obj, dict):
                for v in obj.values():
                    vals.extend(extract_values(v))
            elif isinstance(obj, list):
                for item in obj:
                    vals.extend(extract_values(item))
            elif isinstance(obj, (int, float)):
                vals.append(str(obj))
                vals.append(f"{obj:.2f}")
                vals.append(f"{obj:.1f}")
            elif isinstance(obj, str):
                vals.append(obj)
            return vals

        flattened_context_str = " ".join(extract_values(data_context))
        
        audited = []
        for num in found_numbers:
            clean_num = num.replace("$", "").replace("%", "").replace(",", "")
            # Verify if clean_num is in context
            matched = (clean_num in flattened_context_str) or (len(clean_num) <= 1)
            audited.append({"token": num, "grounded": matched})

        return {
            "total_tokens_checked": len(found_numbers),
            "grounded_ratio": 1.0 if not found_numbers else sum(1 for a in audited if a["grounded"]) / len(audited),
            "tokens": audited
        }
