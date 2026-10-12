import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# Project root
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))


# ============================================================
# Application imports
# ============================================================

from app.scoring.scorer import account_context
from app.llm.account_intel import explain, outreach


# ============================================================
# Streamlit configuration
# ============================================================

st.set_page_config(
    page_title="CyberSignal AI",
    layout="wide"
)

st.title("CyberSignal AI")

st.caption(
    "AI Sales Intelligence for cybersecurity prospecting"
)


# ============================================================
# Load scored account data
# ============================================================

data = ROOT / "data" / "accounts_scored.parquet"

if not data.exists():
    st.error(
        "Scored account data not found. Run:\n\n"
        "python scripts/ingest_pyspark.py\n"
        "python scripts/build_accounts_spark.py\n"
        "python scripts/build_scores.py"
    )
    st.stop()


df = pd.read_parquet(data)


# ============================================================
# Top-level metrics
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Accounts",
    len(df)
)

c2.metric(
    "High priority",
    int((df.priority == "High").sum())
)

c3.metric(
    "Medium priority",
    int((df.priority == "Medium").sum())
)

c4.metric(
    "Average score",
    round(df.score.mean(), 1)
)


# ============================================================
# Sidebar filters
# ============================================================

st.sidebar.header("Account filters")

priorities = st.sidebar.multiselect(
    "Priority",
    ["High", "Medium", "Low"],
    ["High", "Medium"]
)

min_score = st.sidebar.slider(
    "Minimum score",
    0,
    100,
    0
)

org_search = st.sidebar.text_input(
    "Organization"
)


# ============================================================
# Apply filters
# ============================================================

view = df[
    df.priority.isin(priorities)
    & (df.score >= min_score)
].copy()


if org_search:
    view = view[
        view.org.str.contains(
            org_search,
            case=False,
            na=False
        )
    ]


# ============================================================
# Sort accounts
# ============================================================

view = view.sort_values(
    ["score", "observation_count"],
    ascending=False
)


# ============================================================
# Prioritized accounts table
# ============================================================

st.subheader("Prioritized accounts")

columns = [
    "org",
    "score",
    "priority",
    "observation_count",
    "unique_ips",
    "unique_ports",
    "unique_products",
    "sensitive_port_observations",
    "cloud_observations",
    "iot_observations",
    "source_parts",
    "last_observed_at"
]


st.dataframe(
    view[columns].head(100),
    width="stretch",
    hide_index=True
)


# ============================================================
# Account selection
# ============================================================

if len(view):

    selected = st.selectbox(
        "Select account",
        view.org.tolist()
    )

    row = view[
        view.org == selected
    ].iloc[0]

    account = account_context(row)


    # ========================================================
    # Account header
    # ========================================================

    st.divider()

    st.header(selected)


    a, b, c = st.columns(3)

    a.metric(
        "Cybersecurity Priority Score",
        row.score
    )

    b.metric(
        "Priority",
        row.priority
    )

    c.metric(
        "Source dataset parts",
        row.source_parts
    )


    # ========================================================
    # Observed signals
    # ========================================================

    st.subheader("Observed signals")

    for signal in account["signals"]:
        st.write(
            "•",
            signal
        )


    # ========================================================
    # Infrastructure evidence
    # ========================================================

    st.subheader("Infrastructure evidence")

    st.json(account)


    # ========================================================
    # AI Account Brief
    # ========================================================

    if st.button(
        "Generate AI account brief",
        width="stretch"
    ):

        with st.spinner(
            "Generating AI account brief..."
        ):

            result = explain(
                account,
                os.getenv(
                    "PROMPT_VERSION",
                    "v2"
                )
            )


        # ----------------------------------------------------
        # Handle both response formats:
        #
        # 1. String:
        #    "This company has..."
        #
        # 2. Dictionary:
        #    {
        #       "text": "...",
        #       "model": "...",
        #       ...
        #    }
        # ----------------------------------------------------

        if isinstance(result, dict):

            st.write(
                result.get(
                    "text",
                    ""
                )
            )

            if result.get("enabled"):

                model = result.get(
                    "model",
                    "Groq"
                )

                prompt_version = result.get(
                    "prompt_version",
                    "unknown"
                )

                latency = result.get(
                    "latency_ms",
                    0
                )

                cost = result.get(
                    "estimated_cost_usd",
                    0
                )

                st.caption(
                    f"{model} | "
                    f"{prompt_version} | "
                    f"{latency} ms | "
                    f"${cost:.6f}"
                )

        else:

            # Groq client currently returns a string
            st.write(result)


    # ========================================================
    # AI Outreach
    # ========================================================

    if st.button(
        "Generate AI outreach",
        width="stretch"
    ):

        with st.spinner(
            "Generating AI outreach..."
        ):

            result = outreach(
                account
            )


        # ----------------------------------------------------
        # Handle dictionary response
        # ----------------------------------------------------

        if isinstance(result, dict):

            st.write(
                result.get(
                    "text",
                    ""
                )
            )

            if result.get("enabled"):

                model = result.get(
                    "model",
                    "Groq"
                )

                prompt_version = result.get(
                    "prompt_version",
                    "unknown"
                )

                latency = result.get(
                    "latency_ms",
                    0
                )

                cost = result.get(
                    "estimated_cost_usd",
                    0
                )

                st.caption(
                    f"{model} | "
                    f"{prompt_version} | "
                    f"{latency} ms | "
                    f"${cost:.6f}"
                )

        else:

            # Groq client currently returns a string
            st.write(result)


# ============================================================
# No accounts found
# ============================================================

else:

    st.warning(
        "No accounts match the selected filters."
    )


# ============================================================
# Guardrail
# ============================================================

st.divider()

st.caption(
    "Guardrail: observed internet exposure does not by itself "
    "establish vulnerability, breach, or compromise."
)