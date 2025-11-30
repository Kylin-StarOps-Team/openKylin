#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown渲染演示
展示聊天界面中的Markdown支持功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextBrowser, QLabel
from PyQt5.QtCore import Qt

try:
    from apps.floating_ball_qt import MarkdownRenderer
    DEMO_AVAILABLE = True
except ImportError as e:
    print(f"❌ 无法导入MarkdownRenderer: {e}")
    DEMO_AVAILABLE = False


class MarkdownDemo(QWidget):
    """Markdown渲染演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("StarOps - Markdown渲染演示")
        self.setGeometry(300, 300, 800, 600)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("Markdown渲染功能演示")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2196F3;
            padding: 10px;
            text-align: center;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 演示内容
        if DEMO_AVAILABLE:
            demo_content = self.create_demo_content()
            
            # 创建Markdown渲染器
            renderer = MarkdownRenderer()
            
            # 创建文本浏览器
            browser = QTextBrowser()
            browser.setHtml(renderer.render(demo_content))
            browser.setStyleSheet("""
                QTextBrowser {
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    background-color: white;
                }
            """)
            layout.addWidget(browser)
        else:
            error_label = QLabel("❌ Markdown渲染器不可用\n请确保已正确安装依赖")
            error_label.setStyleSheet("""
                color: #dc3545;
                font-size: 16px;
                padding: 20px;
                text-align: center;
            """)
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
        
        self.setLayout(layout)
        
    def create_demo_content(self):
        """创建演示内容"""
        return """
# StarOps 智能监控助手

## 🎯 系统监控功能

StarOps 是一个**强大的系统监控助手**，支持多种监控协议和智能分析功能。

### 📊 核心特性

- **实时监控**: 支持CPU、内存、磁盘、网络等系统资源监控
- **智能分析**: 基于AI的异常检测和问题诊断  
- **多协议支持**: 集成10种专业监控协议
- **可视化报告**: 生成美观的HTML格式检测报告

### 🔍 列表渲染测试

#### 无序列表测试
- 第一个列表项
- 第二个列表项
  - 嵌套列表项1
  - 嵌套列表项2
- 第三个列表项

#### 不同符号的列表
• 使用圆点符号的列表项
• 另一个圆点列表项
* 使用星号的列表项
* 另一个星号列表项

#### 混合符号列表
- 连字符列表项
• 圆点列表项
* 星号列表项

### 🔧 支持的监控协议

| 协议名称 | 功能描述 | 适用场景 |
|---------|----------|----------|
| **Prometheus** | 指标收集和监控 | 微服务监控 |
| **MySQL优化** | 数据库性能分析 | 数据库调优 |
| **Trivy安全扫描** | 容器安全检测 | DevSecOps |
| **Web配置检测** | 网站安全分析 | Web安全 |

### 💡 使用示例

#### 1. CPU监控
```bash
# 查看CPU使用情况
检查CPU使用情况
```

#### 2. 数据库优化
```sql
-- MySQL配置优化建议
SHOW VARIABLES LIKE 'innodb%';
```

#### 3. Python代码示例
```python
from core import SmartMonitor

# 创建监控实例
monitor = SmartMonitor(api_key="your-key")

# 执行智能查询
result = monitor.smart_query("检查系统性能")
print(result)
```

### 🎨 界面特色

> **iOS风格设计**: 采用现代化的iOS设计语言，提供简约而优雅的用户体验。

- 🔮 **悬浮球交互**: 独特的悬浮球启动方式
- 💬 **智能对话**: 自然语言交互界面  
- 📋 **报告管理**: 精美的卡片式报告展示
- 🎯 **一键操作**: 双击悬浮球即可开始使用

### 🚀 快速开始

1. **安装依赖**
   ```bash
   python install_pyqt_deps.py
   ```

2. **启动应用**
   ```bash
   python run_floating_ball.py
   ```

3. **开始监控**
   - 双击屏幕右侧的悬浮球
   - 在聊天界面输入监控需求
   - 查看智能分析结果

### ⚡ 性能优势

- **轻量级**: PyQt5原生界面，资源占用低
- **高效率**: 多线程处理，界面响应流畅
- **跨平台**: 支持Windows、macOS、Linux

---

**💻 技术支持**: 基于PyQt5 + AI智能分析
**🎯 适用场景**: 系统运维、性能监控、安全检测
**📱 交互方式**: 悬浮球 + 自然语言对话

> 让系统监控变得更简单、更智能、更高效！
        """


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    demo = MarkdownDemo()
    demo.show()
    
    print("🎯 Markdown渲染演示启动")
    print("📝 展示了聊天界面中的Markdown渲染效果")
    print("❌ 按Ctrl+C或关闭窗口退出")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
