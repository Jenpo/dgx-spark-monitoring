#!/usr/bin/env python3
"""
mock_gb10_metrics.py — zero-dependency mock Prometheus exporter that fakes a
two-node DGX Spark (GB10) cluster so the 17-panel dashboard can be previewed
WITHOUT any NVIDIA hardware. All numbers are synthetic and clearly marked MOCK;
they mimic a 2200 MHz clock-capped, DP-ready GB10 pair (temperature ~66-71 C,
rail ~29-45 W, unified 128 GiB memory). Use with docker-compose.mock.yml.

See docs/gb10-specific-panels.md for why the panel set is GB10-specific.
"""
import http.server
import math
import time
from datetime import datetime

PORT = 9100
START = time.time()

NODES = ["spark-001", "spark-002"]

def metric(name, help, t, labels, value):
    lbl = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"# HELP {name} {help}\n# TYPE {name} {t}\n{name}{{{lbl}}} {value}\n"

def render():
    t = time.time() - START
    period = 90.0
    out = []
    # Per-node, per-GPU synthetic series. spark-001 idle-ish, spark-002 heavier load.
    for i, node in enumerate(NODES):
        gpu = "0"
        phase = (t / period + i * 0.37)
        load = (math.sin(phase * 2.3) * 0.5 + 0.5) ** 2
        sm = 2184.0 + 14.0 * math.sin(phase * 1.7)          # ~ under 2200 cap
        power = 29.0 + load * 46.0
        temp = 66.0 + load * 12.0
        util = load * 96.0
        tokens = 40.0 + load * 120.0

        out.append(metric("DCGM_FI_DEV_POWER_USAGE", "MOCK GPU power W", "gauge", {"node": node, "gpu": gpu}, round(power, 1)))
        out.append(metric("DCGM_FI_DEV_GPU_UTIL", "MOCK GPU util %", "gauge", {"node": node, "gpu": gpu}, round(util, 1)))
        for kind, base in (("MEM_COPY", 8), ("DEC", 4), ("ENC", 1)):
            out.append(metric(f"DCGM_FI_DEV_{kind}_UTIL", "MOCK engine util %", "gauge", {"node": node, "gpu": gpu}, round(base + load * 30, 1)))
        out.append(metric("DCGM_FI_DEV_GPU_TEMP", "MOCK GPU core temp C", "gauge", {"node": node, "gpu": gpu}, round(temp, 1)))
        out.append(metric("DCGM_FI_DEV_MEMORY_TEMP", "MOCK GPU mem temp C", "gauge", {"node": node, "gpu": gpu}, round(temp + 4, 1)))
        out.append(metric("DCGM_FI_DEV_SM_CLOCK", "MOCK SM clock Hz", "gauge", {"node": node, "gpu": gpu}, int(sm) * 1000_000))
        out.append(metric("DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION", "MOCK cumulative energy mWh", "counter", {"node": node, "gpu": gpu}, int(1_200_000 + t * power / 3.6)))

        out.append(metric("node_thermal_zone_temp", "MOCK cpu temp C", "gauge", {"node": node, "zone": "acpitz"}, round(temp - 8, 1)))
        out.append(metric("node_cpu_seconds_total", "MOCK cpu seconds", "counter", {"node": node, "mode": "idle", "cpu": "0"}, int((0.6 - load * 0.4) * t * 1000)))
        for n in ("1", "5", "15"):
            out.append(metric(f"node_load{n}", "MOCK load", "gauge", {"node": node}, round(2.1 + load * 3.0, 2)))
        out.append(metric("node_memory_MemTotal_bytes", "MOCK unified memory total (128 GiB)", "gauge", {"node": node}, int(128 * 1024**3)))
        out.append(metric("node_memory_MemAvailable_bytes", "MOCK mem available", "gauge", {"node": node}, int((78 - load * 30) * 1024**3)))
        out.append(metric("node_memory_SwapTotal_bytes", "MOCK swap total", "gauge", {"node": node}, int(16 * 1024**3)))
        out.append(metric("node_memory_SwapFree_bytes", "MOCK swap free", "gauge", {"node": node}, int((16 - load * 4) * 1024**3)))
        out.append(metric("node_filesystem_avail_bytes", "MOCK disk free", "gauge", {"node": node, "mountpoint": "/"}, int((video_lib_huge := (900 - load * 50)) * 1024**3)))
        out.append(metric("node_network_receive_bytes_total", "MOCK net rx", "counter", {"node": node, "device": "enp1s0f0np0"}, int(2.0e9 + t * (30 + load * 220) * 1e6)))
        out.append(metric("node_network_transmit_bytes_total", "MOCK net tx", "counter", {"node": node, "device": "enp1s0f0np0"}, int(1.2e9 + t * (20 + load * 180) * 1e6)))

        out.append(metric("vllm:generation_tokens_total", "MOCK vLLM gen tokens", "counter", {"node": node}, int(t * tokens)))
        out.append(metric("vllm:prompt_tokens_total", "MOCK vLLM prompt tokens", "counter", {"node": node}, int(t * tokens * 0.6)))
        out.append(metric("vllm:kv_cache_usage_perc", "MOCK KV cache %", "gauge", {"node": node}, round(55 + load * 38, 1)))
        out.append(metric("vllm:num_requests_running", "MOCK req running", "gauge", {"node": node}, int(1 + load * 4)))
        out.append(metric("vllm:num_requests_waiting", "MOCK req waiting", "gauge", {"node": node}, int(load * 3)))
        out.append(metric("vllm:inter_token_latency_seconds_sum", "MOCK TPOT sum", "counter", {"node": node}, t * (0.03 + load * 0.05)))
        out.append(metric("vllm:inter_token_latency_seconds_count", "MOCK TPOT count", "counter", {"node": node}, int(t * tokens / 60)))
        out.append(metric("vllm:request_prefill_time_seconds_sum", "MOCK TTFT sum", "counter", {"node": node}, t * 1.2))
        out.append(metric("vllm:request_prefill_time_seconds_count", "MOCK TTFT count", "counter", {"node": node}, int(t / 90 + 1)))
        out.append(metric("vllm:request_queue_time_seconds_sum", "MOCK queue sum", "counter", {"node": node}, t * 0.4))
        out.append(metric("vllm:request_queue_time_seconds_count", "MOCK queue count", "counter", {"node": node}, int(t / 90 + 1)))
    out.append(metric("mock_gb10_info", "MOCK synthetic data indicator (never from real hardware)", "gauge", {"note": "MOCK"}, 1.0))
    return "".join(out)

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/metrics"):
            body = render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/health"):
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"MOCK GB10 metrics exporter on :{PORT} (all values synthetic)", flush=True)
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
