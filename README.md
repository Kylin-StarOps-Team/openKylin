# StarOps

AI-Powered Intelligent System Monitoring Assistant

智能系统监控助手

## Overview

StarOps is an AI-driven infrastructure monitoring and operations assistant designed for Linux desktop environments. It leverages natural language processing to allow users to query system metrics, security vulnerabilities, database performance, and other infrastructure concerns through conversational AI. The system automatically selects and executes appropriate monitoring protocols based on user queries.

## Features

- **Natural Language Interface** - Query system metrics using plain English or Chinese
- **AI-Powered Protocol Selection** - DeepSeek LLM intelligently selects the right monitoring protocol
- **Multi-Protocol Monitoring** - Supports 13+ monitoring protocols for comprehensive coverage
- **Floating Ball UI** - Non-intrusive desktop widget for quick access
- **Automated Analysis & Reports** - Generates HTML reports for MySQL optimization and web scans

## Supported Monitoring Protocols

| Protocol | Description |
|----------|-------------|
| NodeExporterProtocol | System metrics (CPU, memory, disk, network) |
| BlackboxExporterProtocol | Network probing (HTTP, TCP, ICMP, DNS) |
| MysqldExporterProtocol | MySQL database monitoring |
| MySQLOptimizationProtocol | MySQL configuration analysis |
| PrometheusMonitorProtocol | Traditional Prometheus metrics |
| LokiPromtailProtocol | Log analysis |
| TrivySecurityProtocol | Container/security vulnerability scanning |
| WebScanProtocol | Web application security & performance |
| AutofixProtocol | Automated problem remediation |
| SkyWalkingProtocol | Microservice distributed tracing |
| AnomalyPatternDetectionProtocol | Anomaly pattern detection |
| FusionLLMAnomalyDetectionProtocol | AI-powered anomaly detection |
| WindowsIOMonitorProtocol | Windows IO monitoring |

## Tech Stack

- **Backend**: Python 3.8+
- **Frontend**: HTML/CSS/JavaScript with Electron
- **AI/ML**: DeepSeek API
- **Monitoring**: Prometheus-based metrics collection

## Project Structure

```
src/
├── core/                    # Core backend modules
│   ├── ai_model.py         # AI model interface (DeepSeek API)
│   ├── smart_monitor.py    # Main monitoring orchestrator
│   └── mcp_protocols.py    # 13 monitoring protocol implementations
├── frontend/               # Electron desktop app
├── apps/                   # Various app implementations (CLI, Qt, Flet)
├── mysql_report/           # MySQL optimization analysis module
├── utils/                  # Utility modules
└── reports/               # Generated analysis reports
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for Electron frontend)
- DeepSeek API key

### Backend Setup

```bash
cd src
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd src/frontend
npm install
npm start
```

## Documentation

- [Frontend Documentation](src/frontend/README.md)
- [MySQL Optimization Module](src/mysql_report/README.md)

## License

MIT License
