import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# Load environment variables
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# Groq LLM Client
# ============================================================

class GroqLLMClient:
    """
    Groq-based LLM client.

    Provides:
        - call()      -> compatible with the existing application
        - generate()  -> direct prompt-based generation
        - LLM tracing
        - token tracking
        - configurable cost estimation
    """

    def __init__(self):

        # ----------------------------------------------------
        # API Key
        # ----------------------------------------------------

        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please add GROQ_API_KEY to your .env file."
            )

        # ----------------------------------------------------
        # Model configuration
        # ----------------------------------------------------

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        self.reasoning_effort = os.getenv(
            "GROQ_REASONING_EFFORT",
            "medium"
        )

        # ----------------------------------------------------
        # Cost configuration
        #
        # Keep these configurable instead of hardcoding
        # pricing because provider pricing can change.
        # ----------------------------------------------------

        self.input_cost_per_1m = float(
            os.getenv(
                "GROQ_INPUT_COST_PER_1M",
                "0"
            )
        )

        self.output_cost_per_1m = float(
            os.getenv(
                "GROQ_OUTPUT_COST_PER_1M",
                "0"
            )
        )

        self.production_cost_ceiling = float(
            os.getenv(
                "PRODUCTION_COST_CEILING_USD_PER_DAY",
                "10"
            )
        )

        # ----------------------------------------------------
        # Groq client
        # ----------------------------------------------------

        self.client = Groq(
            api_key=self.api_key
        )

        # ----------------------------------------------------
        # Trace directory
        # ----------------------------------------------------

        self.trace_dir = PROJECT_ROOT / "traces"

        self.trace_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.trace_file = (
            self.trace_dir / "llm_calls.jsonl"
        )


    # ========================================================
    # Existing application-compatible method
    # ========================================================

    def call(
        self,
        system,
        user,
        decision="unknown"
    ):
        """
        Compatibility method used by account_intel.py.

        Existing application code can continue using:

            client.call(system, user, decision)

        """

        return self.generate(
            system=system,
            prompt=user,
            prompt_version=decision
        )


    # ========================================================
    # Main generation method
    # ========================================================

    def generate(
        self,
        prompt,
        prompt_version="unknown",
        system=None
    ):
        """
        Send a request to Groq and return the generated text.
        """

        # ----------------------------------------------------
        # Build messages
        # ----------------------------------------------------

        messages = []

        if system:
            messages.append(
                {
                    "role": "system",
                    "content": system
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        # ----------------------------------------------------
        # Start latency timer
        # ----------------------------------------------------

        start_time = time.perf_counter()

        response = None
        error_message = None

        try:

            # ------------------------------------------------
            # Groq API call
            # ------------------------------------------------

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_completion_tokens=2048,
                top_p=1,
                reasoning_effort=self.reasoning_effort,
                stream=False
            )

            # ------------------------------------------------
            # Calculate latency
            # ------------------------------------------------

            latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2
            )

            # ------------------------------------------------
            # Extract response text
            # ------------------------------------------------

            content = ""

            if response.choices:

                message = response.choices[0].message

                if message:
                    content = message.content or ""

            # ------------------------------------------------
            # Extract token usage
            # ------------------------------------------------

            input_tokens = 0
            output_tokens = 0
            total_tokens = 0

            if getattr(response, "usage", None):

                input_tokens = getattr(
                    response.usage,
                    "prompt_tokens",
                    0
                ) or 0

                output_tokens = getattr(
                    response.usage,
                    "completion_tokens",
                    0
                ) or 0

                total_tokens = getattr(
                    response.usage,
                    "total_tokens",
                    0
                ) or 0

            # ------------------------------------------------
            # Estimate cost
            # ------------------------------------------------

            estimated_cost = self.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            # ------------------------------------------------
            # Trace successful request
            # ------------------------------------------------

            self.write_trace(
                prompt=prompt,
                system=system,
                response=content,
                prompt_version=prompt_version,
                decision=prompt_version,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost,
                status="success"
            )

            return content

        except Exception as exc:

            # ------------------------------------------------
            # Calculate latency even when request fails
            # ------------------------------------------------

            latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2
            )

            error_message = str(exc)

            # ------------------------------------------------
            # Trace failed request
            # ------------------------------------------------

            self.write_trace(
                prompt=prompt,
                system=system,
                response="",
                prompt_version=prompt_version,
                decision=prompt_version,
                latency_ms=latency_ms,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                estimated_cost_usd=0,
                status="error",
                error=error_message
            )

            raise


    # ========================================================
    # Cost calculation
    # ========================================================

    def calculate_cost(
        self,
        input_tokens,
        output_tokens
    ):
        """
        Calculate estimated LLM cost.

        Formula:

        input_tokens / 1,000,000 * input_price
        +
        output_tokens / 1,000,000 * output_price
        """

        input_cost = (
            input_tokens / 1_000_000
        ) * self.input_cost_per_1m

        output_cost = (
            output_tokens / 1_000_000
        ) * self.output_cost_per_1m

        total_cost = input_cost + output_cost

        return round(
            total_cost,
            8
        )


    # ========================================================
    # Trace writer
    # ========================================================

    def write_trace(
        self,
        prompt,
        system,
        response,
        prompt_version,
        decision,
        latency_ms,
        input_tokens,
        output_tokens,
        total_tokens,
        estimated_cost_usd,
        status,
        error=None
    ):
        """
        Store every LLM call as JSONL.

        This satisfies the take-home requirement for:
            - request
            - response
            - model
            - prompt version
            - latency
            - tokens
            - cost
            - decision
        """

        trace_record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "provider": "groq",

            "model": self.model,

            "prompt_version": prompt_version,

            "decision": decision,

            "latency_ms": latency_ms,

            "input_tokens": input_tokens,

            "output_tokens": output_tokens,

            "total_tokens": total_tokens,

            "estimated_cost_usd": estimated_cost_usd,

            "cost_estimation_method": (
                "input_tokens/1M * GROQ_INPUT_COST_PER_1M "
                "+ output_tokens/1M * GROQ_OUTPUT_COST_PER_1M"
            ),

            "status": status,

            "request": {
                "system": system,
                "user": prompt
            },

            "response": response
        }

        if error:
            trace_record["error"] = error

        # ----------------------------------------------------
        # Write one JSON object per line
        # ----------------------------------------------------

        with open(
            self.trace_file,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(
                    trace_record,
                    ensure_ascii=False
                )
                + "\n"
            )


# ============================================================
# Backward compatibility
# ============================================================
#
# account_intel.py currently imports:
#
#     from app.llm.client import LLMClient
#
# Therefore keep this alias.
#
# LLMClient actually uses GroqLLMClient.
# ============================================================

LLMClient = GroqLLMClient