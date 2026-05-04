# Person C - Throughput Benchmark

## Status

| Key | Value |
|---|---|
| status | ok |
| skip_reason | None |
| max_sustainable_concurrency | 6 |
| breakpoint_concurrency | 8 |

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

## Results

| Concurrency | Turns/s | Errors | Median TTFT (ms) | Median E2E (ms) |
|---:|---:|---:|---:|---:|
| 1 | 0.262 | 0 | 919.764 | 1651.387 |
| 2 | 0.492 | 0 | 1011.147 | 1701.451 |
| 4 | 0.846 | 0 | 1199.293 | 1875.88 |
| 6 | 1.0 | 0 | 1836.6 | 2427.819 |
| 8 | 1.058 | 0 | 3155.734 | 3855.356 |
