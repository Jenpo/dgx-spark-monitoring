# DGX Spark 集群监控栈（中文说明）

> **一条命令监控 NVIDIA DGX Spark（GB10）集群** —— DCGM GPU 指标、节点系统指标、vLLM 推理遥测，配好开箱即用的 Grafana 仪表盘。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

为你的 **NVIDIA DGX Spark / GB10** 集群搭建监控，几分钟搞定。无需手动拼接面板，拉取代码、跑一个脚本即可获得：

- 🎛️ **DCGM GPU 遥测** —— 功耗、利用率、显存/引擎利用率、温度、SM 时钟、累计能耗
- 🖥️ **节点系统指标** —— CPU 温度与负载、内存、磁盘、网络带宽
- 🤖 **vLLM 推理遥测** —— 吞吐（tok/s）、KV Cache 占用、请求队列、TPOT/TTFT 延迟
- 🌐 **多节点就绪** —— 一个仪表盘监控两台（或多台）GB10 节点
- 🔒 **GB10 特有遥测** —— 128GB CPU+GPU 统一内存、2200 MHz 锁频散热工程、GB10 功耗–温度联动

---

## ✨ 为什么是 GB10 特有（而非“能在 GB10 上跑”）

通用 NVIDIA 监控栈在任何 x86 主机上渲染的都是同一套曲线。这个仪表盘有意做成 **GB10 专属**：

- **128GB 统一内存，而非“显存 + 主机内存”。** DGX Spark 只有一个共享 LPDDR5X 内存池（Grace CPU + Blackwell GPU 共用）。*GB10 统一内存* 面板直接监控这个池子——GB10 根本不暴露独立的 `DCGM_FI_DEV_FB_*` 帧缓冲指标（已在真机上验证）。
- **2200 MHz 锁频散热工程。** GB10 推荐的软件锁频（`nvidia-smi -i 0 -lgc 0,2200`，硬件上限 3003 MHz）是保持桌面超级计算机冷静的关键杠杆。*SM Clock vs 2200 锁频* 面板同时画出当前时钟、锁频线和硅上限线；*功耗–温度* 面板双轴联动，一眼看清华氏权衡。
- **双机 200Gb/s 互联部署。** 通过 RoCE 织网扩展到第二台 GB10、张量并行推理是 DGX Spark 的一等公民用法；整个栈给每台节点/每块 GPU 打 tag，1–N 台 Spark 汇总到一个 Prometheus。

---

## 🎯 功能特性

- **GPU 温度与热监控** —— 在影响推理前发现过热降频（核心 + 显存 °C）
- **GPU 利用率与功耗监控** —— 基于 DCGM 的利用率、功耗、SM 时钟实时监控
- **LLM 推理可观测性** —— vLLM 吞吐（tok/s）、KV Cache 占用、请求队列、TPOT/TTFT 延迟
- **完整节点健康** —— CPU 负载、内存与 Swap、磁盘可用空间、网络带宽
- **仪表盘自动导入** —— 17 个预置 Grafana 面板（14 通用 + 3 GB10 特有），零手动配置
- **多节点集群支持** —— 从一个 Prometheus + Grafana 监控 1–N 台 DGX Spark GB10 节点
- **一键 Docker 安装** —— `./install.sh start` 即刻上线
- **无厂商锁定** —— 标准 Prometheus + Grafana + DCGM exporter + node_exporter

<p align="center">
  <img src="docs/dashboard-preview.png" alt="DGX Spark 集群监控仪表盘预览" width="850">
  <br/><i>DGX Spark 集群监控仪表盘 —— 17 个面板一键导入 Grafana</i>
</p>

#### GB10 特有面板特写

<p align="center">
  <img src="docs/dashboard-gb10.png" alt="GB10 特有面板：统一内存 / 时钟锁频 / 功耗温度" width="850">
  <br/><i>GB10 特有面板：统一内存 / 2200 MHz 锁频 / 功耗–温度联动（图为真实双机实采数据）</i>
</p>

#### GPU / 系统 / 推理面板特写

<p align="center">
  <img src="docs/dashboard-gpu.png" alt="GPU 遥测面板" width="850">
  <img src="docs/dashboard-system.png" alt="节点系统面板" width="850">
  <img src="docs/dashboard-inference.png" alt="vLLM 推理面板" width="850">
  <br/><i>GPU 遥测 / 节点系统 / vLLM 推理 面板细节</i>
</p>

---

## ✨ 为什么要用

DGX Spark（GB10）把强大的 AI 算力装进桌面。这个监控栈回答你真正关心的问题：

- *GPU 是不是过热降频了？* → **GPU 温度 & SM 时钟** 面板
- *我的 vLLM 服务是不是瓶颈？* → **吞吐、KV Cache、延迟** 面板
- *集群健康吗？* → **负载、内存、磁盘、网络** 面板

全部封装成**预接线 Grafana 仪表盘**（`DGX Spark 集群监控`），首次启动自动导入。

---

## 🚀 快速开始

**前置条件：** Docker + Docker Compose，NVIDIA Container Toolkit（供 DCGM exporter 使用），以及每台被监控节点上的对应环境。

```bash
# 1. 克隆
git clone https://github.com/Jenpo/dgx-spark-monitoring.git
cd dgx-spark-monitoring

# 2. （可选）配置节点
cp .env.example .env   # 设置 SPARK_NODE1_HOST / SPARK_NODE2_HOST / VLLM_HOST

# 3. 一键安装
./install.sh start

# 4. 打开仪表盘
#    Grafana    http://localhost:3000   (admin / admin)
#    Prometheus http://localhost:9090
```

> ⚠️ 在**第二台** DGX Spark（node 2）上，只需跑 exporter：
> ```bash
> docker run -d --runtime=nvidia --network=host --name dcgm-node2 nvidia/dcgm-exporter:3.3.5-1.4.0-ubuntu22.04
> docker run -d --network=host --pid=host --name node-exp2 prom/node-exporter:v1.8.1
> ```

就这样 —— **"DGX Spark 集群监控"** 仪表盘会自动加载 17 个预置面板。

> 💡 Grafana 10 首次用默认 `admin/admin` 登录会强制要求改密。若希望保持默认账密（脚本/无人值守场景），给 Grafana 服务加环境变量即可跳过：
> `GF_SECURITY_DISABLE_INITIAL_ADMIN_PASSWORD_CHANGE=true`

---

## 📊 仪表盘面板

| 指标 | 面板 |
|---|---|
| GPU 功耗 (W) | `DCGM_FI_DEV_POWER_USAGE` |
| GPU 利用率 (%) | `DCGM_FI_DEV_GPU_UTIL` |
| 引擎利用率（显存拷贝/解码/编码 %） | `DCGM_FI_DEV_MEM_COPY_UTIL` / `_DEC_` / `_ENC_` |
| GPU 温度（核心/显存 °C） | `DCGM_FI_DEV_GPU_TEMP` / `_MEMORY_TEMP` |
| SM 时钟 (MHz) | `DCGM_FI_DEV_SM_CLOCK` |
| 累计能耗 (mWh) | `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` |
| CPU 温度（最高/平均 °C） | `node_thermal_zone_temp` |
| 负载 & CPU 使用率 | `node_load1/5/15` |
| 内存 / Swap | `node_memory_*` |
| 磁盘可用空间 | `node_filesystem_avail_bytes` |
| 网络带宽 (B/s) | `node_network_*` |
| 推理吞吐 (tok/s) | `vllm:*_tokens_total` |
| KV Cache & 请求队列 | `vllm:kv_cache_usage_perc` / `num_requests_*` |
| 延迟（TPOT/TTFT/排队） | `vllm:inter_token_latency` / `request_prefill` / `request_queue` |
| **GB10 统一内存 (128GB CPU+GPU 共享)** | `node_memory_MemTotal/Available` — 一体池语义，无独立 FB |
| **SM Clock vs GB10 2200 MHz 锁频** | `DCGM_FI_DEV_SM_CLOCK` + 2200 cap / 3003 max 参考线 |
| **GB10 功耗–温度 (锁频热设计)** | `DCGM_FI_DEV_POWER_USAGE` × `DCGM_FI_DEV_GPU_TEMP` 双轴 |

---

## 🔧 配置

所有配置项都在 **`.env`**（从 `.env.example` 复制）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SPARK_NODE1_HOST` | `127.0.0.1` | 主节点 / 本机 |
| `SPARK_NODE2_HOST` | *（空）* | 第二台 DGX Spark（留空 = 单机） |
| `VLLM_HOST` | *（空）* | vLLM 服务地址（留空 = 不采集推理指标） |
| `PROM_RETENTION` | `30d` | Prometheus 数据保留时长 |
| `GRAFANA_ADMIN_USER` / `PASSWORD` | `admin` / `admin` | Grafana 登录账号 |

---

## 📁 项目结构

```
dgx-spark-monitoring/
├── docker-compose.yml                 # 一键栈
├── install.sh                         # start / stop / status / logs
├── .env.example                       # 节点与认证配置
├── prometheus/
│   └── prometheus.yml                 # 抓取模板（安装时渲染）
├── grafana/
│   └── provisioning/                  # 自动数据源 + 仪表盘导入
│       ├── datasources/datasource.yml
│       └── dashboards/dgx-spark-cluster.json   # 17 面板仪表盘（14 通用 + 3 GB10 特有）
├── exporters/                         # node 2 手动部署 exporter
└── donate/                            # 微信 & 支付宝打赏收款码
```

---

## 💚 支持与打赏

如果这个项目帮到你，欢迎请喝一杯咖啡：

<p align="center">
  <img src="donate/wechat-qr.jpg" width="180" alt="微信支付" title="微信支付">
  <img src="donate/alipay-qr.jpg" width="180" alt="支付宝" title="支付宝">
</p>

<p align="center">
  <b>微信支付</b> &nbsp;·&nbsp; <b>支付宝</b>
</p>

> ⚠️ 仓库自带的收款码为**占位图**。请将 `donate/wechat-qr.jpg` 与 `donate/alipay-qr.jpg` 替换为你自己的收款码。

---

## 📖 文档

- [English](README.md)
- 中文说明（本文件）

---

## ❓ 常见问题

**如何监控 NVIDIA DGX Spark（GB10）？**
一条命令启动 Docker 监控栈，自动拉起 DCGM exporter、node_exporter、Prometheus 和 Grafana，并预置 17 面板仪表盘。见[快速开始](#-快速开始)。

**如何查看 DGX Spark 的 GPU 温度？**
打开仪表盘看 **GPU 温度（核心/显存 °C）** 面板，由 DCGM exporter 的 `DCGM_FI_DEV_GPU_TEMP` 与 `DCGM_FI_DEV_MEMORY_TEMP` 指标驱动。

**如何监控 vLLM 推理指标（吞吐/延迟）？**
在 `.env` 设置 `VLLM_HOST` 并暴露 vLLM 的 Prometheus 指标端口（默认 `8888`），仪表盘会显示吞吐（tok/s）、KV Cache 占用、请求队列、TPOT/TTFT 延迟。

**仪表盘展示哪些指标？**
GPU 功耗、利用率、引擎（显存拷贝/解码/编码）利用率、核心与显存温度、SM 时钟、累计能耗，以及节点 CPU/内存/磁盘/网络和 vLLM 推理指标。见[仪表盘面板](#-仪表盘面板)。

**可以监控多台 DGX Spark 节点吗？**
可以。在 `.env` 设置 `SPARK_NODE2_HOST` 等，栈会自动给每台节点打标签（`spark-001`、`spark-002`…），所有 GPU 汇总在一个仪表盘。

**这是 NVIDIA 官方监控的分支吗？**
不是。这是基于标准 DCGM exporter、node_exporter、Prometheus 和 Grafana 的独立开源监控栈，与 NVIDIA 无关联，亦未经其背书。

**Grafana 默认登录账号？**
`admin` / `admin`，可通过 `.env` 的 `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` 修改。

---

## 🗺️ 路线图

- [x] DCGM GPU 遥测仪表盘
- [x] 多节点（2× GB10）支持
- [x] vLLM 推理指标
- [ ] Grafana 告警规则（过热 / OOM / 磁盘）
- [ ] Kubernetes / Slurm 作业监控

---

## 📄 许可证

[MIT](LICENSE) © 2026 [Jenpo]

---

*为 NVIDIA DGX Spark（GB10）集群打造。NVIDIA、DGX、GB10 均为 NVIDIA Corporation 的商标。本项目与 NVIDIA 无关联，亦未经其背书。*
