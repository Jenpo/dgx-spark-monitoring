# DGX Spark Cluster Monitoring Stack

> **One-command monitoring for NVIDIA DGX Spark (GB10) clusters** — DCGM GPU metrics, node system metrics, and vLLM inference telemetry, all in a pre-built Grafana dashboard.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-DGX%20Spark%20GB10-lightgrey)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)

Monitor your **NVIDIA DGX Spark / GB10** cluster in minutes with a ready-made **open-source Grafana dashboard**. No manual panel wiring — pull the stack, run one script, and get:

- 🎛️ **DCGM GPU telemetry** — power draw, utilization, memory/engine utilization, temperatures, SM clocks, cumulative energy
- 🖥️ **Node system metrics** — CPU temp & load, memory, disk, network bandwidth
- 🤖 **vLLM inference telemetry** — tokens/sec throughput, KV cache usage, request queue, TPOT/TTFT latency
- 🌐 **Multi-node ready** — monitor two (or more) GB10 nodes from one dashboard

---

## 🎯 Features

- **GPU temperature & thermal monitoring** — catch thermal throttling before it hurts inference (core + memory °C)
- **GPU utilization & power monitoring** — DCGM-powered utilization, power draw, and SM clocks in real time
- **LLM inference observability** — vLLM throughput (tok/s), KV cache usage, request queue, TPOT/TTFT latency
- **Full node health** — CPU load, memory & swap, disk free space, network bandwidth
- **Auto-imported dashboard** — 14 pre-built Grafana panels, zero manual configuration
- **Multi-node cluster support** — monitor 1–N DGX Spark GB10 nodes from a single Prometheus + Grafana
- **One-command Docker install** — `./install.sh start` and you're live
- **No vendor lock-in** — standard Prometheus + Grafana + DCGM exporter + node_exporter

- 🎛️ **DCGM GPU telemetry** — power draw, utilization, memory/engine utilization, temperatures, SM clocks, cumulative energy
- 🖥️ **Node system metrics** — CPU temp & load, memory, disk, network bandwidth
- 🤖 **vLLM inference telemetry** — tokens/sec throughput, KV cache usage, request queue, TPOT/TTFT latency
- 🌐 **Multi-node ready** — monitor two (or more) GB10 nodes from one dashboard

---

## ✨ Why DGX Spark Monitoring?

The DGX Spark (GB10) packs serious AI compute into a desktop. This stack answers the questions you actually ask:

- *Is my GPU thermal-throttling?* → **GPU temp & SM clock** panels
- *Is my vLLM server the bottleneck?* → **throughput, KV cache, latency** panels
- *Is the cluster healthy?* → **system load, memory, disk, network** panels

All shipped as a **pre-wired Grafana dashboard** (`DGX Spark 集群监控`) that auto-imports on first boot.

---

## 🚀 Quick Start

**Prerequisites:** Docker + Docker Compose, NVIDIA Container Toolkit (for DCGM exporter), on each node you want to monitor.

```bash
# 1. Clone
git clone https://github.com/Jenpo/dgx-spark-monitoring.git
cd dgx-spark-monitoring

# 2. (Optional) Configure nodes
cp .env.example .env   # set SPARK_NODE1_HOST / SPARK_NODE2_HOST / VLLM_HOST

# 3. One-command install
./install.sh start

# 4. Open the dashboard
#    Grafana    http://localhost:3000   (admin / admin)
#    Prometheus http://localhost:9090
```

> ⚠️ On **node 2** (second DGX Spark), run only the exporters:
> ```bash
> docker run -d --runtime=nvidia --network=host --name dcgm-node2 nvidia/dcgm-exporter:3.3.5-1.4.0-ubuntu22.04
> docker run -d --network=host --pid=host --name node-exp2 prom/node-exporter:v1.8.1
> ```

That's it — the **"DGX Spark 集群监控"** dashboard auto-loads with 14 pre-built panels.

---

## 📊 Dashboard Panels

| Metric | Panel(s) |
|---|---|
| GPU Power (W) | `DCGM_FI_DEV_POWER_USAGE` |
| GPU Utilization (%) | `DCGM_FI_DEV_GPU_UTIL` |
| Engine Util (MemCopy/Dec/Enc %) | `DCGM_FI_DEV_MEM_COPY_UTIL` / `_DEC_` / `_ENC_` |
| GPU Temp (core/mem °C) | `DCGM_FI_DEV_GPU_TEMP` / `_MEMORY_TEMP` |
| SM Clock (MHz) | `DCGM_FI_DEV_SM_CLOCK` |
| Cumulative Energy (mWh) | `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` |
| CPU Temp (max/avg °C) | `node_thermal_zone_temp` |
| Load & CPU% | `node_load1/5/15` |
| Memory / Swap | `node_memory_*` |
| Disk Free | `node_filesystem_avail_bytes` |
| Network BW (B/s) | `node_network_*` |
| Inference t/s | `vllm:*_tokens_total` |
| KV Cache & Queue | `vllm:kv_cache_usage_perc` / `num_requests_*` |
| Latency (TPOT/TTFT/queue) | `vllm:inter_token_latency` / `request_prefill` / `request_queue` |

---

## 🔧 Configuration

All knobs live in **`.env`** (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `SPARK_NODE1_HOST` | `127.0.0.1` | Main node / this host |
| `SPARK_NODE2_HOST` | *(empty)* | Second DGX Spark (blank = single node) |
| `VLLM_HOST` | *(empty)* | vLLM server (blank = no inference metrics) |
| `PROM_RETENTION` | `30d` | Prometheus data retention |
| `GRAFANA_ADMIN_USER` / `PASSWORD` | `admin` / `admin` | Grafana login |

---

## 📁 Project Structure

```
dgx-spark-monitoring/
├── docker-compose.yml                 # One-command stack
├── install.sh                         # Start / stop / status / logs
├── .env.example                       # Node & auth configuration
├── prometheus/
│   └── prometheus.yml                 # Scrape template (rendered at install)
├── grafana/
│   └── provisioning/                  # Auto datasource + dashboard import
│       ├── datasources/datasource.yml
│       └── dashboards/dgx-spark-cluster.json   # 14-panel dashboard
├── exporters/                         # Manual exporter setup for node 2
└── donate/                            # WeChat & Alipay donation QR codes
```

---

## 💚 Support & Donate

If this saves you time, a coffee is appreciated:

<p align="center">
  <img src="donate/wechat-qr.jpg" width="180" alt="WeChat Pay" title="WeChat Pay (微信支付)">
  <img src="donate/alipay-qr.jpg" width="180" alt="Alipay" title="Alipay (支付宝)">
</p>

<p align="center">
  <b>WeChat Pay (微信)</b> &nbsp;·&nbsp; <b>Alipay (支付宝)</b>
</p>

> ⚠️ The bundled QR codes are **placeholders**. Replace `donate/wechat-qr.jpg` and `donate/alipay-qr.jpg` with your own payment codes.

---

## 📖 Documentation (多语言)

- [中文说明](README.zh-CN.md)
- English (this file)

---

## ❓ FAQ

**How do I monitor NVIDIA DGX Spark (GB10)?**
Run the one-command Docker stack. It starts a DCGM exporter, node_exporter, Prometheus, and Grafana with a pre-built 14-panel dashboard. See [Quick Start](#-quick-start).

**How do I check DGX Spark GPU temperature?**
Open the dashboard and look at the **GPU 温度 (核心/显存 °C)** panel, powered by `DCGM_FI_DEV_GPU_TEMP` and `DCGM_FI_DEV_MEMORY_TEMP` metrics from the DCGM exporter.

**How do I monitor vLLM inference metrics (throughput, latency)?**
Set `VLLM_HOST` in `.env` and expose your vLLM Prometheus metrics port (default `8888`). The dashboard shows tokens/sec, KV cache usage, request queue, and TPOT/TTFT latency panels.

**Which metrics does the dashboard show?**
GPU power, utilization, engine (memcopy/decode/encode) utilization, core & memory temperature, SM clocks, cumulative energy — plus node CPU/memory/disk/network, and vLLM inference metrics. See [Dashboard Panels](#-dashboard-panels).

**Can I monitor multiple DGX Spark nodes?**
Yes. Set `SPARK_NODE2_HOST` (and more) in `.env`; the stack labels each node (`spark-001`, `spark-002`, …) so all GPUs appear in one dashboard.

**Is this a fork of NVIDIA's official monitoring?**
No. It's an independent open-source stack built on the standard DCGM exporter, node_exporter, Prometheus, and Grafana. Not affiliated with or endorsed by NVIDIA.

**What is the default Grafana login?**
`admin` / `admin`, changeable via `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` in `.env`.

---

## 🗺️ Roadmap

- [x] DGCM GPU telemetry dashboard
- [x] Multi-node (2× GB10) support
- [x] vLLM inference metrics
- [ ] Grafana alerting rules (thermal / OOM / disk)
- [ ] Kubernetes / Slurm job monitoring

---

## 📄 License

[MIT](LICENSE) © 2026 [Jenpo]

---

*Built for the NVIDIA DGX Spark (GB10) cluster. NVIDIA, DGX, and GB10 are trademarks of NVIDIA Corporation. This project is not affiliated with or endorsed by NVIDIA.*
