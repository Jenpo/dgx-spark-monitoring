#!/usr/bin/env bash
# DGX Spark 集群监控栈 一键安装
# 用法: ./install.sh [start|stop|restart|status|logs]
set -euo pipefail

cd "$(dirname "$0")"

# ---- 读取 .env (可选) ----
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

SPARK_NODE1_HOST="${SPARK_NODE1_HOST:-127.0.0.1}"
SPARK_NODE2_HOST="${SPARK_NODE2_HOST:-}"
VLLM_HOST="${VLLM_HOST:-}"
PROM_RETENTION="${PROM_RETENTION:-30d}"
GRAFANA_ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"

# ---- 渲染 prometheus 运行时配置 ----
python3 - "$SPARK_NODE1_HOST" "$SPARK_NODE2_HOST" "$VLLM_HOST" <<'PY'
import os, sys
node1, node2, vllm = sys.argv[1], sys.argv[2], sys.argv[3]
jobs = []
jobs.append(f"""  # DGX Spark node 1
  - job_name: 'dcgm-spark-001'
    static_configs:
      - targets: ['{node1}:9400']
        labels:
          node: spark-001
  - job_name: 'node-spark-001'
    static_configs:
      - targets: ['{node1}:9100']
        labels:
          node: spark-001
""")
if node2:
    jobs.append(f"""  # DGX Spark node 2
  - job_name: 'dcgm-spark-002'
    static_configs:
      - targets: ['{node2}:9400']
        labels:
          node: spark-002
  - job_name: 'node-spark-002'
    static_configs:
      - targets: ['{node2}:9100']
        labels:
          node: spark-002
""")
if vllm:
    jobs.append(f"""  # vLLM 推理服务
  - job_name: 'vllm'
    static_configs:
      - targets: ['{vllm}:8888']
        labels:
          node: vllm
""")
content = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
""" + "\n".join(jobs)
open('prometheus/prometheus.runtime.yml', 'w').write(content)
print("✓ 已生成 prometheus/prometheus.runtime.yml")
print("  node1=%s  node2=%s  vllm=%s" % (node1 or '(本机)', node2 or '(未启用)', vllm or '(未启用)'))
PY

cmd="${1:-start}"
case "$cmd" in
  start)
    echo "▶ 启动 DGX Spark 监控栈..."
    docker compose up -d
    echo ""
    echo "✅ 监控栈已启动:"
    echo "   Grafana    http://localhost:3000   (${GRAFANA_ADMIN_USER} / ${GRAFANA_ADMIN_PASSWORD})"
    echo "   Prometheus http://localhost:9090"
    echo ""
    echo "   首次启动后 Grafana 会自动导入 'DGX Spark 集群监控' 仪表盘"
    ;;
  stop)
    docker compose down
    ;;
  restart)
    docker compose restart
    ;;
  status)
    docker compose ps
    ;;
  logs)
    docker compose logs -f --tail=100
    ;;
  *)
    echo "用法: ./install.sh [start|stop|restart|status|logs]"
    ;;
esac
