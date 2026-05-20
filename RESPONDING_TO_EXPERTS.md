# Ledge - Responding To Expert Questions

These are questions a technical reviewer is likely to ask before taking Ledge
seriously. Each answer is intentionally scoped to the current 1.2.0 alpha.

## Where Does Confidence Come From?

Ledge gets confidence scores from the AI backend you connect. Without a backend,
AI operations return `confidence=0.0` and `value=nothing`.

Programmatic backend example:

```python
from ledge_lang import checked_run
from ledge_lang.backends import openai_backend

backend = openai_backend(api_key="sk-...", model="gpt-4o-mini")
checked_run(source, ai_backend=backend)
```

Backend confidence is a signal from the provider or wrapper. It is not assumed
to be calibrated for your domain.

## Is Confidence Calibrated By Domain?

Only if you record outcomes. Ledge includes calibration utilities that compare
declared confidence with observed correctness:

```bash
ledge audit --calibration MODEL DOMAIN
```

The calibrated threshold is derived from your outcome data. It is not a global
truth about a model.

## Is The Audit Trail Legally Sufficient?

No. The regulatory export is structured evidence:

```bash
ledge audit --export-regulatory report.json
ledge audit --validate-regulatory report.json
```

That can support review, but it is not a compliance certification. Whether a
system satisfies HIPAA, GDPR, the EU AI Act, or any other regime depends on the
surrounding organization, deployment, data handling, and legal context.

## Does It Integrate With Real Model Providers?

Yes. OpenAI and Anthropic backend helpers are included:

```python
from ledge_lang.backends import openai_backend, anthropic_backend

openai = openai_backend(api_key="sk-...", model="gpt-4o-mini")
anthropic = anthropic_backend(api_key="sk-ant-...", model="claude-3-haiku")
```

See `examples/showcase/real_backend.py` for a small backend example.

## Is This Ready For Critical Deployment?

No. Ledge 1.2.0 is an alpha core. It has real tests, examples, CI, checked CLI
execution, a checked Python API helper, conformance tests, and clean wheel
verification, but it has no known production deployments or third-party audit.

Working today:

- static checking for documented unsafe `Uncertain` patterns;
- `ledge run` typechecking by default, with explicit `--unsafe` bypass;
- `checked_run(...)` for Python callers that want the same safety gate;
- runtime properties documented in `GUARANTEES.md`;
- local audit chain and calibration utilities;
- bundled `medical_triage` demo that runs after wheel installation.

Not ready yet:

- no mature package ecosystem;
- no distributed audit trail;
- no formal security audit;
- limited static analysis compared with a mature typed language;
- no third-party validation or production pilot evidence.

The design patterns are relevant to production systems. The implementation
should still be treated as experimental until it has external review and pilot
deployment evidence.
