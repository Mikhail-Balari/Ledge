# Ledge Capability Matrix
## Version 1.1.0

## Para Google (language/infra engineer)

### native_compiler
- **Status:** SHIPPED
- Ledge → C99 → gcc → native binary
- Evidence: `tests/compiler/test_native.py — 28 tests, 100%`

### gc
- **Status:** SHIPPED (reference counting)
- Reference-counted GC in C runtime (ccodegen.py)
- Evidence: `ledge_lang/compiler/ccodegen.py (ldg_incref/ldg_decref)`

### profiler
- **Status:** SHIPPED
- Integrated profiler with TW vs native comparison
- Evidence: `ledge_lang/profiler.py`

### package_system
- **Status:** SHIPPED (5 packages)
- Evidence: `packages/`


### Honest limitations
- No JIT yet — each function compiled AOT
- No garbage collection for cycles (by design)
- String/list operations in native are boxing-based (optimization opportunity)
- No concurrent GC (single-threaded memory model for compiled code)

## Para OpenAI

### backends
- **Status:** SHIPPED

### streaming
- **Status:** SHIPPED
- Streaming AI responses via streaming_backend() wrapper

### function_calling
- **Status:** SHIPPED
- OpenAI function calling via tools_backend()

### typed_prompts
- **Status:** SHIPPED
- Schema enforcement on AI outputs via typed_backend()

### uncertainty_type
- **Status:** SHIPPED
- Uncertain[T] enforced by typechecker — prevents most AI safety bugs

## Para Anthropic

### ai_safety_study
- **Status:** SHIPPED

### uncertainty_invariants
- **Status:** SHIPPED — 26 security tests at 100%

### real_case_studies
- **Status:** PARTIAL — examples run, no third-party deployments yet

