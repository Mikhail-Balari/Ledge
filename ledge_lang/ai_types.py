"""
Ledge runtime types for AI-uncertainty handling.

Provides the runtime representation of language-level constructs used by
the interpreter and exposed to user code:
  - Uncertain[T] : a value paired with a confidence score in [0.0, 1.0]
  - UncertainChain: composes uncertainty across a sequence of AI steps
  - AIDerived    : provenance-preserving wrapper for values extracted
                   from Uncertain (so caller code can still detect AI origin)
  - LedgeStream  : lazy iterator with filter/transform/take operators
  - LedgePipeline: composable processing stages
  - AuditTrail   : in-memory hash-chained log of AI operations

Similar concepts exist in other ecosystems (Rx for streams, statically-typed
optional/maybe types for Uncertain-like flows, the various conformal-prediction
and PSI libraries for uncertainty). This file is the Ledge-specific runtime,
not a claim of novelty. The static rules around when an Uncertain value may
be used live in `ledge_lang/typechecker.py`.
"""

import math
import time
import threading
import json
import hashlib
from typing import Any, Callable, Iterator, Optional, List, Dict
from .core_types import (
    NOTHING, LedgeList, LedgeMap, LedgeError,
    _repr, _truthy, _type_of, _py_to_ledge, _ledge_to_py
)


# ── Uncertain[T] ──────────────────────────────────────────────────────────────

class Uncertain:
    """
    A value paired with a confidence score in [0.0, 1.0].

    In Ledge:
        define result as analyze("text") using sentiment
        # result has runtime type Uncertain (not Map), and the static
        # checker rejects direct uses unless they go through a recognized
        # confidence guard, when(...), or an explicit unsafe_value_of(...).

    The confidence score is supplied by the backend (token logprobs for
    OpenAI, structured self-assessment for Anthropic) and is NOT assumed
    to be a calibrated correctness probability. See CALIBRATION_GUIDE.md.
    """
    
    def __init__(self, value: Any, confidence: float, source: str = "unknown",
                 model: str = "", timestamp: float = None, declared_type: str = None):
        self.value = value
        self.confidence = max(0.0, min(1.0, float(confidence)))
        self.source = source
        self.model = model
        self.timestamp = timestamp or time.time()
        # declared_type: the TYPE this Uncertain was promised to hold
        # This is independent of value (which may be NOTHING if no backend)
        self.declared_type = declared_type  # "text", "map", "list", None
        self._hash = hashlib.sha256(
            json.dumps(_ledge_to_py(value), sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
    
    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.8
    
    @property
    def is_uncertain(self) -> bool:
        return self.confidence < 0.5
    
    def when(self, threshold: float, fallback: Any = NOTHING) -> Any:
        """Return value if confidence >= threshold, else fallback."""
        if self.confidence >= threshold:
            return self.value
        return fallback
    
    def unwrap(self, threshold: float = 0.0) -> Any:
        """Get the value. Raises LedgeError if below threshold."""
        if self.confidence >= threshold:
            return self.value
        raise LedgeError(
            f"Confidence {self.confidence:.2f} is below threshold {threshold:.2f}. "
            f"Use 'when confidence > {threshold}' to handle this case."
        )
    
    def map(self, fn: Callable) -> 'Uncertain':
        """Transform the value, preserving confidence."""
        try:
            new_value = fn(self.value)
            return Uncertain(new_value, self.confidence, self.source, self.model)
        except Exception as e:
            return Uncertain(NOTHING, 0.0, self.source, self.model)
    
    def to_map(self) -> LedgeMap:
        """Convert to Ledge map for inspection."""
        return LedgeMap({
            "value":      self.value,
            "confidence": self.confidence,
            "source":     self.source,
            "model":      self.model,
            "timestamp":  self.timestamp,
            "hash":       self._hash,
            "confident":  self.is_confident,
        })
    
    def __repr__(self):
        conf_bar = "█" * int(self.confidence * 10) + "░" * (10 - int(self.confidence * 10))
        return f"~{_repr(self.value)} [{conf_bar} {self.confidence:.0%}]"
    
    def __bool__(self):
        return self.is_confident and _truthy(self.value)
    
    def __getitem__(self, key):
        """Allow field access on uncertain maps."""
        if isinstance(self.value, LedgeMap):
            return self.value.get(_repr(key), NOTHING)
        return NOTHING
    
    def __getattr__(self, name):
        if name in ('value', 'confidence', 'source', 'model', 'timestamp', '_hash'):
            raise AttributeError(name)
        if isinstance(self.value, LedgeMap):
            return self.value.get(name, NOTHING)
        return NOTHING


# ── UncertainChain ───────────────────────────────────────────────────────────

class UncertainChain:
    """
    A chain of AI results where uncertainty propagates automatically between steps.

    chain_confidence = product of all step confidences
    chain_is_safe = True only if ALL steps are above the threshold
    """

    def __init__(self):
        self.steps = []
        self.step_names = []

    def add(self, result, name=""):
        if isinstance(result, Uncertain):
            self.steps.append(result)
        else:
            self.steps.append(Uncertain(result, 1.0))
        self.step_names.append(name or f"step_{len(self.steps)}")
        return self

    _DECAY = 0.9

    def chain_confidence(self):
        """
        Computes composite chain confidence using three factors:

        1. Position-weighted product: early step errors propagate, so later steps
           are penalized more as the chain grows.
           weight[i] = (1/DECAY)^i, all weights >= 1, so product(c^w) <= product(c).

        2. Weak step penalty: any step with confidence < 0.5 penalizes the chain.
           penalty = product(min(1.0, c/0.5) for c < 0.5)

        3. G1 safety floor: if any step has confidence == 0.0, return 0.0.
        """
        if not self.steps:
            return 0.0
        confidences = [s.confidence for s in self.steps]
        if any(c == 0.0 for c in confidences):
            return 0.0
        n = len(self.steps)
        weights = [(1.0 / self._DECAY) ** i for i in range(n)]
        weighted_product = math.prod(c ** w for c, w in zip(confidences, weights))
        weak_penalty = math.prod(
            min(1.0, c / 0.5) for c in confidences if c < 0.5
        ) if any(c < 0.5 for c in confidences) else 1.0
        return weighted_product * weak_penalty

    def chain_risk_level(self) -> str:
        """Return a risk classification based on chain_confidence().
        LOW >= 0.8 | MEDIUM >= 0.5 | HIGH >= 0.2 | CRITICAL < 0.2
        """
        c = self.chain_confidence()
        if c >= 0.8:   return "LOW"
        if c >= 0.5:   return "MEDIUM"
        if c >= 0.2:   return "HIGH"
        return "CRITICAL"

    def chain_is_safe(self, threshold=0.8):
        if not self.steps:
            return False
        return all(s.confidence >= threshold for s in self.steps)

    def weakest_step(self):
        """Return the name of the step with the smallest weighted contribution."""
        if not self.steps:
            return ""
        n = len(self.steps)
        weights = [(1.0 / self._DECAY) ** i for i in range(n)]
        weighted_contribs = [
            s.confidence ** w for s, w in zip(self.steps, weights)
        ]
        min_idx = min(range(n), key=lambda i: weighted_contribs[i])
        return self.step_names[min_idx]

    def chain_audit(self):
        return LedgeList([
            LedgeMap({
                "name":       self.step_names[i],
                "confidence": self.steps[i].confidence,
                "source":     self.steps[i].source,
                "model":      self.steps[i].model,
            })
            for i in range(len(self.steps))
        ])

    def __repr__(self):
        return (f"<UncertainChain steps={len(self.steps)} "
                f"chain_confidence={self.chain_confidence():.3f}>")


# ── AIDerived ─────────────────────────────────────────────────────────────────

class AIDerived:
    """
    Wraps a value extracted from Uncertain to preserve AI provenance through
    function boundaries. Once a value_of() or when() call extracts a concrete
    value, it becomes AIDerived so callers can detect AI origin even after the
    Uncertain wrapper is gone.
    """
    _is_ai_derived = True

    def __init__(self, value, source_confidence: float, source_operation: str,
                 chain_id: str = None):
        self.value = value
        self.source_confidence = source_confidence
        self.source_operation = source_operation
        self.chain_id = chain_id

    def __repr__(self):
        from .core_types import _repr
        return _repr(self.value)

    def __str__(self):
        return repr(self)


# ── Stream[T] ─────────────────────────────────────────────────────────────────

class LedgeStream:
    """
    A lazy, potentially infinite sequence of values with filter/transform/take.

    In Ledge:
        define temps as stream from "mqtt://sensors/temp"
        define alerts as temps where value > 90

    Similar in spirit to Rx Observables, Python generators with itertools,
    and Java Streams. The Ledge-specific part is the language-level syntax
    integration, not the underlying abstraction.
    """
    
    def __init__(self, source, name: str = "<stream>"):
        self._source = source      # iterator, callable, or queue
        self._name = name
        self._filters = []
        self._transforms = []
        self._buffer = []
        self._subscribers = []     # reactive listeners
        self._lock = threading.Lock()
        self._closed = False
        self._stats = {"total": 0, "filtered": 0, "errors": 0}
    
    @classmethod
    def from_list(cls, lst) -> 'LedgeStream':
        """Create a finite stream from a list (re-iterable)."""
        data = list(lst)
        s = cls(None, "<list-stream>")
        s._data = data   # stored for re-iteration
        return s
    
    @classmethod
    def from_generator(cls, gen, name="<gen-stream>") -> 'LedgeStream':
        """Create a stream from a generator function."""
        return cls(gen, name)
    
    @classmethod
    def interval(cls, seconds: float) -> 'LedgeStream':
        """Create an infinite stream that ticks every N seconds."""
        def ticker():
            i = 0
            while True:
                yield i
                i += 1
                time.sleep(seconds)
        return cls(ticker(), f"<interval/{seconds}s>")
    
    @classmethod
    def of(cls, *values) -> 'LedgeStream':
        """Create a stream from explicit values."""
        return cls(iter(values), "<values-stream>")
    
    def where(self, predicate: Callable) -> 'LedgeStream':
        """Filter: keep only items where predicate returns truthy."""
        parent = self
        new = LedgeStream(None, f"{parent._name}.where")
        new._parent = parent
        new._filters.append(predicate)
        return new
    
    def transform(self, fn: Callable) -> 'LedgeStream':
        """Map: transform each item."""
        parent = self
        new = LedgeStream(None, f"{parent._name}.transform")
        new._parent = parent
        new._transforms.append(fn)
        return new
    
    def take(self, n: int) -> 'LedgeStream':
        """Limit to first N items."""
        parent = self
        s = LedgeStream(None, f"{parent._name}.take({n})")
        s._parent = parent
        s._take_limit = n
        return s
    
    def window(self, size: int) -> 'LedgeStream':
        """Sliding window of N items."""
        def windowed():
            buf = []
            for item in self._chain_iter():
                buf.append(item)
                if len(buf) >= size:
                    yield LedgeList(buf[-size:])
        return LedgeStream(windowed(), f"{self._name}.window({size})")
    
    def collect(self, limit: int = 10000) -> LedgeList:
        """Force evaluation into a list."""
        result = []
        for i, item in enumerate(self._chain_iter()):
            if i >= limit: break
            result.append(item)
        return LedgeList(result)
    
    def first(self) -> Any:
        """Get the first item."""
        for item in self._chain_iter():
            return item
        return NOTHING
    
    def subscribe(self, callback: Callable):
        """Register a reactive listener."""
        self._subscribers.append(callback)
    
    def _chain_iter(self) -> Iterator:
        """Internal: iterate with filters/transforms, re-iterable via parent chain."""
        parent = getattr(self, '_parent', None)
        data   = getattr(self, '_data',   None)
        take_n = getattr(self, '_take_limit', None)

        if parent is not None:
            base = parent._chain_iter()
        elif data is not None:
            base = iter(data)
        elif self._source is not None:
            base = self._source if hasattr(self._source, '__next__') else iter(self._source)
        else:
            return  # empty

        count = 0
        for item in base:
            if take_n is not None and count >= take_n:
                break
            skip = False
            for f in self._filters:
                try:
                    # Support both calling conventions:
                    # (item) -> bool  (direct)
                    # ([item], {}, None) -> bool  (Ledge Native convention)
                    try:
                        result = f(item)  # direct call first
                    except TypeError:
                        result = f([item], {}, None)  # Ledge convention fallback
                    if not _truthy(result):
                        skip = True; break
                except Exception:
                    skip = True; break
            if skip:
                self._stats["filtered"] += 1
                continue
            for t in self._transforms:
                try:
                    try:
                        item = t(item)  # direct call first
                    except TypeError:
                        item = t([item], {}, None)  # Ledge convention fallback
                except Exception:
                    break
            self._stats["total"] += 1
            for sub in self._subscribers:
                try: sub(item)
                except Exception: pass
            yield item
            count += 1


    def __iter__(self):
        return self._chain_iter()
    
    def __repr__(self):
        return f"<stream {self._name} total={self._stats['total']}>"


# ── Pipeline ──────────────────────────────────────────────────────────────────

class LedgePipeline:
    """
    A composable, declarative data processing pipeline.
    
    In Ledge:
        define process as pipeline:
            read "data.csv" as csv
            | filter row: row["valid"] = true
            | transform row: row["score"] * 1.2
            | analyze using sentiment
            | write "output.json" as json
        
        run process
        # or
        run process distributed across 4 workers
    
    The pipeline is a value — it can be passed, stored, modified.
    Execution is lazy and can be distributed.
    """
    
    def __init__(self, name: str = "<pipeline>"):
        self._name = name
        self._stages = []
        self._stats = {}
    
    def stage(self, name: str, fn: Callable, **kwargs) -> 'LedgePipeline':
        """Add a processing stage."""
        self._stages.append({"name": name, "fn": fn, "kwargs": kwargs})
        return self
    
    def run(self, data=None, workers: int = 1) -> Any:
        """Execute the pipeline."""
        current = data
        
        for stage in self._stages:
            t0 = time.perf_counter()
            try:
                current = stage["fn"](current, **stage["kwargs"])
            except LedgeError:
                raise
            except Exception as e:
                raise LedgeError(f"Pipeline stage '{stage['name']}' failed: {e}")
            finally:
                elapsed = time.perf_counter() - t0
                self._stats[stage["name"]] = elapsed
        
        return current
    
    def __repr__(self):
        stages = " | ".join(s["name"] for s in self._stages)
        return f"<pipeline {self._name}: {stages}>"


# ── Audit Trail ───────────────────────────────────────────────────────────────

class AuditTrail:
    """
    In-memory hash-chained log of AI operations performed during a run.

    Every call to analyze/generate/classify/ask/embed is recorded with:
      - timestamp
      - input hash (the input itself is NOT stored)
      - model identifier
      - output type and confidence
      - caller context
      - SHA-256 chain hash linking to the previous entry

    Threat model and limitations:
      - Detects post-hoc modification of records by an actor without
        access to the anchor file (see audit_store.py).
      - Does NOT protect against an attacker who controls both the
        SQLite store and the on-disk anchor file.
      - Does NOT prove correctness of the AI outputs themselves.
      - Recording this trail does not by itself satisfy any specific
        regulatory regime — it is supporting evidence, not compliance.
    """
    
    _global = None
    _GENESIS = "0" * 64  # expected prev_hash of first entry in any trail

    @classmethod
    def global_trail(cls) -> 'AuditTrail':
        if cls._global is None:
            cls._global = cls()
        return cls._global

    def __init__(self):
        self._entries = []
        self._lock = threading.Lock()
        self._last_hash = self._GENESIS  # chain tip
        self._anchor = self._GENESIS     # expected prev_hash of _entries[0]

    @staticmethod
    def _compute_chain_hash(audit_id: str, operation: str, input_hash: str,
                            output_type: str, confidence: float, model: str,
                            caller: str, timestamp: float, prev_hash: str) -> str:
        """Deterministic chain hash for one audit entry."""
        chain_input = (
            f"{audit_id}:{operation}:{input_hash}:{output_type}:"
            f"{confidence:.6f}:{model}:{caller}:{timestamp:.6f}:{prev_hash}"
        )
        return hashlib.sha256(chain_input.encode()).hexdigest()

    def record(self, operation: str, input_val: Any, output_val: Any,
               model: str = "", confidence: float = 1.0,
               caller: str = "<unknown>") -> str:
        """Record an AI operation. Returns the audit ID."""
        input_str = _repr(input_val)

        with self._lock:
            ts = time.time()
            audit_id = hashlib.sha256(
                f"{ts}{input_str}{operation}".encode()
            ).hexdigest()[:12]

            ih = hashlib.sha256(input_str.encode()).hexdigest()[:16]
            ot = _type_of(output_val)
            prev_hash = self._last_hash

            chain_hash = self._compute_chain_hash(
                audit_id, operation, ih, ot, confidence, model, caller, ts, prev_hash
            )

            entry = LedgeMap({
                "id":          audit_id,
                "operation":   operation,
                "input_hash":  ih,
                "output_type": ot,
                "confidence":  confidence,
                "model":       model,
                "caller":      caller,
                "timestamp":   ts,
                "prev_hash":   prev_hash,
                "chain_hash":  chain_hash,
            })

            self._entries.append(entry)
            self._last_hash = chain_hash

            if len(self._entries) > 10000:
                self._entries = self._entries[-10000:]
                self._anchor = self._entries[0]["prev_hash"]

        # Forward to SQLite store if one is active (never let it break execution)
        try:
            from . import audit_store as _asm
            _store = _asm.GLOBAL_AUDIT_STORE
            if _store is not None:
                _store.record(
                    operation=operation,
                    input_hash=ih,
                    output_type=ot,
                    confidence=confidence,
                    model=model or "mock",
                    program_id=get_program_id(),
                    decision_id=audit_id,
                )
        except Exception:
            pass

        return audit_id

    def verify(self) -> bool:
        """Return True if the chain is intact, False if any entry was modified."""
        with self._lock:
            entries = list(self._entries)
            anchor = self._anchor

        if not entries:
            return True

        if entries[0]["prev_hash"] != anchor:
            return False

        prev_hash = anchor
        for entry in entries:
            if entry["prev_hash"] != prev_hash:
                return False

            expected = self._compute_chain_hash(
                entry["id"], entry["operation"], entry["input_hash"],
                entry["output_type"], entry["confidence"], entry["model"],
                entry["caller"], entry["timestamp"], prev_hash,
            )
            if entry["chain_hash"] != expected:
                return False

            prev_hash = entry["chain_hash"]

        return True

    def query(self, operation: str = None, since: float = None,
              limit: int = 100) -> LedgeList:
        """Query the audit trail."""
        with self._lock:
            entries = list(self._entries)

        if operation:
            entries = [e for e in entries if e["operation"] == operation]
        if since:
            entries = [e for e in entries if e["timestamp"] >= since]

        return LedgeList(entries[-limit:])

    def export(self) -> str:
        """Export as JSON string."""
        with self._lock:
            return json.dumps([_ledge_to_py(e) for e in self._entries],
                              indent=2, default=str)

    def reset(self):
        """Clear all entries and reset the chain to genesis (per-run isolation)."""
        with self._lock:
            self._entries.clear()
            self._last_hash = self._GENESIS
            self._anchor = self._GENESIS

    def __len__(self):
        return len(self._entries)

    def __bool__(self):
        return True  # Always truthy — even empty audit is a valid audit object

    def __repr__(self):
        return f"<audit_trail entries={len(self._entries)}>"


# ── MCP Native Client ─────────────────────────────────────────────────────────

class MCPTool:
    """
    A tool connected via the Model Context Protocol.
    
    In Ledge:
        define search as mcp tool "brave-search" at "http://localhost:3000"
        define results as search("latest AI news")
    
    This wraps any MCP server as a callable Ledge function.
    No SDK, no boilerplate, no JSON schema to write manually.
    """
    
    def __init__(self, name: str, endpoint: str, tool_name: str = None):
        self.name = name
        self.endpoint = endpoint
        self.tool_name = tool_name or name
        self._schema = None
    
    def call(self, args: Any, kwargs: dict) -> Any:
        """Call the MCP tool."""
        try:
            import urllib.request
            
            # Build MCP request
            request_body = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": self.tool_name,
                    "arguments": _ledge_to_py(args[0]) if args else {}
                },
                "id": 1
            }
            
            data = json.dumps(request_body).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                if "error" in result:
                    raise LedgeError(f"MCP error: {result['error']}")
                return _py_to_ledge(result.get("result", NOTHING))
        
        except LedgeError:
            raise
        except Exception as e:
            raise LedgeError(f"MCP tool '{self.name}' failed: {e}")
    
    def __repr__(self):
        return f"<mcp-tool {self.name}@{self.endpoint}>"


# ── Contract ──────────────────────────────────────────────────────────────────

class Contract:
    """
    A verifiable pre/postcondition contract for a function.
    
    In Ledge:
        define process(data: Record) requires:
            data has "id" of type text
            data has "value" of type number
        returns:
            Map where keys include "result"
        ensures:
            result["result"] is number between 0 and 1
        
        # The interpreter verifies these at runtime (v0.2)
        # The compiler will verify them statically (v1.0)
    """
    
    def __init__(self, fn_name: str):
        self.fn_name = fn_name
        self.requires = []    # list of (check_fn, description)
        self.ensures = []     # list of (check_fn, description)
        self.returns_hint = None
    
    def add_require(self, check: Callable, desc: str):
        self.requires.append((check, desc))
    
    def add_ensure(self, check: Callable, desc: str):
        self.ensures.append((check, desc))
    
    def check_pre(self, *args):
        """Verify preconditions before function execution."""
        for check, desc in self.requires:
            try:
                if not check(*args):
                    raise LedgeError(
                        f"Contract violation in '{self.fn_name}': "
                        f"precondition failed: {desc}"
                    )
            except LedgeError:
                raise
            except Exception as e:
                raise LedgeError(
                    f"Contract error in '{self.fn_name}': {desc}: {e}"
                )
    
    def check_post(self, result):
        """Verify postconditions after function execution."""
        for check, desc in self.ensures:
            try:
                if not check(result):
                    raise LedgeError(
                        f"Contract violation in '{self.fn_name}': "
                        f"postcondition failed: {desc}\n"
                        f"  Got: {_repr(result)}"
                    )
            except LedgeError:
                raise
            except Exception as e:
                raise LedgeError(f"Contract error: {desc}: {e}")
    
    def __repr__(self):
        return f"<contract {self.fn_name} requires={len(self.requires)} ensures={len(self.ensures)}>"


# ── Global audit trail ────────────────────────────────────────────────────────

GLOBAL_AUDIT = AuditTrail.global_trail()

# ── Persistent store (optional) ───────────────────────────────────────────────
# Set GLOBAL_AUDIT_STORE to an AuditStore instance to enable SQLite persistence.
# Every AI decision recorded by AuditTrail will also be forwarded there.

GLOBAL_AUDIT_STORE = None          # type: Optional[Any]  # AuditStore | None

_program_id_ctx = threading.local()


def set_program_id(pid: str):
    """Set the program identifier for the current thread (used in audit records)."""
    _program_id_ctx.value = pid


def get_program_id() -> str:
    return getattr(_program_id_ctx, "value", "default")


def make_ai_native_builtins(audit: AuditTrail = None):
    """
    Create AI-native builtin functions that integrate with Uncertain,
    Stream, AuditTrail, and the full type system.
    """
    from .interpreter import _Native, _repr, NOTHING
    audit = audit or GLOBAL_AUDIT
    
    def _n(name, fn):
        return _Native(name, fn)

    def _uncertain_chain_fn(a, k, u):
        chain = UncertainChain()
        items = list(a[0]) if a else []
        for i, item in enumerate(items):
            chain.add(item, f"step_{i+1}")
        return chain

    def _compare_to_ledge(report):
        from .core_types import _py_to_ledge
        return _py_to_ledge(report)

    return {
        # Uncertain type operations
        "confidence_of": _n("confidence_of", lambda a,k,u:
            a[0].confidence if isinstance(a[0], Uncertain) else 1.0),
        
        # value_of and unsafe_value_of share the same runtime behavior — they
        # both extract the inner value as an AIDerived wrapper. The difference
        # is enforced by the static checker: `value_of(x)` on an Uncertain `x`
        # outside a confidence guard is rejected; `unsafe_value_of(x)` is the
        # explicit, deliberately ugly escape hatch.
        "value_of": _n("value_of", lambda a,k,u:
            AIDerived(a[0].value, a[0].confidence,
                      getattr(a[0], 'source', 'unknown') or 'unknown')
            if isinstance(a[0], Uncertain)
            else a[0]),

        "unsafe_value_of": _n("unsafe_value_of", lambda a,k,u:
            AIDerived(a[0].value, a[0].confidence,
                      getattr(a[0], 'source', 'unknown') or 'unknown')
            if isinstance(a[0], Uncertain)
            else a[0]),

        "when": _n("when", lambda a,k,u: (
            AIDerived(a[0].value, a[0].confidence,
                      getattr(a[0], 'source', 'unknown') or 'unknown')
            if a[0].confidence >= float(a[1])
            else (a[2] if len(a) > 2 else NOTHING)
        ) if isinstance(a[0], Uncertain) else a[0]),
        
        "is_confident": _n("is_confident", lambda a,k,u:
            a[0].is_confident if isinstance(a[0], Uncertain) else True),
        
        "uncertain": _n("uncertain", lambda a,k,u:
            Uncertain(a[0], float(a[1]) if len(a) > 1 else 1.0)),
        
        # Stream operations
        "stream_of": _n("stream_of", lambda a,k,u:
            LedgeStream.from_list(a[0]) if a else LedgeStream.of()),
        
        "stream_interval": _n("stream_interval", lambda a,k,u:
            LedgeStream.interval(float(a[0]))),
        
        "stream_take": _n("stream_take", lambda a,k,u:
            a[0].take(int(a[1])) if isinstance(a[0], LedgeStream) else a[0]),
        
        "stream_collect": _n("stream_collect", lambda a,k,u:
            a[0].collect(int(a[1]) if len(a) > 1 else 1000)
            if isinstance(a[0], LedgeStream) else LedgeList(a[0])),
        
        "stream_first": _n("stream_first", lambda a,k,u:
            a[0].first() if isinstance(a[0], LedgeStream) else NOTHING),
        
        # Audit trail operations
        "audit_log": _n("audit_log", lambda a,k,u: audit.query()),

        "audit_query": _n("audit_query", lambda a,k,u:
            audit.query(
                operation=a[0] if a else None,
                limit=int(a[1]) if len(a) > 1 else 100
            )),

        "audit_export": _n("audit_export", lambda a,k,u: audit.export()),

        "audit_verify": _n("audit_verify", lambda a,k,u: audit.verify()),

        # Persistent store builtins (no-ops when store is not active)
        "record_outcome": _n("record_outcome", lambda a, k, u: (
            GLOBAL_AUDIT_STORE.record_outcome(
                str(a[0]),
                bool(a[1]),
                str(a[2]) if len(a) > 2 else "",
            ) or True
        ) if GLOBAL_AUDIT_STORE is not None else NOTHING),

        # Pipeline creation
        "pipeline": _n("pipeline", lambda a,k,u: LedgePipeline()),
        
        # Type checking extensions
        "is_uncertain": _n("is_uncertain", lambda a,k,u: isinstance(a[0], Uncertain)),
        "is_stream":    _n("is_stream",    lambda a,k,u: isinstance(a[0], LedgeStream)),
        "is_pipeline":  _n("is_pipeline",  lambda a,k,u: isinstance(a[0], LedgePipeline)),

        # UncertainChain — transitive uncertainty propagation
        "uncertain_chain": _n("uncertain_chain", _uncertain_chain_fn),

        "chain_confidence": _n("chain_confidence", lambda a,k,u:
            a[0].chain_confidence() if isinstance(a[0], UncertainChain) else 0.0),

        "chain_is_safe": _n("chain_is_safe", lambda a,k,u:
            a[0].chain_is_safe(float(a[1]) if len(a) > 1 else 0.8)
            if isinstance(a[0], UncertainChain) else False),

        "chain_audit": _n("chain_audit", lambda a,k,u:
            a[0].chain_audit() if isinstance(a[0], UncertainChain) else LedgeList([])),

        "weakest_step": _n("weakest_step", lambda a,k,u:
            a[0].weakest_step() if isinstance(a[0], UncertainChain) else ""),

        "chain_risk_level": _n("chain_risk_level", lambda a,k,u:
            a[0].chain_risk_level() if isinstance(a[0], UncertainChain) else "CRITICAL"),

        # Model migration comparison (Feature 4)
        "compare_models_report": _n("compare_models_report", lambda a, k, u: (
            _compare_to_ledge(
                __import__('ledge_lang.comparison', fromlist=['ModelMigrationAnalyzer'])
                .ModelMigrationAnalyzer(GLOBAL_AUDIT_STORE)
                .compare_models(
                    str(a[0]), str(a[1]),
                    program_id=str(a[2]) if len(a) > 2 else None,
                )
            )
        ) if GLOBAL_AUDIT_STORE is not None else NOTHING),

        # Domain calibration (Feature 3)
        "calibrated_threshold": _n("calibrated_threshold", lambda a, k, u: (
            __import__('ledge_lang.calibration', fromlist=['DomainCalibrator'])
            .DomainCalibrator(GLOBAL_AUDIT_STORE)
            .get_calibrated_threshold(str(a[0]), str(a[1]))["threshold"]
        ) if GLOBAL_AUDIT_STORE is not None else 0.85),

        "model_trustworthy": _n("model_trustworthy", lambda a, k, u: (
            __import__('ledge_lang.calibration', fromlist=['DomainCalibrator'])
            .DomainCalibrator(GLOBAL_AUDIT_STORE)
            .is_model_trustworthy(str(a[0]), str(a[1]))
        ) if GLOBAL_AUDIT_STORE is not None else False),

        # Interprocedural uncertainty provenance (Feature 2)
        "has_ai_origin": _n("has_ai_origin", lambda a,k,u:
            getattr(a[0], '_is_ai_derived', False)),

        "origin_confidence": _n("origin_confidence", lambda a,k,u:
            a[0].source_confidence if getattr(a[0], '_is_ai_derived', False) else NOTHING),

        "origin_operation": _n("origin_operation", lambda a,k,u:
            a[0].source_operation if getattr(a[0], '_is_ai_derived', False) else NOTHING),
    }
