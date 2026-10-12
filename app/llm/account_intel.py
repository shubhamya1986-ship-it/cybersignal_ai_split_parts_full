from pathlib import Path
from app.llm.client import GroqLLMClient


ROOT=Path(__file__).resolve().parents[2]

def prompt(folder,version):
    return (ROOT/"prompts"/folder/f"{version}.txt").read_text(encoding="utf-8")

def explain(account,version="v2"):
    client = GroqLLMClient()
    system=prompt("account_scoring",version)
    user=f"""Account evidence:
{account}

Return:
- Why this account received its priority
- Strongest observed signals
- What is unknown
- Evidence-grounded why-now
- Relevant security persona as a role hypothesis"""
    return client.call(system,user,"account_explanation")

def outreach(account,version="v1"):
    client = GroqLLMClient()
    system=prompt("outreach",version)
    user=f"""Account evidence:
{account}

Write 80-120 words of B2B outreach.
Use only the supplied evidence.
Include one or two observed signals and a soft CTA."""
    return client.call(system,user,"outreach_draft")
