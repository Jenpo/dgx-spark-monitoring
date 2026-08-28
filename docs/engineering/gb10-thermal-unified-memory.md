# Running a DGX Spark without burning it: the 2200 MHz cap and the 128 GiB that is not VRAM

*Engineering field notes from a two-node GB10 cluster serving DeepSeek V4 Flash (TP=2, NVFP4 ML-A KV cache). All numbers below are from real `nvidia-smi` / DCGM captures, not marketing.*

A GB10 desktop unit is quiet and sits on a desk. It also runs 128 GB of unified LPDDR5X at close to its silicon limit by default, and the two things people get wrong about it are both visible in telemetry before they become a problem.

## The 3003 MHz trap

The hardware ceiling on `clocks.max.graphics` is 3003 MHz. A fresh unit boots there, and for short bursts that is fine. Leave a heavy vLLM serving load running for hours and the GPU rides a thin line between full clock and thermal throttle — you pay for the oscillation in latency variance, not in throughput.

`nvidia-smi -i 0 -lgc 0,2200` is the recommended day-to-day cap for good reason. On our pair, the numbers were:

| metric | uncapped | capped at 2200 MHz |
|---|---|---|
| peak GPU temp | +8–12 °C higher | base 66–71 °C under load |
| GPU rail power | baseline (45–48 W idle) | ≈ 29 W idle, rail ≈ −36 % |
| SM clock | 2489 / 2515 MHz | 2184 / 2177 MHz |
| decode throughput | baseline | within noise |
| cold prefill | baseline | ≈ +3.9 % |

Calling that a "1.34 % penalty" (our synthetic overall cost) is defensible, but it undersells what you buy: the power rail drops roughly a third and headroom for temperature stops being a coin flip during a 1 M-token prefill. For a long-running inference host, the cap is a decision, not a sacrifice. `-rgc` brings it back if you know you are about to run a short burst benchmark.

The catch is durability: the cap **does not survive a reboot**. Every driver reload or restart silently drops you back to 3003. Our monitoring dashboard draws a reference line at 2200 so a drifted machine is visible the moment it comes back.

## The 128 GiB that has no VRAM column

x86 GPU monitoring conventions do not survive GB10. There is **no frame buffer** to graph. DCGM exporter on GB10 exposes **no `DCGM_FI_DEV_FB_*` series at all**:

```bash
curl -s --data-urlencode 'match[]={__name__=~".*FB.*"}' \
  http://localhost:9090/api/v1/series   # -> empty on GB10
```

Run that on an x86 NVIDIA host and it is non-empty. The Grace CPU and the Blackwell GPU share one LPDDR5X pool (`node_memory_MemTotal_bytes` ≈ 137,438,953,472 = 128 GiB per node). What that means operationally:

- Watch `MemTotal - MemAvailable`, not "GPU memory". A model that is resident *and* the host OS both tax the same pool.
- A "VRAM full" panel asks a question GB10 cannot answer. The panel that works reads the unified pool directly and does not pretend otherwise.
- Swap is real: `node_memory_Swap*` moves on GB10 in a way it rarely does on a box with dedicated HBM.

## Verify it on yours in five commands

Does not require our stack — just `nvidia-smi` and Prometheus if you have one:

```bash
# 1. is the cap still applied after reboot?
nvidia-smi --query-gpu=index,clocks.current.graphics,clocks.max.graphics --format=csv,noheader
# 2. power/temp under a real load
nvidia-smi --query-gpu=index,temperature.gpu,power.draw --format=csv,noheader
# 3. no FB series (unified memory, no VRAM)
curl -s --data-urlencode 'match[]={__name__=~".*FB.*"}' http://localhost:9090/api/v1/series
# 4. unified pool is one 128 GiB block
curl -s 'http://localhost:9090/api/v1/query?query=node_memory_MemTotal_bytes'
```

If you want the full picture without touching hardware at all, the [dashboard repo](https://github.com/Jenpo/dgx-spark-monitoring) ships a mock exporter (`docker-compose.mock.yml`) that replays a synthetic capped pair, because the panels that matter — clock vs cap, unified-memory, power–temperature on one axis — are GB10-shaped questions, not NVIDIA-generic ones.

*First published in the DGX Spark monitoring notes. Data captured 2026-08 on a 2× GB10 cluster; rerun after driver/mirror changes — numbers here are observations, not guarantees.*
