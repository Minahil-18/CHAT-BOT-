import json
import os
import matplotlib.pyplot as plt
from pathlib import Path

def generate_latency_chart(latency_file: str, output_image: str):
    if not os.path.exists(latency_file):
        print(f"Skipping latency chart: {latency_file} not found.")
        return

    with open(latency_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('status') != 'ok' or not data.get('results'):
        print("Skipping latency chart: status is not ok or no results.")
        # Create an empty placeholder image with text
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No Data: Server was unreachable', ha='center', va='center', fontsize=14)
        ax.axis('off')
        plt.savefig(output_image)
        plt.close()
        return

    results = data['results']
    scenarios = [r['scenario']['name'] for r in results]
    median_ttft = [r['ttft_ms'].get('median', 0) for r in results]
    median_e2e = [r['e2e_ms'].get('median', 0) for r in results]

    x = range(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar([pos - width/2 for pos in x], median_ttft, width, label='Median TTFT (ms)', color='skyblue')
    rects2 = ax.bar([pos + width/2 for pos in x], median_e2e, width, label='Median E2E (ms)', color='lightcoral')

    ax.set_ylabel('Latency (ms)')
    ax.set_title('Latency by Scenario')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.0f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.savefig(output_image)
    plt.close()
    print(f"Latency chart saved to {output_image}")

def generate_throughput_chart(throughput_file: str, output_image: str):
    if not os.path.exists(throughput_file):
        print(f"Skipping throughput chart: {throughput_file} not found.")
        return

    with open(throughput_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('status') != 'ok' or not data.get('results'):
        print("Skipping throughput chart: status is not ok or no results.")
        # Create an empty placeholder image with text
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No Data: Server was unreachable', ha='center', va='center', fontsize=14)
        ax.axis('off')
        plt.savefig(output_image)
        plt.close()
        return

    results = data['results']
    concurrency = [r['concurrency'] for r in results]
    turns_per_sec = [r['turns_per_second'] for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(concurrency, turns_per_sec, marker='o', linestyle='-', color='teal', linewidth=2)
    
    ax.set_xlabel('Concurrency (Concurrent Users)')
    ax.set_ylabel('Throughput (Turns / Second)')
    ax.set_title('Concurrency vs Throughput')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Mark sustainable concurrency if available
    max_sust = data.get('max_sustainable_concurrency')
    if max_sust is not None:
        ax.axvline(x=max_sust, color='green', linestyle='--', label=f'Max Sustainable ({max_sust})')
        ax.legend()

    fig.tight_layout()
    plt.savefig(output_image)
    plt.close()
    print(f"Throughput chart saved to {output_image}")

def main():
    base_dir = Path(__file__).parent
    out_dir = base_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    latency_json = out_dir / "latency_report.json"
    throughput_json = out_dir / "throughput_report.json"
    
    latency_png = out_dir / "latency_bar_chart.png"
    throughput_png = out_dir / "throughput_line_chart.png"
    
    generate_latency_chart(str(latency_json), str(latency_png))
    generate_throughput_chart(str(throughput_json), str(throughput_png))

if __name__ == "__main__":
    main()
