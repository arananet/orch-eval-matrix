# Observability Integration Guide

**orch-eval-matrix** is designed to produce structured, traceable evaluation runs. This guide covers how to attach the evaluation matrix to Langfuse, Phoenix/Arize, and a generic OpenTelemetry collector so every scenario run becomes a queryable, comparable data point.

---

## Recommended Span Attributes

Every evaluation span — regardless of platform — should carry these attributes so results are filterable and dashboardable:

| Attribute | Type | Example |
|---|---|---|
| `eval.scenario_id` | string | `CLR-011` |
| `eval.category` | string | `clarification_required` |
| `eval.subcategory` | string | `ambiguous_system` |
| `eval.domain` | string | `it` |
| `eval.difficulty` | string | `advanced` |
| `eval.score` | float | `8.5` |
| `eval.max_score` | int | `10` |
| `eval.score_pct` | float | `0.85` |
| `eval.routing_expected` | string (JSON) | `["ITTriageAgent","ClarificationAgent"]` |
| `eval.routing_actual` | string (JSON) | `["ITTriageAgent"]` |
| `eval.clarification_expected` | string (JSON) | `["Incident ID","Ticketing system"]` |
| `eval.clarification_actual` | string (JSON) | `["Incident ID"]` |
| `eval.failure_modes_triggered` | string (JSON) | `[]` |
| `eval.critical_failure` | bool | `false` |
| `eval.run_id` | string | `eval-2026-q1-langgraph` |
| `eval.version` | string | `1.0.0` |
| `gen_ai.system` | string | `langgraph` |

---

## 1. Langfuse Integration

[Langfuse](https://langfuse.com) provides trace-level scoring, dataset tracking, and session grouping — ideal for multi-turn scenarios.

### Setup

```bash
pip install langfuse
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

### Tracing a Single Scenario

```python
from langfuse import Langfuse
import json, time

lf = Langfuse()

def run_scenario_with_langfuse(scenario: dict, system_response: dict, score: float):
    trace = lf.trace(
        name=f"orch-eval/{scenario['id']}",
        input={"prompt": scenario.get("prompt"), "turns": scenario.get("turns")},
        output=system_response,
        metadata={
            "eval.scenario_id": scenario["id"],
            "eval.category": scenario["category"],
            "eval.subcategory": scenario["subcategory"],
            "eval.domain": scenario["domain"],
            "eval.version": "1.0.0",
            "eval.run_id": "eval-2026-q1",
        },
        tags=[scenario["category"], scenario.get("domain", "general")],
    )

    # Attach the numeric score
    lf.score(
        trace_id=trace.id,
        name="orch_eval_score",
        value=score,
        comment=f"Max: {sum(scenario['scoring'].values())} pts",
    )

    # Log per-dimension scores
    for dimension, weight in scenario["scoring"].items():
        # dimension_score is your evaluator's 0.0–1.0 rating for this dimension
        pass  # attach as additional scores if desired

    trace.update(status_message="completed")
    return trace.id
```

### Multi-Turn Scenario Sessions

For MTX-* scenarios, group all turns under a single session:

```python
session_id = f"orch-eval-{scenario['id']}-{run_id}"

for i, turn in enumerate(scenario["turns"]):
    trace = lf.trace(
        name=f"orch-eval/{scenario['id']}/turn-{turn['turn']}",
        session_id=session_id,
        input={"user": turn["user"]},
        output=system_turn_response,
        metadata={"eval.turn": turn["turn"], "eval.expected_state": turn.get("expected_state", {})},
    )
```

### Langfuse Dataset for Regression Testing

```python
dataset = lf.create_dataset(name="orch-eval-v1.0.0")

for scenario in all_scenarios:
    dataset.create_item(
        input={"prompt": scenario.get("prompt"), "turns": scenario.get("turns")},
        expected_output={
            "routing": scenario["expected_routing"],
            "clarification": scenario["expected_clarification"],
        },
        metadata={"id": scenario["id"], "category": scenario["category"]},
    )
```

### Recommended Langfuse Dashboard Panels

1. **Score distribution by category** — box plot of `orch_eval_score` grouped by `eval.category`
2. **Failure rate by domain** — count of `eval.critical_failure=true` by `eval.domain`
3. **Score over time** — line chart of mean score per `eval.run_id` for regression tracking
4. **Clarification quality** — % scenarios where `eval.clarification_actual` matches `eval.clarification_expected`

---

## 2. Phoenix / Arize Integration

[Phoenix](https://phoenix.arize.com) (open-source) and [Arize](https://arize.com) (managed) support span-level LLM evaluation with built-in evaluation templates.

### Phoenix Setup (Local)

```bash
pip install arize-phoenix opentelemetry-sdk opentelemetry-exporter-otlp
```

```python
import phoenix as px

# Start Phoenix server (local)
px.launch_app()
# Phoenix UI at http://localhost:6006
```

### Tracing with OpenTelemetry → Phoenix

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

resource = Resource(attributes={"service.name": "orch-eval"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://localhost:6006/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("orch-eval")

def run_scenario_with_phoenix(scenario: dict, system_response: dict, score: float):
    with tracer.start_as_current_span(f"orch_eval.{scenario['id']}") as span:
        span.set_attribute("eval.scenario_id", scenario["id"])
        span.set_attribute("eval.category", scenario["category"])
        span.set_attribute("eval.domain", scenario["domain"])
        span.set_attribute("eval.score", score)
        span.set_attribute("eval.max_score", sum(scenario["scoring"].values()))
        span.set_attribute("eval.routing_expected", str(scenario["expected_routing"]["agents"]))
        span.set_attribute("eval.routing_actual", str(system_response.get("agents_invoked", [])))
        span.set_attribute("eval.critical_failure", any(
            fm in system_response.get("observed_behaviors", [])
            for fm in scenario["failure_modes"]
        ))
        span.set_attribute("gen_ai.system", "your-orchestration-system")
```

### Attaching Evaluations in Phoenix

```python
import pandas as pd
from phoenix.evals import llm_classify, OpenAiModel

# Build eval dataframe from your results
eval_df = pd.DataFrame([
    {
        "context.span_id": span_id,
        "input": scenario["prompt"],
        "output": system_response["text"],
        "expected_routing": str(scenario["expected_routing"]["agents"]),
        "actual_routing": str(system_response["agents_invoked"]),
    }
    for span_id, scenario, system_response in results
])

# Log evaluations back to Phoenix
px.Client().log_evaluations(
    evaluations=eval_df,
    evaluation_name="orch_eval_routing_accuracy",
)
```

### Recommended Phoenix Dashboard Panels

1. **Routing accuracy by category** — heatmap of correct vs. incorrect routing decisions
2. **Latency vs. score scatter** — identify speed/quality tradeoffs per category
3. **Failure mode frequency** — bar chart of most common failure modes across all runs
4. **Dimension correlation** — does clarification quality correlate with routing accuracy?

---

## 3. Generic OpenTelemetry Collector

For teams using Jaeger, Grafana Tempo, Honeycomb, or a custom collector:

### Minimal OTEL Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]))
)
trace.set_tracer_provider(provider)
```

### Semantic Conventions

Follow the [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) for LLM spans, supplemented by the `eval.*` attributes defined in the table above.

```
span name:        orch_eval.scenario.{scenario_id}
span kind:        CLIENT
gen_ai.system:    {orchestration framework name}
gen_ai.request.*: (model, temperature, max_tokens if applicable)
eval.*:           (all attributes from the table above)
```

---

## 4. CI/CD Integration

Run the evaluation matrix automatically on pull requests to prevent routing regression.

### GitHub Actions Example

```yaml
# .github/workflows/orch-eval.yml
name: Orchestration Evaluation
on:
  pull_request:
    branches: [main]

jobs:
  orch-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run orch-eval matrix
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          ORCH_API_ENDPOINT: ${{ secrets.ORCH_API_ENDPOINT }}
        run: |
          python eval_runner.py \
            --config examples/sample_run_config.yaml \
            --output results/pr-${{ github.event.pull_request.number }}.json

      - name: Check pass threshold
        run: |
          python -c "
          import json, sys
          r = json.load(open('results/pr-${{ github.event.pull_request.number }}.json'))
          score = r['total_score']
          threshold = 850
          print(f'Score: {score}/1000')
          if score < threshold:
              print(f'FAIL: score {score} below threshold {threshold}')
              sys.exit(1)
          print('PASS')
          "

      - name: Upload results artifact
        uses: actions/upload-artifact@v4
        with:
          name: orch-eval-results
          path: results/
```

### Environment Variables

| Variable | Purpose |
|---|---|
| `ORCH_EVAL_PASS_THRESHOLD` | Override default pass threshold (850) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | Langfuse project secret key |
| `LANGFUSE_HOST` | Langfuse host (default: cloud.langfuse.com) |
| `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix/Arize OTLP endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Generic OTLP collector endpoint |

---

## 5. Regression Alerting

Set up alerts when evaluation scores degrade between runs:

```python
# After each run, compare to previous run stored in Langfuse/your DB
def check_regression(current_score: float, previous_score: float, threshold_pct: float = 5.0):
    delta_pct = ((previous_score - current_score) / previous_score) * 100
    if delta_pct > threshold_pct:
        raise ValueError(
            f"Regression detected: score dropped {delta_pct:.1f}% "
            f"({previous_score:.0f} → {current_score:.0f}). "
            f"Threshold: {threshold_pct}%"
        )
```

Per `scoring/thresholds.json`: a drop exceeding **5%** from the previous evaluation run should block deployment and trigger a root cause investigation.
