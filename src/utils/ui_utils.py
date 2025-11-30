# -*- coding: utf-8 -*-
"""
UI工具模块
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

class UIUtils:
    """UI工具类"""
    
    @staticmethod
    def check_gui_environment():
        """检查GUI环境是否可用"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
            return True
        except Exception as e:
            print(f"GUI环境不可用: {e}")
            return False
    
    @staticmethod
    def create_chat_display(parent, **kwargs):
        """创建聊天显示区域"""
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=(kwargs.get('font_family', 'Consolas'), kwargs.get('font_size', 10)),
            bg=kwargs.get('bg', 'white'),
            height=kwargs.get('height', 20),
            **{k: v for k, v in kwargs.items() if k not in ['font_family', 'font_size', 'bg', 'height']}
        )
    
    @staticmethod
    def create_tools_display(parent, **kwargs):
        """创建工具调用显示区域"""
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=(kwargs.get('font_family', 'Consolas'), kwargs.get('font_size', 9)),
            bg=kwargs.get('bg', '#f8f8f8'),
            height=kwargs.get('height', 15),
            **{k: v for k, v in kwargs.items() if k not in ['font_family', 'font_size', 'bg', 'height']}
        )
    
    @staticmethod
    def add_message_with_timestamp(text_widget, role, message, thinking_process=None, tool_calls=None):
        """添加带时间戳的消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 添加思考过程
        if thinking_process:
            text_widget.insert(tk.END, f"[{timestamp}] 助手思考过程:\n", "thinking")
            text_widget.insert(tk.END, f"{thinking_process}\n\n", "thinking")
        
        # 添加工具调用信息
        if tool_calls:
            text_widget.insert(tk.END, f"[{timestamp}] 工具调用:\n", "tool_call")
            for tool in tool_calls:
                text_widget.insert(tk.END, f"🔧 {tool}\n", "tool_call")
            text_widget.insert(tk.END, "\n")
        
        # 添加消息
        text_widget.insert(tk.END, f"[{timestamp}] {role}: {message}\n\n")
        text_widget.see(tk.END)
        
        # 设置文本标签样式
        text_widget.tag_config("thinking", foreground="blue", font=('Consolas', 9, 'italic'))
        text_widget.tag_config("tool_call", foreground="green", font=('Consolas', 9, 'bold'))
    
    @staticmethod
    def update_tools_display(text_widget, tool_info):
        """更新工具调用显示"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        text_widget.insert(tk.END, f"[{timestamp}] {tool_info}\n")
        text_widget.see(tk.END)
    
    @staticmethod
    def show_info_dialog(title, message):
        """显示信息对话框"""
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_error_dialog(title, message):
        """显示错误对话框"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def show_confirm_dialog(title, message):
        """显示确认对话框"""
        return messagebox.askyesno(title, message)
    
    @staticmethod
    def show_file_dialog(title, filetypes, save=False):
        """显示文件对话框"""
        if save:
            return filedialog.asksaveasfilename(title=title, filetypes=filetypes)
        else:
            return filedialog.askopenfilename(title=title, filetypes=filetypes)
    
    @staticmethod
    def create_banner():
        """创建应用横幅"""
        return """
╔══════════════════════════════════════════════════════════════╗
║                智能系统监控助手 - 命令行版本                    ║
╠══════════════════════════════════════════════════════════════╣
║ 功能特性:                                                    ║
║ • 智能系统监控 (CPU、内存、磁盘IO、网络等)                    ║
║ • 实时工具调用链显示                                          ║
║ • 思考过程可视化                                              ║
║ • 对话历史保存和加载                                          ║
║ • 支持11种监控协议 (系统、网络、数据库、日志、安全、修复、微服务)   ║
║ • 异常检测和十级制评分                                        ║
║ • 从日志文件读取监控数据                                      ║
╚══════════════════════════════════════════════════════════════╝
        """
    
    @staticmethod
    def create_help_text():
        """创建帮助文本"""
        return """
📋 可用命令:
• 直接输入问题 - 与AI助手对话
• /help - 显示此帮助信息
• /history - 显示对话历史
• /clear - 清空当前对话
• /save - 保存对话到文件
• /load - 从文件加载对话
• /status - 显示系统状态
• /quit 或 /exit - 退出应用

💡 示例问题:
• "我的CPU使用率怎么样？" (Node Exporter)
• "系统内存使用情况如何？" (Node Exporter)
• "磁盘IO状态如何？" (Windows IO监控)
• "系统负载高吗？" (Prometheus)
• "百度网站能访问吗？" (Blackbox Exporter)
• "MySQL数据库连接数多少？" (Mysqld Exporter)
• "有什么错误日志？" (Loki Promtail)
• "扫描Docker镜像安全漏洞" (Trivy)
• "系统内存占用高，需要修复" (Ansible)
• "分析微服务异常情况" (SkyWalking)
• "进行根因分析" (SkyWalking)


🔧 支持的监控协议:
• WindowsIOMonitorProtocol - 磁盘IO状态监控
• PrometheusMonitorProtocol - CPU/内存/负载等指标监控
• NodeExporterProtocol - 系统级指标采集
• BlackboxExporterProtocol - 黑盒探测(HTTP/TCP/ICMP/DNS)
• MysqldExporterProtocol - MySQL数据库监控
• LokiPromtailProtocol - 日志收集和分析
• TrivySecurityProtocol - 安全漏洞扫描
• AutofixProtocol - 系统自动修复服务
• WebScanProtocol - Web应用配置检测
• MySQLOptimizationProtocol - MySQL配置优化分析
• SkyWalkingProtocol - 微服务分布式追踪与根因分析

🌟 微服务相关问题触发关键词:
• 微服务、服务间调用、服务依赖、服务拓扑
• 分布式、链路追踪、调用链、trace、span
• 异常服务、服务异常、异常检测、服务故障
• 根因定位、根因分析、故障原因、问题定位、RCA
• 资源关联、资源依赖、依赖关系、服务关系


📊 异常评分系统:
• 0级: 正常 | 1-3级: 轻微异常 | 4-6级: 中等异常
• 7-8级: 严重异常 | 9-10级: 危急异常
        """ 