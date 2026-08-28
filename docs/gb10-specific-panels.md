# Why these 17 panels are specific to GB10 (and how to verify it)

An upstream awesome-list maintainer asked for something **specific to GB10** rather
than a stack that merely *runs on* a GB10. This page is the reproducible argument:
three of the seventeen panels exist because of the GB10 hardware itself, and each
one can be checked on your own DGX Spark in a few commands.

The dashboard is **17 panels = 14 generic + 3 GB10-specific**. The generic fourteen
(DCGM power/utilization/temperature/clock, node CPU/memory/disk/network, vLLM
throughput/KV-cache/latency) are what any NVIDIA GPU host would show. The three
below are the ones an x86 + NVIDIA GPU host *cannot* render the same way.

---

## 1. GB10 unified memory (128 GB CPU+GPU shared)

**Why it is GB10-specific.** DGX Spark has **one shared LPDDR5X pool** — the Grace
CPU and the Blackwell GPU address the same 128 GB. There is no separate VRAM
dimension, which is exactly why the DCGM exporter on GB10 **exposes no
`DCGM_FI_DEV_FB_*` (frame-buffer) series at all**. An x86 NVIDIA host always has
`DCGM_FI_DEV_FB_USED/FREE/TOTAL`; a GB10 does not. The panel therefore watches the
unified pool via `node_memory_*` (total fixed at 128 GB, used = CPU+GPU combined)
and does not draw a "VRAM" line that would be a lie on this machine.

**Verify it yourself:**

```bash
# 1. GB10 exposes no FB series:
curl -s --data-urlencode 'match[]={__name__=~".*FB.*"}' \
  http://localhost:9090/api/v1/series
#    -> empty result on GB10 (try the same on any x86 NVIDIA host: non-empty)

# 2. The unified pool is one 128 GB block:
curl -s 'http://localhost:9090/api/v1/query?query=node_memory_MemTotal_bytes' | jq .
#    -> ~137,438,953,472 bytes (~128 GiB) per node
```

---

## 2. SM clock vs the 2200 MHz software clock-cap (silicon max 3003 MHz)

**Why it is GB10-specific.** GB10 has a nominal/allowed SM ceiling of **3003 MHz**,
and the recommended day-to-day thermal practice for the desktop form factor is a
**software clock cap at 2200 MHz**:

```bash
sudo nvidia-smi -i 0 -lgc 0,2200      # cap
sudo nvidia-smi -i 0 -rgc             # restore
```

The panel plots the live `DCGM_FI_DEV_SM_CLOCK` against two dashed reference lines:
**2200 MHz (the cap) and 3003 MHz (the silicon max)**. On the reference captures
the two GPUs sit at ~2184/2177 MHz under the cap — a level an x86 GPU would have no
reason to show. This is a GB10-specific operating envelope, not a generic metric.

**Measured trade-off of the cap (our two-node cluster, A/B):** peak temperature
↓ 8–12 °C, GPU-rail power ≈ −36 %, decode within noise, cold-prefill ≈ +3.9 %,
overall ≈ −1.34 %. (Rerun on your hardware after any driver/mirror revision; the
dashboard gives you the two axes to see it live.)

**Verify it yourself:**

```bash
# Is the cap applied?
nvidia-smi --query-gpu=index,clocks.current.graphics,clocks.max.graphics \
  --format=csv,noheader
#    -> current ≈ 2xxx (capped) while max = 3003 on GB10

# Live clock + both reference lines are visible in the "SM Clock vs GB10 2200 MHz 锁频" panel.
```

---

## 3. GB10 power–temperature co-plot (the cap's thermal/energy trade-off)

**Why it is GB10-specific.** Power and temperature are plotted on two axes in one
panel so the **2200 MHz cap's trade-off is visible in a single view** — the exact
quantity the second panel describes numerically is observed on the graph itself.
This co-plot only makes sense in the context of the GB10 cap discussion; on a
rackmount GPU it is just two unrelated lines.

**Verify it yourself:** run the stack, apply the cap (`-lgc 0,2200`), and watch the
power–temperature panel move together while `clocks.current.graphics` holds at
~2.2 GHz.

---

## Reproducible environment for the screenshots

The screenshots in this repo (`docs/dashboard-*.png`) were captured from a live
**two-node DGX Spark cluster** (2× GB10, 200 Gb/s RoCE fabric, TP=2 serving
DeepSeek V4 Flash with NVFP4 ML-A KV cache):

- `dashboard-preview.png` — all 17 panels
- `dashboard-gb10.png` — the three GB10-specific panels close-up
- `dashboard-gpu.png` / `dashboard-system.png` / `dashboard-inference.png` — the 14 generic panels

Data sources are the stock, unmodified open-source exporters (DCGM exporter,
node_exporter, vLLM `/metrics`) scraped by Prometheus into the bundled Grafana
dashboard — all the JSON in this repo is original work.

---

*NVIDIA, DGX, and GB10 are trademarks of NVIDIA Corporation. This project is not
affiliated with or endorsed by NVIDIA.*
