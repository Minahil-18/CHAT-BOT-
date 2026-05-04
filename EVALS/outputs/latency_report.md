# Person C - Latency Benchmark

## Status

| Key | Value |
|---|---|
| status | ok |
| skip_reason | None |
| ollama_up | True |

## Hardware

| Key | Value |
|---|---|
| os | Windows |
| os_version | 10.0.26200 |
| machine | AMD64 |
| processor | AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD |
| python_version | 3.11.9 |
| cpu_count_logical | 12 |
| cpu_count_physical | 6 |
| ram_total_gb | 15.27 |
| disk_total_gb | 330.39 |

## Scenario: tool_only

Single tool call (weather) with structured response (no LLM).

## Summary

| Key | Value |
|---|---|
| trials | 30 |
| successes | 30 |
| failures | 0 |

## TTFT (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 785.312 |
| median | 769.01 |
| p90 | 875.139 |
| p99 | 983.908 |
| min | 661.476 |
| max | 1021.36 |

## Inter-token (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 9.095 |
| median | 9.111 |
| p90 | 9.274 |
| p99 | 9.561 |
| min | 8.672 |
| max | 9.585 |

## E2E (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 1593.701 |
| median | 1597.346 |
| p90 | 1781.093 |
| p99 | 1839.737 |
| min | 1368.255 |
| max | 1855.293 |

## Scenario: rag_only

Knowledge retrieval for travel tips using RAG documents.

## Summary

| Key | Value |
|---|---|
| trials | 30 |
| successes | 30 |
| failures | 0 |

## TTFT (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 757.953 |
| median | 755.832 |
| p90 | 803.515 |
| p99 | 890.808 |
| min | 620.376 |
| max | 900.794 |

## Inter-token (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 8.597 |
| median | 8.604 |
| p90 | 8.754 |
| p99 | 8.81 |
| min | 8.296 |
| max | 8.82 |

## E2E (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 4290.068 |
| median | 4371.072 |
| p90 | 5019.841 |
| p99 | 5095.985 |
| min | 2834.886 |
| max | 5108.111 |

## Scenario: rag_plus_tool

Combined RAG retrieval + tool call (e.g. food recommendations + weather).

## Summary

| Key | Value |
|---|---|
| trials | 30 |
| successes | 30 |
| failures | 0 |

## TTFT (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 772.311 |
| median | 769.311 |
| p90 | 816.598 |
| p99 | 929.85 |
| min | 588.159 |
| max | 947.058 |

## Inter-token (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 8.709 |
| median | 8.691 |
| p90 | 8.845 |
| p99 | 8.902 |
| min | 8.52 |
| max | 8.915 |

## E2E (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 2723.493 |
| median | 2650.793 |
| p90 | 3492.627 |
| p99 | 4229.453 |
| min | 1988.234 |
| max | 4362.611 |

## Scenario: full_pipeline

Full itinerary request triggering RAG, tools, and narrative LLM generation.

## Summary

| Key | Value |
|---|---|
| trials | 30 |
| successes | 30 |
| failures | 0 |

## TTFT (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 1119.707 |
| median | 1130.592 |
| p90 | 1159.942 |
| p99 | 1181.263 |
| min | 748.549 |
| max | 1185.83 |

## Inter-token (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 8.474 |
| median | 8.474 |
| p90 | 8.593 |
| p99 | 8.671 |
| min | 8.32 |
| max | 8.684 |

## E2E (ms)

| Key | Value |
|---|---|
| n | 30 |
| mean | 4493.993 |
| median | 5289.527 |
| p90 | 5341.385 |
| p99 | 5406.79 |
| min | 1587.862 |
| max | 5412.44 |
