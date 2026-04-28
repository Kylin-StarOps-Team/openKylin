# StarOps

**AI-Powered Intelligent System Monitoring Assistant**
**智能系统监控助手**

---

## Overview | 简介

StarOps is an AI-driven infrastructure monitoring and operations assistant designed for Linux desktop environments. It leverages natural language processing to allow users to query system metrics, security vulnerabilities, database performance, and other infrastructure concerns through conversational AI. The system automatically selects and executes appropriate monitoring protocols based on user queries.

StarOps 是一款 AI 驱动的智能基础设施监控与运维助手，专为 Linux 桌面环境设计。它利用自然语言处理技术，让用户可以通过对话式 AI 查询系统指标、安全漏洞、数据库性能等基础设施问题。系统会根据用户查询自动选择并执行相应的监控协议。

---

## Features | 功能特性

| | |
|---|---|
| **Natural Language Interface / 自然语言交互** | Query system metrics using plain English or Chinese. 支持中英文自然语言查询系统指标。 |
| **AI-Powered Protocol Selection / AI 智能协议选择** | DeepSeek LLM intelligently selects the right monitoring protocol. DeepSeek LLM 智能选择最佳监控协议。 |
| **Multi-Protocol Monitoring / 多协议监控** | Supports 13+ monitoring protocols for comprehensive coverage. 支持 13+ 监控协议，覆盖全面。 |
| **Floating Ball UI / 悬浮球界面** | Non-intrusive desktop widget for quick access. 非侵入式桌面小部件，快速访问。 |
| **Automated Analysis & Reports / 自动分析与报告** | Generates HTML reports for MySQL optimization and web scans. 自动生成 MySQL 优化及 Web 扫描 HTML 报告。 |
| **10-Level Anomaly Scoring / 10 级异常评分** | Sophisticated risk assessment system. 完善的风险评估体系。 |

---

## Supported Monitoring Protocols | 支持的监控协议

| Protocol 协议 | Description 描述 |
|---|---|
| NodeExporterProtocol | System metrics (CPU, memory, disk, network) 系统指标 (CPU, 内存, 磁盘, 网络) |
| BlackboxExporterProtocol | Network probing (HTTP, TCP, ICMP, DNS) 网络探测 (HTTP, TCP, ICMP, DNS) |
| MysqldExporterProtocol | MySQL database monitoring MySQL 数据库监控 |
| MySQLOptimizationProtocol | MySQL configuration analysis MySQL 配置分析与优化 |
| PrometheusMonitorProtocol | Traditional Prometheus metrics 传统 Prometheus 指标 |
| LokiPromtailProtocol | Log analysis 日志分析 |
| TrivySecurityProtocol | Container/security vulnerability scanning 容器/安全漏洞扫描 |
| WebScanProtocol | Web application security & performance Web 应用安全与性能 |
| AutofixProtocol | Automated problem remediation 自动化问题修复 |
| SkyWalkingProtocol | Microservice distributed tracing 微服务分布式追踪 |
| AnomalyPatternDetectionProtocol | Anomaly pattern detection 异常模式检测 |
| FusionLLMAnomalyDetectionProtocol | AI-powered anomaly detection AI 驱动的异常检测 |
| WindowsIOMonitorProtocol | Windows IO monitoring Windows IO 监控 |

---

## Tech Stack | 技术栈

- **Backend / 后端:** Python 3.8+
- **Frontend / 前端:** HTML/CSS/JavaScript with Electron
- **AI/ML:** DeepSeek API
- **Monitoring / 监控:** Prometheus-based metrics collection 基于 Prometheus 的指标采集

---

## Project Structure | 项目结构

```
src/
├── core/                    # Core backend modules / 核心后端模块
│   ├── ai_model.py         # AI model interface (DeepSeek API)
│   ├── smart_monitor.py    # Main monitoring orchestrator / 主监控编排器
│   └── mcp_protocols.py   # 13 monitoring protocol implementations / 13 种监控协议实现
├── frontend/               # Electron desktop app / Electron 桌面应用
├── apps/                   # Various app implementations (CLI, Qt, Flet) / 多种应用实现 (CLI, Qt, Flet)
├── mysql_report/           # MySQL optimization analysis module / MySQL 优化分析模块
├── utils/                  # Utility modules / 工具模块
└── reports/               # Generated analysis reports / 生成的报告
```

---

## Quick Start | 快速开始

### Prerequisites | 环境要求

- Python 3.8+
- Node.js (for Electron frontend / 用于 Electron 前端)
- DeepSeek API key / DeepSeek API 密钥

### Backend Setup | 后端安装

```bash
cd src
pip install -r requirements.txt
```

### Frontend Setup | 前端安装

```bash
cd src/frontend
npm install
npm start
```

---

## Documentation | 相关文档

- [Frontend Documentation / 前端文档](src/frontend/README.md)
- [MySQL Optimization Module / MySQL 优化模块](src/mysql_report/README.md)

---

## License | 许可证

MIT License / MIT 许可证
