<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StarOps</title>
<style>
:root {
  --bg: #0d1117;
  --text: #c9d1d9;
  --accent: #58a6ff;
  --border: #30363d;
  --card: #161b22;
  --muted: #8b949e;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 40px 20px;
  max-width: 900px;
  margin: 0 auto;
}
.lang-switch {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 8px;
  z-index: 100;
}
.lang-switch button {
  padding: 6px 16px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--muted);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.lang-switch button:hover { border-color: var(--accent); color: var(--text); }
.lang-switch button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
h1 {
  font-size: 2.5em;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #58a6ff, #a371f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle { color: var(--muted); font-size: 1.1em; margin-bottom: 32px; }
section { margin-bottom: 40px; }
h2 {
  font-size: 1.4em;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin-bottom: 16px;
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}
.feature {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
}
.feature h3 { color: var(--accent); font-size: 1em; margin-bottom: 6px; }
.feature p { color: var(--muted); font-size: 0.9em; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}
th { color: var(--accent); }
tr:hover { background: var(--card); }
code {
  background: var(--card);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
  color: #f0883e;
}
pre {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-size: 0.9em;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.doc-links { display: flex; gap: 16px; flex-wrap: wrap; }
.doc-link {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 16px;
  color: var(--text);
  transition: all 0.2s;
}
.doc-link:hover { border-color: var(--accent); text-decoration: none; }

[lang="zh"] { display: none; }
:lang(zh) [lang="en"] { display: none; }
:lang(zh) [lang="zh"] { display: block; }
:lang(en) [lang="zh"] { display: none; }
</style>
</head>
<body>

<div class="lang-switch">
  <button onclick="setLang('en')" class="active" id="btn-en">English</button>
  <button onclick="setLang('zh')" id="btn-zh">中文</button>
</div>

<h1>StarOps</h1>
<p class="subtitle" lang="en">AI-Powered Intelligent System Monitoring Assistant</p>
<p class="subtitle" lang="zh">智能系统监控助手</p>

<!-- Overview -->
<section>
<h2 lang="en">Overview</h2>
<h2 lang="zh">简介</h2>
<p lang="en">StarOps is an AI-driven infrastructure monitoring and operations assistant designed for Linux desktop environments. It leverages natural language processing to allow users to query system metrics, security vulnerabilities, database performance, and other infrastructure concerns through conversational AI. The system automatically selects and executes appropriate monitoring protocols based on user queries.</p>
<p lang="zh">StarOps 是一款 AI 驱动的智能基础设施监控与运维助手，专为 Linux 桌面环境设计。它利用自然语言处理技术，让用户可以通过对话式 AI 查询系统指标、安全漏洞、数据库性能等基础设施问题。系统会根据用户查询自动选择并执行相应的监控协议。</p>
</section>

<!-- Features -->
<section>
<h2 lang="en">Features</h2>
<h2 lang="zh">功能特性</h2>
<div class="features-grid">
  <div class="feature">
    <h3 lang="en">Natural Language Interface</h3>
    <h3 lang="zh">自然语言交互</h3>
    <p lang="en">Query system metrics using plain English or Chinese</p>
    <p lang="zh">支持中英文自然语言查询系统指标</p>
  </div>
  <div class="feature">
    <h3 lang="en">AI-Powered Protocol Selection</h3>
    <h3 lang="zh">AI 智能协议选择</h3>
    <p lang="en">DeepSeek LLM intelligently selects the right monitoring protocol</p>
    <p lang="zh">DeepSeek LLM 智能选择最佳监控协议</p>
  </div>
  <div class="feature">
    <h3 lang="en">Multi-Protocol Monitoring</h3>
    <h3 lang="zh">多协议监控</h3>
    <p lang="en">Supports 13+ monitoring protocols for comprehensive coverage</p>
    <p lang="zh">支持 13+ 监控协议，覆盖全面</p>
  </div>
  <div class="feature">
    <h3 lang="en">Floating Ball UI</h3>
    <h3 lang="zh">悬浮球界面</h3>
    <p lang="en">Non-intrusive desktop widget for quick access</p>
    <p lang="zh">非侵入式桌面小部件，快速访问</p>
  </div>
  <div class="feature">
    <h3 lang="en">Automated Analysis & Reports</h3>
    <h3 lang="zh">自动分析与报告</h3>
    <p lang="en">Generates HTML reports for MySQL optimization and web scans</p>
    <p lang="zh">自动生成 MySQL 优化及 Web 扫描 HTML 报告</p>
  </div>
  <div class="feature">
    <h3 lang="en">10-Level Anomaly Scoring</h3>
    <h3 lang="zh">10 级异常评分</h3>
    <p lang="en">Sophisticated risk assessment system</p>
    <p lang="zh">完善的风险评估体系</p>
  </div>
</div>
</section>

<!-- Protocols -->
<section>
<h2 lang="en">Supported Monitoring Protocols</h2>
<h2 lang="zh">支持的监控协议</h2>
<table>
  <thead>
    <tr>
      <th lang="en">Protocol</th>
      <th lang="zh">协议</th>
      <th lang="en">Description</th>
      <th lang="zh">描述</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>NodeExporterProtocol</td><td lang="en">System metrics (CPU, memory, disk, network)</td><td lang="zh">系统指标 (CPU, 内存, 磁盘, 网络)</td></tr>
    <tr><td>BlackboxExporterProtocol</td><td lang="en">Network probing (HTTP, TCP, ICMP, DNS)</td><td lang="zh">网络探测 (HTTP, TCP, ICMP, DNS)</td></tr>
    <tr><td>MysqldExporterProtocol</td><td lang="en">MySQL database monitoring</td><td lang="zh">MySQL 数据库监控</td></tr>
    <tr><td>MySQLOptimizationProtocol</td><td lang="en">MySQL configuration analysis</td><td lang="zh">MySQL 配置分析与优化</td></tr>
    <tr><td>PrometheusMonitorProtocol</td><td lang="en">Traditional Prometheus metrics</td><td lang="zh">传统 Prometheus 指标</td></tr>
    <tr><td>LokiPromtailProtocol</td><td lang="en">Log analysis</td><td lang="zh">日志分析</td></tr>
    <tr><td>TrivySecurityProtocol</td><td lang="en">Container/security vulnerability scanning</td><td lang="zh">容器/安全漏洞扫描</td></tr>
    <tr><td>WebScanProtocol</td><td lang="en">Web application security & performance</td><td lang="zh">Web 应用安全与性能</td></tr>
    <tr><td>AutofixProtocol</td><td lang="en">Automated problem remediation</td><td lang="zh">自动化问题修复</td></tr>
    <tr><td>SkyWalkingProtocol</td><td lang="en">Microservice distributed tracing</td><td lang="zh">微服务分布式追踪</td></tr>
    <tr><td>AnomalyPatternDetectionProtocol</td><td lang="en">Anomaly pattern detection</td><td lang="zh">异常模式检测</td></tr>
    <tr><td>FusionLLMAnomalyDetectionProtocol</td><td lang="en">AI-powered anomaly detection</td><td lang="zh">AI 驱动的异常检测</td></tr>
    <tr><td>WindowsIOMonitorProtocol</td><td lang="en">Windows IO monitoring</td><td lang="zh">Windows IO 监控</td></tr>
  </tbody>
</table>
</section>

<!-- Tech Stack -->
<section>
<h2 lang="en">Tech Stack</h2>
<h2 lang="zh">技术栈</h2>
<ul>
  <li lang="en"><strong>Backend:</strong> Python 3.8+</li>
  <li lang="zh"><strong>后端:</strong> Python 3.8+</li>
  <li lang="en"><strong>Frontend:</strong> HTML/CSS/JavaScript with Electron</li>
  <li lang="zh"><strong>前端:</strong> HTML/CSS/JavaScript + Electron</li>
  <li lang="en"><strong>AI/ML:</strong> DeepSeek API</li>
  <li lang="zh"><strong>AI/ML:</strong> DeepSeek API</li>
  <li lang="en"><strong>Monitoring:</strong> Prometheus-based metrics collection</li>
  <li lang="zh"><strong>监控:</strong> 基于 Prometheus 的指标采集</li>
</ul>
</section>

<!-- Project Structure -->
<section>
<h2 lang="en">Project Structure</h2>
<h2 lang="zh">项目结构</h2>
<pre><code>src/
├── core/                    <span lang="en"># Core backend modules</span><span lang="zh"># 核心后端模块</span>
│   ├── ai_model.py         <span lang="en"># AI model interface (DeepSeek API)</span><span lang="zh"># AI 模型接口 (DeepSeek API)</span>
│   ├── smart_monitor.py    <span lang="en"># Main monitoring orchestrator</span><span lang="zh"># 主监控编排器</span>
│   └── mcp_protocols.py    <span lang="en"># 13 monitoring protocol implementations</span><span lang="zh"># 13 种监控协议实现</span>
├── frontend/               <span lang="en"># Electron desktop app</span><span lang="zh"># Electron 桌面应用</span>
├── apps/                   <span lang="en"># Various app implementations (CLI, Qt, Flet)</span><span lang="zh"># 多种应用实现 (CLI, Qt, Flet)</span>
├── mysql_report/           <span lang="en"># MySQL optimization analysis module</span><span lang="zh"># MySQL 优化分析模块</span>
├── utils/                  <span lang="en"># Utility modules</span><span lang="zh"># 工具模块</span>
└── reports/               <span lang="en"># Generated analysis reports</span><span lang="zh"># 生成的报告</span></code></pre>
</section>

<!-- Quick Start -->
<section>
<h2 lang="en">Quick Start</h2>
<h2 lang="zh">快速开始</h2>

<h3 lang="en">Prerequisites</h3>
<h3 lang="zh">环境要求</h3>
<ul>
  <li lang="en">Python 3.8+</li>
  <li lang="zh">Python 3.8+</li>
  <li lang="en">Node.js (for Electron frontend)</li>
  <li lang="zh">Node.js (用于 Electron 前端)</li>
  <li lang="en">DeepSeek API key</li>
  <li lang="zh">DeepSeek API 密钥</li>
</ul>

<h3 lang="en" style="margin-top:16px">Backend Setup</h3>
<h3 lang="zh" style="margin-top:16px">后端安装</h3>
<pre><code>cd src
pip install -r requirements.txt</code></pre>

<h3 lang="en" style="margin-top:16px">Frontend Setup</h3>
<h3 lang="zh" style="margin-top:16px">前端安装</h3>
<pre><code>cd src/frontend
npm install
npm start</code></pre>
</section>

<!-- Documentation -->
<section>
<h2 lang="en">Documentation</h2>
<h2 lang="zh">相关文档</h2>
<div class="doc-links">
  <a href="src/frontend/README.md" class="doc-link" lang="en">Frontend Documentation</a>
  <a href="src/frontend/README.md" class="doc-link" lang="zh">前端文档</a>
  <a href="src/mysql_report/README.md" class="doc-link" lang="en">MySQL Optimization Module</a>
  <a href="src/mysql_report/README.md" class="doc-link" lang="zh">MySQL 优化模块</a>
</div>
</section>

<!-- License -->
<section>
<h2 lang="en">License</h2>
<h2 lang="zh">许可证</h2>
<p lang="en">MIT License</p>
<p lang="zh">MIT 许可证</p>
</section>

<script>
function setLang(lang) {
  document.documentElement.lang = lang;
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');
  document.getElementById('btn-zh').classList.toggle('active', lang === 'zh');
}
</script>

</body>
</html>
