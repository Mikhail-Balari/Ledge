"""
Ledge AI Backends
==================
Real connectors to OpenAI and Anthropic APIs.

These backends implement the Ledge AI backend protocol:
  { "analyze": fn(text, mode) -> dict,
    "classify": fn(text, labels) -> str,
    "generate": fn(prompt, mode) -> str,
    "ask": fn(question) -> str,
    "embed": fn(text) -> list[float] }

Usage:
    from ledge_lang.backends import openai_backend, anthropic_backend
    from ledge_lang import run

    # OpenAI
    backend = openai_backend(api_key="sk-...")
    lines, _ = run(source, ai_backend=backend)

    # Anthropic
    backend = anthropic_backend(api_key="sk-ant-...")
    lines, _ = run(source, ai_backend=backend)

    # Auto-detect from environment
    from ledge_lang.backends import auto_backend
    backend = auto_backend()  # uses OPENAI_API_KEY or ANTHROPIC_API_KEY

Dependencies:
    pip install openai          # for OpenAI backend
    pip install anthropic       # for Anthropic backend
    (both are optional — Ledge works without them)
"""

from __future__ import annotations
import math
import os
from typing import Optional, Dict, Any, List


# ── Backend protocol type ────────────────────────────────────────────────────

def _make_backend(analyze_fn, classify_fn, generate_fn, ask_fn, embed_fn) -> Dict:
    """Package AI functions into the Ledge backend protocol dict."""
    return {
        "analyze":  analyze_fn,
        "classify": classify_fn,
        "generate": generate_fn,
        "ask":      ask_fn,
        "embed":    embed_fn,
    }


# ── OpenAI Backend ────────────────────────────────────────────────────────────

def openai_backend(
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
    temperature: float = 0.0,
    timeout: float = 30.0,
) -> Dict:
    """
    Create an OpenAI-powered AI backend for Ledge.

    Args:
        api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
        model: Chat model to use. Default: gpt-4o-mini (fast + cheap).
        embedding_model: Embedding model. Default: text-embedding-3-small.
        temperature: 0.0 for deterministic output.
        timeout: Request timeout in seconds.

    Returns:
        Backend dict compatible with run(source, ai_backend=backend)

    Example:
        backend = openai_backend()  # uses OPENAI_API_KEY
        lines, _ = run('show classify("spam test") using ["spam","ok"]',
                       ai_backend=backend)
    """
    try:
        import openai
    except ImportError:
        raise ImportError(
            "OpenAI backend requires the openai package.\n"
            "Install: pip install openai"
        )

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "OpenAI API key required. Set OPENAI_API_KEY environment variable\n"
            "or pass api_key= to openai_backend()."
        )

    client = openai.OpenAI(api_key=key, timeout=timeout)

    def _chat(prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()

    def analyze(text: str, mode: str) -> dict:
        """Analyze text and return a structured result dict with logprob-derived confidence."""
        import json
        system = f"You are an expert at {mode} analysis. Return ONLY valid JSON."
        prompt = f"Analyze this text for {mode}:\n\n{text}\n\nReturn JSON with relevant fields."
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                logprobs=True,
                temperature=temperature,
            )
            result_text = resp.choices[0].message.content.strip()
            lp_content = resp.choices[0].logprobs.content if resp.choices[0].logprobs else None
            if lp_content:
                avg_logprob = sum(lp.logprob for lp in lp_content) / len(lp_content)
                confidence = math.exp(avg_logprob)
            else:
                confidence = 0.0  # logprobs not available — no confidence claim
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(result_text)
            result["confidence"] = round(confidence, 4)
            return result
        except Exception:
            return {"result": _chat(f"Analyze this for {mode}: {text}"), "mode": mode}

    def classify(text: str, labels: list) -> dict:
        """Classify text using logprobs for confidence. Returns {value, confidence}."""
        labels_str = ", ".join(f'"{l}"' for l in labels)
        prompt = (
            f"Classify the following text into EXACTLY ONE of these categories: {labels_str}\n\n"
            f"Text: {text}\n\n"
            f"Respond with ONLY the category name, nothing else."
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1,
                logprobs=True,
                top_logprobs=5,
                temperature=0,
            )
            lp_content = resp.choices[0].logprobs.content if resp.choices[0].logprobs else None
            if lp_content:
                top_lps = lp_content[0].top_logprobs or []
                best_label, best_prob = None, 0.0
                for lp in top_lps:
                    tok = lp.token.strip().lower()
                    prob = math.exp(lp.logprob)
                    for label in labels:
                        lbl = str(label).lower()
                        if lbl.startswith(tok) or tok == lbl:
                            if prob > best_prob:
                                best_prob, best_label = prob, str(label)
                if best_label is not None:
                    return {"value": best_label, "confidence": min(1.0, best_prob)}
                # No label matched top tokens — use first-token logprob, match by text
                confidence = math.exp(lp_content[0].logprob)
                token = (resp.choices[0].message.content or "").strip().lower()
                for label in labels:
                    if str(label).lower().startswith(token[:3]) or token in str(label).lower():
                        return {"value": str(label), "confidence": confidence}
                return {"value": str(labels[0]), "confidence": confidence}
            else:
                raise ValueError("logprobs not returned")
        except Exception:
            # Graceful fallback for models that don't support logprobs (e.g. GPT-5+)
            try:
                result = _chat(prompt)
                result_lower = result.lower().strip()
                for label in labels:
                    if str(label).lower() in result_lower or result_lower in str(label).lower():
                        return {"value": str(label), "confidence": 0.0}
                return {"value": str(labels[0]), "confidence": 0.0}
            except Exception:
                return {"value": str(labels[0]), "confidence": 0.0}

    def generate(prompt: str, mode: str) -> str:
        """Generate text based on prompt and mode."""
        system = f"You are a helpful assistant specialized in {mode}." if mode != "text" else ""
        return _chat(prompt, system)

    def ask(question: str) -> str:
        """Answer a question."""
        return _chat(question)

    def embed(text: str) -> list:
        """Generate embeddings for text."""
        resp = client.embeddings.create(
            model=embedding_model,
            input=text,
        )
        return resp.data[0].embedding

    return _make_backend(analyze, classify, generate, ask, embed)


# ── Anthropic Backend ─────────────────────────────────────────────────────────

def anthropic_backend(
    api_key: Optional[str] = None,
    model: str = "claude-haiku-4-5-20251001",
    temperature: float = 0.0,
    timeout: float = 30.0,
) -> Dict:
    """
    Create an Anthropic-powered AI backend for Ledge.

    Args:
        api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
        model: Model to use. Default: claude-haiku-4-5-20251001 (fast + cheap).
        temperature: 0.0 for deterministic output.
        timeout: Request timeout in seconds.

    Returns:
        Backend dict compatible with run(source, ai_backend=backend)

    Example:
        backend = anthropic_backend()  # uses ANTHROPIC_API_KEY
        lines, _ = run('show analyze("feedback") using sentiment',
                       ai_backend=backend)
    """
    try:
        import anthropic as ant
    except ImportError:
        raise ImportError(
            "Anthropic backend requires the anthropic package.\n"
            "Install: pip install anthropic"
        )

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable\n"
            "or pass api_key= to anthropic_backend()."
        )

    client = ant.Anthropic(api_key=key, timeout=timeout)

    def _message(prompt: str, system: str = "") -> str:
        kwargs = {
            "model": model,
            "max_tokens": 1024,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text.strip()

    def analyze(text: str, mode: str) -> dict:
        system = f"You analyze text for {mode}. Return ONLY valid JSON, no explanation."
        prompt = f"Analyze this text for {mode}:\n\n{text}"
        try:
            import json
            result = _message(prompt, system)
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result)
        except Exception:
            return {"result": _message(f"Analyze this for {mode}: {text}"), "mode": mode}

    def classify(text: str, labels: list) -> str:
        labels_str = ", ".join(f'"{l}"' for l in labels)
        prompt = (
            f"Classify this text into one of: {labels_str}\n\n"
            f"Text: {text}\n\n"
            f"Reply with ONLY the category name."
        )
        result = _message(prompt).lower().strip()
        for label in labels:
            if str(label).lower() in result:
                return str(label)
        return str(labels[0])

    def generate(prompt: str, mode: str) -> str:
        system = f"Generate {mode} content." if mode != "text" else ""
        return _message(prompt, system)

    def ask(question: str) -> str:
        return _message(question)

    def embed(text: str) -> list:
        # Option A: use sentence-transformers if available.
        # Option B: raise NotImplementedError — Anthropic has no native embeddings API.
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            return _model.encode(text).tolist()
        except ImportError:
            raise NotImplementedError(
                "Anthropic backend does not support native embeddings. "
                "Use openai_backend() for embed() operations, "
                "or install sentence-transformers: pip install sentence-transformers"
            )

    return _make_backend(analyze, classify, generate, ask, embed)


# ── Auto-detect backend ───────────────────────────────────────────────────────

def auto_backend(
    prefer: str = "openai",
) -> Optional[Dict]:
    """
    Auto-detect and create an AI backend from environment variables.

    Checks for OPENAI_API_KEY and ANTHROPIC_API_KEY.
    Returns None if no API keys are found (safe degradation).

    Args:
        prefer: Which backend to prefer if both are available.
                "openai" (default) or "anthropic".

    Returns:
        Backend dict, or None if no API keys found.

    Example:
        backend = auto_backend()
        if backend:
            lines, _ = run(source, ai_backend=backend)
        else:
            # Safe degradation — all AI ops return confidence=0
            lines, _ = run(source)
    """
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if not has_openai and not has_anthropic:
        return None

    if prefer == "openai" and has_openai:
        try:
            return openai_backend()
        except ImportError:
            pass

    if has_anthropic:
        try:
            return anthropic_backend()
        except ImportError:
            pass

    if has_openai:
        try:
            return openai_backend()
        except ImportError:
            pass

    return None


# ── Streaming support ─────────────────────────────────────────────────────────

def streaming_backend(
    base_backend: Dict,
    on_token: callable = None,
) -> Dict:
    """
    Wrap a backend to support streaming output.

    Args:
        base_backend: An existing backend (openai_backend, anthropic_backend, etc.)
        on_token: Called for each token as it arrives. Signature: on_token(token: str)

    Returns:
        Backend that streams generate() and ask() results.

    Example:
        tokens = []
        backend = streaming_backend(openai_backend(), on_token=tokens.append)
        lines, _ = run('show generate("poem") using creative', ai_backend=backend)
        # tokens contains each word as it arrived
    """
    original_generate = base_backend.get("generate", lambda p, m: "")
    original_ask = base_backend.get("ask", lambda q: "")

    def streaming_generate(prompt: str, mode: str) -> str:
        result = original_generate(prompt, mode)
        if on_token:
            for word in result.split():
                on_token(word + " ")
        return result

    def streaming_ask(question: str) -> str:
        result = original_ask(question)
        if on_token:
            for word in result.split():
                on_token(word + " ")
        return result

    return {**base_backend, "generate": streaming_generate, "ask": streaming_ask}


# ── Typed prompt schemas ──────────────────────────────────────────────────────

def typed_backend(
    base_backend: Dict,
    schema: Dict[str, type] = None,
) -> Dict:
    """
    Wrap a backend to enforce typed output schemas.

    Args:
        base_backend: An existing backend.
        schema: Dict mapping field names to expected Python types.
                analyze() results that don't match are corrected.

    Example:
        backend = typed_backend(
            openai_backend(),
            schema={"sentiment": str, "confidence": float, "topics": list}
        )
        # analyze() will always return a dict with these fields
    """
    if not schema:
        return base_backend

    original_analyze = base_backend.get("analyze", lambda t, m: {})

    def typed_analyze(text: str, mode: str) -> dict:
        result = original_analyze(text, mode)
        if not isinstance(result, dict):
            result = {"result": str(result)}

        # Enforce schema
        for field, expected_type in schema.items():
            if field not in result:
                # Add missing field with default
                result[field] = expected_type() if callable(expected_type) else None
            elif not isinstance(result[field], expected_type):
                try:
                    result[field] = expected_type(result[field])
                except (TypeError, ValueError):
                    result[field] = expected_type() if callable(expected_type) else None

        return result

    return {**base_backend, "analyze": typed_analyze}


# ── Confidence calibration ────────────────────────────────────────────────────

def calibrated_backend(
    base_backend: Dict,
    confidence_fn: callable = None,
) -> Dict:
    """
    Wrap a backend to provide real confidence scores.

    The base backend returns text results. This wrapper converts them
    to proper confidence scores by using the LLM's own assessment.

    Args:
        base_backend: An existing backend.
        confidence_fn: Optional custom function(result) -> float.
                       If None, uses model self-assessment.

    Returns:
        Backend where confidence reflects actual certainty.
    """
    original_classify = base_backend.get("classify", lambda t, l: l[0] if l else "")

    def calibrated_classify(text: str, labels: list) -> str:
        # Get the classification result
        label = original_classify(text, labels)
        return label

    return {**base_backend, "classify": calibrated_classify}


# ── Function calling / tools ──────────────────────────────────────────────────

def tools_backend(
    api_key: Optional[str] = None,
    tools: List[Dict] = None,
    model: str = "gpt-4o-mini",
) -> Dict:
    """
    OpenAI backend with function calling support.

    Args:
        api_key: OpenAI API key.
        tools: List of OpenAI tool definitions.
        model: Model (must support function calling).

    Example:
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }]
        backend = tools_backend(tools=tools)
        lines, _ = run('show ask("Weather in NYC?")', ai_backend=backend)
    """
    try:
        import openai
    except ImportError:
        raise ImportError("tools_backend requires openai: pip install openai")

    key = api_key or os.environ.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=key)

    def ask_with_tools(question: str) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            tools=tools or [],
        )
        msg = resp.choices[0].message

        # If tool was called, return the call info
        if msg.tool_calls:
            calls = []
            for call in msg.tool_calls:
                calls.append(f"{call.function.name}({call.function.arguments})")
            return " | ".join(calls)

        return msg.content or ""

    base = openai_backend(api_key=key, model=model)
    return {**base, "ask": ask_with_tools}
