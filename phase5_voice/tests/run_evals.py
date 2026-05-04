import subprocess
import sys
import os
from pathlib import Path

def run_script(script_path: Path, description: str):
    print(f"\n[{description}]")
    print(f"Running {script_path.name}...")
    
    if not script_path.exists():
        print(f"Error: {script_path} not found.")
        return 1

    env = os.environ.copy()
    # Add project root to PYTHONPATH so imports work correctly
    repo_root = Path(__file__).parent.resolve()
    env["PYTHONPATH"] = str(repo_root)
    env["PYTHONIOENCODING"] = "utf-8"

    # Change cwd to the script's directory for tests that rely on local relative paths
    cwd = script_path.parent

    result = subprocess.run([sys.executable, str(script_path)], env=env, cwd=str(cwd))
    
    if result.returncode != 0:
        print(f"Warning: {script_path.name} exited with code {result.returncode}")
    else:
        print(f"Successfully ran {script_path.name}")
    return result.returncode

def main():
    # repo root is 2 levels up from phase5_voice/tests/
    repo_root = Path(__file__).parent.parent.parent.resolve()
    
    print("="*60)
    print("TRAVEL BUDDY UNIFIED EVALUATION ORCHESTRATOR")
    print("="*60)
    
    # Person A: RAG & Correctness
    script_a_rag = repo_root / "phase5_voice" / "tests" / "test_rag_eval.py"
    run_script(script_a_rag, "Phase 1: RAG Correctness Evaluation (Person A)")
 
    script_a_faith = repo_root / "phase5_voice" / "tests" / "test_faithfulness.py"
    run_script(script_a_faith, "Phase 2: RAG Faithfulness Evaluation (Person A)")
 
    # Person B: CRM & Tools
    script_b = repo_root / "phase5_voice" / "tests" / "run_person_b_tests.py"
    run_script(script_b, "Phase 3: Tool & CRM Testing Suite (Person B)")
 
    # Person C: Performance & Load Testing
    script_c = repo_root / "EVALS" / "run_person_c.py"
    run_script(script_c, "Phase 4: Performance Testing (Latency & Throughput) (Person C)")
 
    # Graph Generation
    script_graphs = repo_root / "EVALS" / "graph_generator.py"
    run_script(script_graphs, "Phase 5: Graph Generation")
 
    # Final Unified Report
    script_report = repo_root / "EVALS" / "report_generator.py"
    run_script(script_report, "Phase 6: Master Markdown Report Compilation")

    print("\n" + "="*60)
    print("EVALUATION ORCHESTRATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
