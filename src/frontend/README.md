# StarOps AI系统监控助手 - Linux桌面版

基于Electron框架开发的智能系统监控助手，为Linux用户提供强大的AI驱动的系统监控和运维服务。

## 🌟 核心特性

### 🤖 智能AI对话
- 自然语言交互，智能识别监控需求
- 自动调用适合的监控协议和工具
- 支持10种专业监控协议
- 实时分析过程展示

### 🎈 悬浮球设计
- 不占用桌面空间，悬浮球形式存在
- 显示"StarOps"标识，双击打开主界面
- 支持拖拽移动，始终保持在最顶层

### 📊 报告管理
- Web检测报告查看和管理
- MySQL优化报告查看和管理
- 一键打开浏览器查看详细报告
- 智能解析报告元数据

### 🎨 简约界面
- 现代化Material Design设计风格
- 清晰的导航和布局
- 响应式设计，适配不同屏幕尺寸
- 优雅的动画和交互效果

## 🚀 快速开始

### 环境要求
- Linux操作系统
- Node.js 16+ 
- Python 3.8+
- 已配置的StarOps后端服务

### 安装步骤

1. **克隆项目**
   ```bash
   cd /path/to/MCPArchieve/frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动应用**
   ```bash
   # 开发模式
   npm run dev
   
   # 生产模式
   npm start
   ```

4. **构建发布版本**
   ```bash
   npm run build
   ```

## 📱 使用指南

### 悬浮球模式
- 应用启动后自动显示悬浮球
- 双击悬浮球打开主界面
- 可拖拽移动到任意位置

### AI对话功能
1. 点击"AI对话"标签
2. 在输入框中输入您的问题
3. 系统会自动分析并调用相应的监控工具
4. 查看右侧的分析过程和工具调用详情

#### 示例问题
```
- "检查CPU使用情况"
- "分析MySQL数据库配置优化"  
- "扫描Docker镜像安全漏洞"
- "检测网站配置和性能"
- "监控系统内存使用率"
```

### 报告查看
1. 点击相应的报告标签
2. 浏览生成的检测报告
3. 点击"打开报告"在浏览器中查看详情

## 🔧 支持的监控协议

1. **系统监控**
   - WindowsIOMonitorProtocol - Windows IO监控
   - PrometheusMonitorProtocol - Prometheus指标收集
   - NodeExporterProtocol - 节点指标导出

2. **安全检测**  
   - TrivySecurityProtocol - 容器安全扫描
   - WebScanProtocol - Web应用安全检测

3. **数据库优化**
   - MysqldExporterProtocol - MySQL指标导出
   - MySQLOptimizationProtocol - MySQL配置优化

4. **网络监控**
   - BlackboxExporterProtocol - 黑盒监控探测

5. **日志分析**
   - LokiPromtailProtocol - 日志收集和分析

6. **智能修复**
   - AutofixProtocol - 自动化问题修复

7. **微服务监控**
   - SkyWalkingProtocol - 分布式追踪
   - AnomalyPatternDetectionProtocol - 异常模式检测
   - FusionLLMAnomalyDetectionProtocol - AI异常检测

## 📂 项目结构

```
frontend/
├── main.js              # Electron主进程
├── index.html          # 主界面HTML
├── floating-ball.html  # 悬浮球HTML
├── styles.css          # 样式文件
├── renderer.js         # 渲染进程逻辑
├── package.json        # 项目配置
├── assets/             # 资源文件
└── README.md           # 说明文档
```

## 🛠 开发说明

### 主要技术栈
- **Electron** - 跨平台桌面应用框架
- **HTML/CSS/JavaScript** - 前端技术
- **Node.js** - 后端运行时
- **Python** - 智能监控后端
- **Marked.js** - Markdown渲染
- **Highlight.js** - 代码高亮

### 架构设计
- **主进程(main.js)**: 负责窗口管理、Python调用、文件操作
- **渲染进程(renderer.js)**: 负责UI交互、数据展示、用户体验
- **IPC通信**: 主进程与渲染进程间的通信桥梁

### 与Python后端通信
应用通过spawn子进程的方式调用Python智能监控脚本：
- 传递用户问题到smart_monitor.py
- 接收JSON格式的分析结果
- 支持实时输出和错误处理

## 🎯 特色功能

### 智能分析展示
- 实时显示AI分析思考过程
- 工具调用链路可视化
- 结果以Markdown格式美化展示

### 响应式设计
- 适配不同屏幕尺寸
- 移动端友好的交互设计
- 优雅的动画和过渡效果

### 报告管理
- 自动扫描和解析报告文件
- 智能提取报告元信息
- 跨平台文件打开支持

## 🐛 故障排除

### 常见问题

1. **Python调用失败**
   - 确认Python环境和依赖包正确安装
   - 检查smart_monitor.py路径是否正确
   - 验证API密钥配置

2. **报告无法打开**
   - 确认报告文件存在且有读取权限
   - 检查默认浏览器设置
   - 尝试手动打开file://路径

3. **悬浮球无法显示**
   - 检查X11显示权限
   - 确认窗口管理器支持置顶窗口
   - 重启应用尝试

## 📄 许可证

ISC License

## 👥 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📞 支持

如有问题，请联系StarOps团队或提交Issue。
