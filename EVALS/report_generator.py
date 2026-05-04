import os
from pathlib import Path

def get_markdown_content(filepath: Path) -> list:
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # If the first line is a `# ` heading, we might keep it or strip it depending on preference.
            # Here we just keep all lines.
            return [line.rstrip() for line in lines]
    return [f"*{filepath.name} not found.*"]

def main():
    base_dir = Path(__file__).parent.resolve()
    root_dir = base_dir.parent
    reports_dir = root_dir / "phase5_voice" / "reports"
    
    out_dir = base_dir / "outputs"
    
    latency_md = out_dir / "latency_report.md"
    throughput_md = out_dir / "throughput_report.md"
    latency_png = out_dir / "latency_bar_chart.png"
    throughput_png = out_dir / "throughput_line_chart.png"
    
    final_report = root_dir / "Report" / "FINAL_EVALUATION_REPORT.md"
    
    content = []
    content.append("# FINAL EVALUATION REPORT: Conversational AI System")
    content.append("\n**Date:** 2026-05-02")
    content.append("**Status:** ✅ COMPLETE (Ready for Submission)\n")
    content.append("---\n")
    
    # ---------------- PERSON A ----------------
    content.append("## PART 1: Correctness & Component Evaluation (Person A)\n")
    person_a_md = reports_dir / "evaluation_report_PersonA.md"
    content.extend(get_markdown_content(person_a_md))
    content.append("\n---\n")

    # ---------------- PERSON B ----------------
    content.append("## PART 2: Tool & CRM Component Testing (Person B)\n")
    person_b_md = reports_dir / "tool_report_PersonB.md"
    content.extend(get_markdown_content(person_b_md))
    content.append("\n---\n")

    # ---------------- PERSON C ----------------
    content.append("## PART 3: Performance & Automation Evaluation (Person C)\n")
    content.append("This section summarizes the performance evaluation, covering latency testing (TTFT, Inter-token, E2E) and load testing (throughput, concurrency).\n")
    
    content.append("### 3.1 Latency Benchmark\n")
    if latency_md.exists():
        with open(latency_md, "r", encoding="utf-8") as f:
            md_lines = f.readlines()
            if md_lines and md_lines[0].startswith("# Person C"):
                md_lines = md_lines[1:]
            content.extend([line.rstrip() for line in md_lines])
    else:
        content.append("*Latency report markdown not found.*")
        
    content.append("\n#### Latency Chart\n")
    rel_latency_png = "EVALS/outputs/latency_bar_chart.png"
    if latency_png.exists():
        content.append(f"![Latency Bar Chart]({rel_latency_png})")
    else:
        content.append("*Latency chart not generated.*")

    content.append("\n### 3.2 Throughput & Load Testing Benchmark\n")
    if throughput_md.exists():
        with open(throughput_md, "r", encoding="utf-8") as f:
            md_lines = f.readlines()
            if md_lines and md_lines[0].startswith("# Person C"):
                md_lines = md_lines[1:]
            content.extend([line.rstrip() for line in md_lines])
    else:
        content.append("*Throughput report markdown not found.*")
        
    content.append("\n#### Throughput Chart\n")
    rel_throughput_png = "EVALS/outputs/throughput_line_chart.png"
    if throughput_png.exists():
        content.append(f"![Throughput Line Chart]({rel_throughput_png})")
    else:
        content.append("*Throughput chart not generated.*")
        
    content.append("\n### 3.3 Automation Details\n")
    content.append("- **Orchestrator**: `run_evals.py` at the root automatically runs all correctness tests, latency and throughput suites, invokes the graphing script, and compiles this unified final report.\n")
    content.append("- **WebSocket Client**: Uses an asynchronous `websockets` implementation to emulate real-time typing and streaming from multiple concurrent users.\n")
    
    with open(final_report, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
        
    print(f"Generated unified final evaluation report at: {final_report}")

if __name__ == "__main__":
    main()
