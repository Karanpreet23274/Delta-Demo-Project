"""The only module that talks to a language model. Two uses: parse a request, word verified evidence.

Provider is chosen by LLM_PROVIDER (anthropic | gemini | ollama) and LLM_MODEL. MOCK_LLM=true (or any model failure) falls back to the
rule parser and the templates, so plans keep working without a model.
"""
import json
import time

from app.agent.intent import Intent, rule_parse
from app.config import env, mock_llm

ROUTER_PROMPT = (
    "You turn a planner's request about allocating manufacturing orders to plants A, B and C into a "
    "typed intent. Do not answer the request. Do not invent values the user did not state; leave them null. "
    "Order ids look like O-077 (\"order 77\" means O-077). A plant that is down, shut or offline loses 100% of "
    "its capacity. 'For two weeks' means duration_weeks=2; 'weeks 2-3' means start_week=2 and duration_weeks=2. "
    "Set use_loaded_events when the user refers to capacity events that were loaded."
)
WRITER_PROMPT = (
    "You write short, plain-English text for operations managers about a production plan. Use ONLY the "
    "figures in the EVIDENCE JSON, written the same way or rounded (1840000 may be written 1,840,000 or "
    "1.84M; carbon_kg/1000 = tonnes). Never compute new figures, never estimate, never add numbers that "
    "are not in the evidence. If the evidence does not contain a figure the user asked for, say it was "
    "not computed. No headings unless asked for a brief."
)


DEFAULT_MODEL = {"anthropic": "claude-sonnet-5-5", "gemini": "gemini-3.8-flash", "ollama": "qwen2.5:7b-instruct"}


def _provider() -> str:
    p = env("LLM_PROVIDER", "anthropic").lower()
    return "gemini" if p in ("google", "gemini") else p


def _model() -> str:
    return env("LLM_MODEL") or DEFAULT_MODEL.get(_provider(), "")


def _client():
    provider, model = _provider(), _model()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = env("GEMINI_API_KEY") or env("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        return ChatGoogleGenerativeAI(model=model, temperature=0, max_output_tokens=1200, google_api_key=key,
                                      timeout=60, max_retries=1)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=0, max_tokens=1200, timeout=60)
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0, base_url=env("OLLAMA_BASE_URL", "http://localhost:11434"))
    raise ValueError(f"Unsupported LLM_PROVIDER {provider}")


def model_name() -> str:
    return "mock (rules and templates)" if mock_llm() else f"{_provider()}:{_model()}"


def health() -> dict:
    if mock_llm():
        return {"status": "mock", "model": model_name()}
    try:
        _client()
        return {"status": "configured", "model": model_name()}
    except Exception as e:  # noqa: BLE001 - report, never crash /health
        return {"status": "unavailable", "model": model_name(), "error": type(e).__name__}


def _tokens(msg) -> int:
    u = getattr(msg, "usage_metadata", None) or {}
    return int(u.get("total_tokens", 0))


def backstop(intent: Intent, text: str) -> Intent:
    """Guardrails that do not depend on the model: the rule parser can add a rule break or a missed detail,
    never remove what the model found."""
    r = rule_parse(text)
    upd = {}
    if r.rule_break and not intent.rule_break:
        upd["rule_break"] = r.rule_break
    if intent.type == "replan" and r.type == "replan":
        if r.use_loaded_events and not intent.use_loaded_events:
            upd["use_loaded_events"] = True
        for k in ("start_week", "duration_weeks", "capacity_loss_pct"):
            if getattr(intent, k) is None and getattr(r, k) is not None:
                upd[k] = getattr(r, k)
    return intent.model_copy(update=upd) if upd else intent


def parse_intent(text: str) -> tuple[Intent, dict]:
    if mock_llm():
        return rule_parse(text), {"source": "rules", "llm_calls": 0, "tokens": 0}
    calls = tokens = 0
    t0 = time.perf_counter()
    for _ in range(2):  # one retry, then rules
        try:
            chain = _client().with_structured_output(Intent, include_raw=True)
            calls += 1
            out = chain.invoke([("system", ROUTER_PROMPT), ("human", text)])
            tokens += _tokens(out.get("raw"))
            if out.get("parsed") is not None:
                return backstop(out["parsed"], text), {"source": "llm", "llm_calls": calls, "tokens": tokens,
                                       "ms": round((time.perf_counter() - t0) * 1000)}
        except Exception:  # noqa: BLE001 - provider errors fall back to rules
            pass
    return rule_parse(text), {"source": "rules_fallback", "llm_calls": calls, "tokens": tokens}


def narrate(task: str, evidence: dict, bad: list[str] | None = None) -> tuple[str | None, dict]:
    """Return (text, meta); text is None when no model is available, so the caller uses the template."""
    if mock_llm():
        return None, {"llm_calls": 0, "tokens": 0}
    msg = f"TASK: {task}\nEVIDENCE: {json.dumps(evidence, default=str)}"
    if bad:
        msg += f"\nYour previous answer used figures not in the evidence: {', '.join(bad)}. Remove or correct them."
    try:
        client = _client()
    except Exception as e:  # noqa: BLE001 - not configured (e.g. no key): no call was made, so none is counted
        return None, {"llm_calls": 0, "tokens": 0, "error": type(e).__name__}
    try:
        out = client.invoke([("system", WRITER_PROMPT), ("human", msg)])
        content = out.content if isinstance(out.content, str) else "".join(
            p.get("text", "") for p in out.content if isinstance(p, dict))
        return content.strip(), {"llm_calls": 1, "tokens": _tokens(out)}
    except Exception as e:  # noqa: BLE001
        return None, {"llm_calls": 1, "tokens": 0, "error": type(e).__name__}
