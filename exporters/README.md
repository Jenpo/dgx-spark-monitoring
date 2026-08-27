# Exporters 部署说明（第二台 DGX Spark 节点）

监控栈主节点（运行 docker-compose 的那台）会自动启动本机的 DCGM exporter 和 node_exporter。
**第二台 DGX Spark** 需要手动跑两个 exporter，让 Prometheus 能抓取它的指标。

## 在 node 2 上执行

```bash
# 1. DCGM exporter（GPU 指标）
docker run -d \
  --runtime=nvidia \
  --network=host \
  --name dcgm-node2 \
  --restart unless-stopped \
  nvidia/dcgm-exporter:3.3.5-1.4.0-ubuntu22.04

# 2. node_exporter（系统指标）
docker run -d \
  --network=host \
  --pid=host \
  --name node-exp2 \
  --restart unless-stopped \
  prom/node-exporter:v1.8.1

# 3. 验证指标可访问（应返回 metrics）
curl http://localhost:9400/metrics   # DCGM
curl http://localhost:9100/metrics   # node
```

## 配置主节点 Prometheus 抓取 node 2

在监控栈主节点的 `.env` 中设置：

```bash
SPARK_NODE2_HOST=<node2的IP>   # 例如 192.168.31.158
```

然后重新安装：

```bash
./install.sh restart
```

## 关于 vLLM 推理指标

若你在某台节点上跑 vLLM，暴露其 Prometheus 指标端口（默认 `8888`），
在主节点 `.env` 设置：

```bash
VLLM_HOST=<vLLM所在节点IP>
```

vLLM 启动时开启指标采集：

```bash
vllm serve <model> --port 8000 \
  --metrics-port 8888 \
  --enable-metrics
```

仪表盘会自动显示推理吞吐、KV Cache、延迟面板。
