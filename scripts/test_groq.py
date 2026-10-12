
from app.llm.client import GroqLLMClient


def main():

    client = GroqLLMClient()

    response = client.generate(
        prompt="""
You are a cybersecurity sales intelligence assistant.

Explain in 3 bullet points why externally
observable infrastructure can be useful as a
cybersecurity sales signal.

Do not claim that exposure means vulnerability
or compromise.
""",
        system_prompt="""
You are an evidence-grounded B2B cybersecurity
sales intelligence assistant.
""",
        prompt_version="test-v1",
        decision="test_generation",
        max_completion_tokens=500,
    )

    print("\n===== GROQ RESPONSE =====\n")
    print(response)


if __name__ == "__main__":
    main()