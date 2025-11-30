# -*- coding: utf-8 -*-
"""
智能系统监控助手 - Flet桌面应用
"""

import flet as ft
import asyncio
import threading
import time
import sys
import os
import json
import webbrowser
import glob
import re
import platform
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SmartMonitor
from utils import Config, HistoryManager

class FletDesktopMonitorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "智能系统监控助手 - Flet桌面版"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.padding = 20
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # 设置窗口关闭事件监听器
        self.page.on_window_event = self.on_window_event
        
        # 初始化配置和历史管理
        self.config = Config()
        self.history_manager = HistoryManager()
        
        # 初始化智能监控器
        self.monitor = SmartMonitor(self.config.api_key)
        self.monitor.conversation_history = self.history_manager.conversation_history
        
        # UI控件引用
        self.chat_container = None
        self.tools_container = None
        self.message_input = None
        self.send_button = None
        self.status_text = None
        self.thinking_container = None
        self.main_content_area = None
        self.navigation_tabs = None
        
        # 状态管理
        self.is_processing = False
        self.current_view = "chat"  # chat, web_reports, mysql_reports
        
        # 创建界面
        self.create_ui()
        
    def on_window_event(self, e):
        """处理窗口事件"""
        if e.data == "close":
            # 仿照 cli_app.py，在窗口关闭时同步历史数据并清理
            try:
                # 同步历史数据
                self.history_manager.conversation_history = self.monitor.conversation_history
                self.history_manager.save_history()
                # 清理历史
                self.history_manager.clear_history()
            except Exception as ex:
                print(f"关闭时清理历史数据失败: {ex}")
        
    def create_ui(self):
        """创建用户界面"""
        # 主标题
        title = ft.Text(
            "智能系统监控助手",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_800
        )
        
        # 创建导航选项卡
        self.navigation_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(
                    text="对话聊天",
                    icon=ft.Icons.CHAT,
                ),
                ft.Tab(
                    text="Web检测报告", 
                    icon=ft.Icons.WEB,
                ),
                ft.Tab(
                    text="MySQL优化报告",
                    icon=ft.Icons.STORAGE,
                )
            ]
        )
        
        # 创建主要内容区域
        self.main_content_area = ft.Container(
            content=self.create_chat_view(),
            expand=True,
            padding=10
        )
        
        # 底部按钮区域
        button_row = self.create_button_row()
        
        # 状态栏
        self.status_text = ft.Text(
            "就绪",
            size=12,
            color=ft.Colors.GREEN_600
        )
        status_bar = ft.Container(
            content=self.status_text,
            padding=ft.padding.symmetric(vertical=5, horizontal=10),
            bgcolor=ft.Colors.GREY_100,
            border_radius=5
        )
        
        # 将所有组件添加到页面
        self.page.add(
            ft.Column([
                title,
                self.navigation_tabs,
                self.main_content_area,
                button_row,
                status_bar
            ],
            expand=True,
            spacing=20)
        )
        
        # 显示欢迎信息（在对话区域创建后添加）
        self.show_welcome_message()
        
        # 设置焦点到输入框
        self.page.update()
        
    def create_chat_view(self):
        """创建对话视图"""
        return ft.Row(
            [
                # 左侧：对话区域
                ft.Container(
                    content=self.create_chat_section(),
                    expand=3,
                    padding=10
                ),
                # 右侧：工具调用和状态
                ft.Container(
                    content=self.create_tools_section(),
                    expand=1,
                    padding=10
                )
            ],
            expand=True,
            spacing=20
        )
    
    def create_chat_section(self):
        """创建对话区域"""
        # 对话显示区域
        self.chat_container = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(10),
            auto_scroll=True
        )
        
        chat_area = ft.Container(
            content=self.chat_container,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            padding=10,
            expand=True
        )
        
        # 输入区域
        self.message_input = ft.TextField(
            hint_text="输入您的问题...",
            multiline=True,
            max_lines=3,
            expand=True,
            on_submit=self.send_message
        )
        
        self.send_button = ft.ElevatedButton(
            "发送",
            on_click=self.send_message,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE
        )
        
        input_row = ft.Row([
            self.message_input,
            self.send_button
        ], spacing=10)
        
        return ft.Column([
            ft.Text("对话区域", size=16, weight=ft.FontWeight.BOLD),
            chat_area,
            input_row
        ], spacing=10, expand=True)
    
    def show_welcome_message(self):
        """显示系统欢迎信息"""
        if self.current_view == "chat" and self.chat_container:
            self.add_system_message(
                "🎉 欢迎使用智能系统监控助手！\n\n"
                "🔧 **核心功能**：\n"
                "我是您的专业系统运维助手，支持10种强大的监控协议，为您提供全方位的系统监控和安全检测服务。\n\n"
                "📊 **系统监控能力**：\n"
                "• 💻 CPU使用率和系统负载监控\n"
                "• 🧠 内存使用情况和性能分析\n"
                "• 💾 磁盘IO状态和存储空间监控\n"
                "• 🌐 网络流量和连通性探测\n"
                "• 📈 Prometheus指标收集和分析\n\n"
                "🗃️ **数据库专项服务**：\n"
                "• 📊 MySQL数据库性能实时监控\n"
                "• ⚡ MySQL配置优化和性能调优\n"
                "• 📋 生成专业的数据库优化报告\n\n"
                "🔍 **安全和日志分析**：\n"
                "• 🛡️ Trivy容器和应用安全扫描\n"
                "• 📜 系统日志分析和异常检测\n"
                "• 🌐 Web应用配置和安全检测\n\n"
                "🔧 **智能修复服务**：\n"
                "• 🚀 系统问题自动诊断和修复\n"
                "• 📋 提供详细的修复方案和建议\n\n"
                "💡 **使用方式**：\n"
                "直接输入您的问题，我会智能识别并自动调用最适合的监控工具。例如：\n"
                "• \"检查CPU使用情况\"\n"
                "• \"分析MySQL数据库配置优化\"\n"
                "• \"扫描Docker镜像安全漏洞\"\n"
                "• \"检测网站配置和性能\"\n\n"
                "📱 **导航提示**：\n"
                "• 点击上方\"Web检测报告\"查看网站配置检测历史\n"
                "• 点击上方\"MySQL优化报告\"查看数据库优化历史\n\n"
                "🎯 **智能特性**：支持10种监控协议，提供专业级异常评分，让运维工作更高效！"
            )
        
    def create_tools_section(self):
        """创建工具调用和状态区域"""
        # 思考过程显示
        self.thinking_container = ft.ListView(
            expand=True,
            spacing=5,
            padding=ft.padding.all(10),
            auto_scroll=True
        )
        
        thinking_area = ft.Container(
            content=self.thinking_container,
            border=ft.border.all(2, ft.Colors.ORANGE_300),
            border_radius=10,
            bgcolor=ft.Colors.ORANGE_50,
            padding=10,
            height=200
        )
        
        # 工具调用显示
        self.tools_container = ft.ListView(
            expand=True,
            spacing=5,
            padding=ft.padding.all(10),
            auto_scroll=True
        )
        
        tools_area = ft.Container(
            content=self.tools_container,
            border=ft.border.all(2, ft.Colors.GREEN_300),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50,
            padding=10,
            expand=True
        )
        
        return ft.Column([
            ft.Text("思考过程", size=14, weight=ft.FontWeight.BOLD),
            thinking_area,
            ft.Text("工具调用链", size=14, weight=ft.FontWeight.BOLD),
            tools_area
        ], spacing=10, expand=True)
    
    def on_tab_change(self, e):
        """处理选项卡切换"""
        selected_index = e.control.selected_index
        
        if selected_index == 0:  # 对话聊天
            self.current_view = "chat"
            self.main_content_area.content = self.create_chat_view()
            # 如果对话区域为空，显示欢迎信息
            if not self.chat_container.controls:
                self.show_welcome_message()
        elif selected_index == 1:  # Web检测报告
            self.current_view = "web_reports"
            self.main_content_area.content = self.create_web_reports_view()
        elif selected_index == 2:  # MySQL优化报告
            self.current_view = "mysql_reports"  
            self.main_content_area.content = self.create_mysql_reports_view()
        
        self.page.update()
    
    def create_web_reports_view(self):
        """创建Web检测报告视图"""
        reports_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(20)
        )
        
        # 获取reports目录下的HTML文件
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        
        try:
            html_files = glob.glob(os.path.join(reports_dir, "*.html"))
            html_files.sort(reverse=True)  # 按时间倒序排列
            
            if html_files:
                for html_file in html_files:
                    filename = os.path.basename(html_file)
                    # 解析文件名中的时间戳
                    try:
                        timestamp_part = filename.replace("web_config_report_", "").replace(".html", "")
                        formatted_time = f"{timestamp_part[:4]}-{timestamp_part[4:6]}-{timestamp_part[6:8]} {timestamp_part[9:11]}:{timestamp_part[11:13]}:{timestamp_part[13:15]}"
                    except:
                        formatted_time = "时间未知"
                    
                    # 获取文件大小
                    file_size = os.path.getsize(html_file)
                    size_mb = file_size / (1024 * 1024)
                    
                    # 提取目标URL
                    target_url = self.extract_target_url_from_web_report(html_file)
                    report_title = f"Web配置检测报告"
                    if target_url:
                        report_title = f"Web检测: {target_url}"
                    
                    report_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.WEB, color=ft.Colors.BLUE_600),
                                    ft.Text(report_title, weight=ft.FontWeight.BOLD, size=16)
                                ]),
                                ft.Text(f"生成时间: {formatted_time}", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"文件大小: {size_mb:.1f}MB", size=12, color=ft.Colors.GREY_600),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "打开报告",
                                        icon=ft.Icons.OPEN_IN_BROWSER,
                                        on_click=lambda e, path=html_file: self.open_html_file(path),
                                        bgcolor=ft.Colors.BLUE_600,
                                        color=ft.Colors.WHITE
                                    ),
                                    ft.TextButton(
                                        f"文件: {filename}",
                                        on_click=lambda e, path=html_file: self.open_html_file(path)
                                    )
                                ])
                            ], spacing=5),
                            padding=15
                        )
                    )
                    reports_list.controls.append(report_card)
            else:
                # 没有找到报告文件
                no_reports_msg = ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_400),
                        ft.Text("暂无Web检测报告", size=18, color=ft.Colors.GREY_600),
                        ft.Text("请先进行Web配置检测以生成报告", size=14, color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    expand=True
                )
                reports_list.controls.append(no_reports_msg)
                
        except Exception as e:
            error_msg = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED_400),
                    ft.Text("加载报告失败", size=18, color=ft.Colors.RED_600),
                    ft.Text(f"错误信息: {str(e)}", size=12, color=ft.Colors.GREY_500)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                expand=True
            )
            reports_list.controls.append(error_msg)
        
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.WEB, color=ft.Colors.BLUE_600),
                ft.Text("Web检测报告", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="刷新列表",
                    on_click=lambda e: self.refresh_reports_view()
                )
            ]),
            ft.Container(
                content=reports_list,
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=10,
                padding=10,
                expand=True
            )
        ], spacing=10, expand=True)
    
    def create_mysql_reports_view(self):
        """创建MySQL优化报告视图"""
        reports_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(20)
        )
        
        # 获取mysql_report目录下的HTML文件
        mysql_reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mysql_report")
        
        try:
            html_files = glob.glob(os.path.join(mysql_reports_dir, "mysql_optimization_report_*.html"))
            html_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]), reverse=True)  # 按检测编号倒序
            
            if html_files:
                for html_file in html_files:
                    filename = os.path.basename(html_file)
                    # 提取检测编号
                    try:
                        detection_num = filename.split('_')[-1].split('.')[0]
                    except:
                        detection_num = "未知"
                    
                    # 获取文件大小和修改时间
                    file_size = os.path.getsize(html_file)
                    size_kb = file_size / 1024
                    modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(html_file)))
                    
                    # 尝试读取对应的建议文件以获取建议数量
                    suggestions_file = html_file.replace("mysql_optimization_report_", "mysql_suggestions_").replace(".html", ".json")
                    suggestions_count = 0
                    try:
                        if os.path.exists(suggestions_file):
                            with open(suggestions_file, 'r', encoding='utf-8') as f:
                                suggestions_data = json.load(f)
                                suggestions_count = len(suggestions_data)
                    except:
                        pass
                    
                    report_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.STORAGE, color=ft.Colors.GREEN_600),
                                    ft.Text(f"MySQL配置优化报告 #{detection_num}", weight=ft.FontWeight.BOLD, size=16)
                                ]),
                                ft.Text(f"生成时间: {modified_time}", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"文件大小: {size_kb:.1f}KB", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"优化建议: {suggestions_count} 条", size=12, color=ft.Colors.GREY_600),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "打开报告",
                                        icon=ft.Icons.OPEN_IN_BROWSER,
                                        on_click=lambda e, path=html_file: self.open_html_file(path),
                                        bgcolor=ft.Colors.GREEN_600,
                                        color=ft.Colors.WHITE
                                    ),
                                    ft.TextButton(
                                        f"检测 #{detection_num}",
                                        on_click=lambda e, path=html_file: self.open_html_file(path)
                                    )
                                ])
                            ], spacing=5),
                            padding=15
                        )
                    )
                    reports_list.controls.append(report_card)
            else:
                # 没有找到报告文件
                no_reports_msg = ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_400),
                        ft.Text("暂无MySQL优化报告", size=18, color=ft.Colors.GREY_600),
                        ft.Text("请先进行MySQL配置优化检测以生成报告", size=14, color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    expand=True
                )
                reports_list.controls.append(no_reports_msg)
                
        except Exception as e:
            error_msg = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED_400),
                    ft.Text("加载报告失败", size=18, color=ft.Colors.RED_600),
                    ft.Text(f"错误信息: {str(e)}", size=12, color=ft.Colors.GREY_500)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                expand=True
            )
            reports_list.controls.append(error_msg)
        
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.STORAGE, color=ft.Colors.GREEN_600),
                ft.Text("MySQL优化报告", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="刷新列表",
                    on_click=lambda e: self.refresh_reports_view()
                )
            ]),
            ft.Container(
                content=reports_list,
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=10,
                padding=10,
                expand=True
            )
        ], spacing=10, expand=True)
    
    def open_html_file(self, file_path):
        """使用默认浏览器打开HTML文件"""
        try:
            # 获取绝对路径
            abs_path = os.path.abspath(file_path)
            # 构造file://URL格式，按您测试成功的方式
            file_url = f"file://{abs_path}"
            
            print(f"📂 打开文件: {file_url}")
            
            # 根据操作系统使用不同的打开方式
            system = platform.system()
            
            if system == "Windows":
                print("windows")
                # Windows下直接使用文件路径
                os.startfile(abs_path)
            elif system == "Darwin":  # macOS
                print("macos")
                subprocess.run(["open", file_url])
            else:  # Linux and others
                # 尝试多种浏览器打开，使用file://URL格式
                commands = [
                    ["google-chrome",file_url],
                    ["firefox", file_url],
                    ["chromium-browser", file_url],
                    ["xdg-open", file_url]
                ]
                print("else")
                opened = False
                for cmd in commands:
                    try:
                        print(cmd)
                        subprocess.run(cmd)
                        opened = True
                        print(f"✅ 成功使用 {cmd[0]} 打开报告")
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print(f"❌ {cmd[0]} 不可用，尝试下一个")
                        continue
                
                if not opened:
                    # 最后尝试webbrowser模块
                    webbrowser.open(file_url)
                    print("✅ 使用webbrowser模块打开报告")
            
            self.update_status(f"已打开报告: {os.path.basename(file_path)}", ft.Colors.GREEN_600)
            
        except Exception as e:
            # 如果所有方法都失败，提供完整的命令给用户手动执行
            abs_path = os.path.abspath(file_path)
            manual_command = f"google-chrome file://{abs_path}"
            self.update_status(f"请手动执行: {manual_command}", ft.Colors.ORANGE_600)
            print(f"❌ 打开报告失败: {str(e)}")
            print(f"💡 请手动执行命令: {manual_command}")
    
    def refresh_reports_view(self):
        """刷新报告视图"""
        if self.current_view == "web_reports":
            self.main_content_area.content = self.create_web_reports_view()
        elif self.current_view == "mysql_reports":
            self.main_content_area.content = self.create_mysql_reports_view()
        self.page.update()
        self.update_status("报告列表已刷新", ft.Colors.GREEN_600)
    
    def extract_target_url_from_web_report(self, html_file):
        """从Web报告文件中提取目标URL"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找目标URL行
                url_match = re.search(r'<p>目标URL:\s*([^<]+)</p>', content)
                if url_match:
                    return url_match.group(1).strip()
        except Exception as e:
            print(f"提取目标URL失败: {e}")
        return None
        
    def create_button_row(self):
        """创建按钮行"""
        return ft.Row([
            ft.ElevatedButton(
                "清空对话",
                on_click=self.clear_chat,
                bgcolor=ft.Colors.RED_400,
                color=ft.Colors.WHITE
            ),
            ft.ElevatedButton(
                "保存对话",
                on_click=self.save_conversation,
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE
            ),
            ft.ElevatedButton(
                "加载对话",
                on_click=self.load_conversation,
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE
            ),
            ft.ElevatedButton(
                "显示历史",
                on_click=self.show_history,
                bgcolor=ft.Colors.PURPLE_600,
                color=ft.Colors.WHITE
            )
        ], spacing=10)
        
    def add_system_message(self, message):
        """添加系统消息"""
        timestamp = time.strftime("%H:%M:%S")
        
        message_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.COMPUTER, color=ft.Colors.BLUE_600),
                        ft.Text(f"系统 [{timestamp}]", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600)
                    ]),
                    ft.Text(message, color=ft.Colors.BLACK87)
                ], spacing=5),
                padding=15
            ),
            color=ft.Colors.BLUE_50
        )
        
        self.chat_container.controls.append(message_card)
        self.page.update()
        
    def add_user_message(self, message):
        """添加用户消息"""
        timestamp = time.strftime("%H:%M:%S")
        
        message_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=ft.Colors.GREEN_600),
                        ft.Text(f"用户 [{timestamp}]", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600)
                    ]),
                    ft.Text(message, color=ft.Colors.BLACK87)
                ], spacing=5),
                padding=15
            ),
            color=ft.Colors.GREEN_50
        )
        
        self.chat_container.controls.append(message_card)
        self.page.update()
        
    def add_assistant_message(self, message, thinking_process=None, tool_calls=None):
        """添加助手消息"""
        timestamp = time.strftime("%H:%M:%S")
        
        content_column = [
            ft.Row([
                ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.PURPLE_600),
                ft.Text(f"助手 [{timestamp}]", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_600)
            ]),
            ft.Text(message, color=ft.Colors.BLACK87)
        ]
        
        # 如果有思考过程，添加可折叠的思考过程显示
        if thinking_process:
            thinking_text = thinking_process if isinstance(thinking_process, str) else "\n".join(thinking_process)
            content_column.append(
                ft.ExpansionTile(
                    title=ft.Text("思考过程", size=12, color=ft.Colors.ORANGE_600),
                    subtitle=ft.Text("点击查看详细思考过程", size=10),
                    controls=[
                        ft.Container(
                            content=ft.Text(thinking_text, size=11, color=ft.Colors.BLACK54),
                            padding=10,
                            bgcolor=ft.Colors.ORANGE_50,
                            border_radius=5
                        )
                    ]
                )
            )
            
        # 如果有工具调用，添加工具调用显示
        if tool_calls:
            tool_text = "\n".join(tool_calls) if isinstance(tool_calls, list) else str(tool_calls)
            content_column.append(
                ft.ExpansionTile(
                    title=ft.Text("工具调用", size=12, color=ft.Colors.GREEN_600),
                    subtitle=ft.Text("点击查看工具调用详情", size=10),
                    controls=[
                        ft.Container(
                            content=ft.Text(tool_text, size=11, color=ft.Colors.BLACK54),
                            padding=10,
                            bgcolor=ft.Colors.GREEN_50,
                            border_radius=5
                        )
                    ]
                )
            )
        
        message_card = ft.Card(
            content=ft.Container(
                content=ft.Column(content_column, spacing=5),
                padding=15
            ),
            color=ft.Colors.PURPLE_50
        )
        
        self.chat_container.controls.append(message_card)
        self.page.update()
        
    def add_thinking_step(self, step):
        """添加思考步骤"""
        thinking_item = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LIGHTBULB, size=16, color=ft.Colors.ORANGE_600),
                ft.Text(step, size=12, color=ft.Colors.BLACK87)
            ], spacing=5),
            padding=5
        )
        self.thinking_container.controls.append(thinking_item)
        self.page.update()
        
    def add_tool_call(self, tool_info):
        """添加工具调用信息"""
        tool_item = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BUILD, size=16, color=ft.Colors.GREEN_600),
                ft.Text(tool_info, size=12, color=ft.Colors.BLACK87)
            ], spacing=5),
            padding=5
        )
        self.tools_container.controls.append(tool_item)
        self.page.update()
        
    def update_status(self, status, color=ft.Colors.BLACK87):
        """更新状态"""
        self.status_text.value = status
        self.status_text.color = color
        self.page.update()
        
    def send_message(self, e=None):
        """发送消息"""
        if self.is_processing:
            return
            
        message = self.message_input.value.strip()
        if not message:
            return
            
        # 清空输入框
        self.message_input.value = ""
        self.page.update()
        
        # 添加用户消息
        self.add_user_message(message)
        
        # 设置处理状态
        self.is_processing = True
        self.send_button.disabled = True
        self.update_status("正在处理...", ft.Colors.ORANGE_600)
        
        # 清空思考过程和工具调用显示
        self.thinking_container.controls.clear()
        self.tools_container.controls.clear()
        self.page.update()
        
        # 在新线程中处理消息
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
        
    def process_message(self, message):
        """处理用户消息"""
        try:
            start_time = time.time()
            
            # 添加思考步骤
            self.add_thinking_step(f"开始处理用户问题: {message}")
            self.add_tool_call(f"调用智能监控器分析问题")
            
            # 调用智能监控器
            result = self.monitor.smart_query(message)
            
            processing_time = time.time() - start_time
            
            # 在主线程中处理结果
            self.handle_response(result, processing_time)
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            self.handle_error(error_msg)
            
    def handle_response(self, result, processing_time):
        """处理响应结果"""
        try:
            thinking_process = []
            tool_calls = []
            
            if result["type"] == "mcp_analysis":
                # MCP协议分析结果
                protocol = result["protocol"]
                params = result.get("params", {})
                mcp_result = result["mcp_result"]
                analysis = result["analysis"]
                
                # 构建思考过程
                thinking_process.append(f"检测到需要调用MCP协议: {protocol}")
                thinking_process.append(f"协议参数: {params}")
                self.add_thinking_step(f"选择协议: {protocol}")
                self.add_thinking_step(f"设置参数: {params}")
                
                # 构建工具调用信息
                tool_calls.append(f"协议: {protocol}")
                tool_calls.append(f"参数: {params}")
                tool_calls.append(f"状态: {mcp_result.get('status', 'unknown')}")
                self.add_tool_call(f"执行协议: {protocol}")
                self.add_tool_call(f"状态: {mcp_result.get('status', 'unknown')}")
                
                if mcp_result.get('status') == 'success':
                    summary = mcp_result.get('summary', {})
                    if summary.get('key_findings'):
                        tool_calls.append("关键发现:")
                        self.add_tool_call("获取监控结果:")
                        for finding in summary['key_findings']:
                            tool_calls.append(f"  • {finding}")
                            self.add_tool_call(f"• {finding}")
                
                # 添加助手回复
                self.add_assistant_message(analysis, thinking_process, tool_calls)
                
            elif result["type"] == "direct_answer":
                # 直接回答
                thinking_process.append("无需调用监控工具，直接回答")
                self.add_thinking_step("分析问题类型")
                self.add_thinking_step("无需调用监控工具")
                self.add_tool_call("直接回答用户问题")
                self.add_assistant_message(result["answer"], thinking_process)
                
            elif result["type"] == "skywalking_direct_output":
                # SkyWalking直接输出
                protocol = result["protocol"]
                mcp_result = result["mcp_result"]
                
                thinking_process.append(f"检测到微服务相关问题，调用SkyWalking协议")
                thinking_process.append("SkyWalking分析结果已直接输出到终端")
                
                self.add_thinking_step("识别微服务/分布式相关问题")
                self.add_thinking_step(f"调用协议: {protocol}")
                self.add_tool_call(f"执行SkyWalking分析")
                self.add_tool_call(f"状态: {mcp_result.get('status', 'unknown')}")
                
                # 根据执行状态显示不同的消息
                if mcp_result.get("status") == "success":
                    response_msg = f"✅ SkyWalking分布式追踪分析已完成！\n\n📊 分析结果已输出到控制台，请查看终端窗口获取详细信息。\n\n💡 分析包含：\n• 微服务拓扑关系\n• 异常检测结果\n• 根因分析报告\n• 资源依赖关系\n\n等待您的下一个问题..."
                else:
                    response_msg = f"❌ SkyWalking分析执行失败：{mcp_result.get('message', '未知错误')}\n\n请检查SkyWalking服务状态和配置。"
                
                self.add_assistant_message(response_msg, thinking_process)
                
            else:
                # 错误情况
                self.handle_error(result.get("message", "未知错误"))
            
            # 更新状态
            self.update_status(f"处理完成 (耗时: {processing_time:.2f}s)", ft.Colors.GREEN_600)
            
        except Exception as e:
            self.handle_error(f"处理响应时出错: {str(e)}")
        finally:
            # 重新启用发送按钮
            self.is_processing = False
            self.send_button.disabled = False
            self.page.update()
            
    def handle_error(self, error_msg):
        """处理错误"""
        self.add_assistant_message(f"❌ 错误: {error_msg}")
        self.update_status("处理出错", ft.Colors.RED_600)
        self.is_processing = False
        self.send_button.disabled = False
        self.page.update()
        
    def clear_chat(self, e):
        """清空对话"""
        def clear_confirmed(e):
            self.chat_container.controls.clear()
            self.thinking_container.controls.clear()
            self.tools_container.controls.clear()
            self.add_system_message("对话已清空")
            dialog.open = False
            self.page.update()
            
        def cancel_clear(e):
            dialog.open = False
            self.page.update()
            
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认清空"),
            content=ft.Text("确定要清空当前对话吗？"),
            actions=[
                ft.TextButton("取消", on_click=cancel_clear),
                ft.TextButton("确定", on_click=clear_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
    def save_conversation(self, e):
        """保存对话"""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"conversation_{timestamp}.json"
            
            # 构建对话数据
            conversation_data = {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "messages": [],
                "thinking_steps": [],
                "tool_calls": []
            }
            
            # 提取对话内容（简化版本，实际应用中可能需要更复杂的序列化）
            for control in self.chat_container.controls:
                if isinstance(control, ft.Card):
                    # 这里简化处理，实际可能需要更详细的内容提取
                    conversation_data["messages"].append({
                        "type": "message",
                        "content": "消息内容"  # 实际需要从Card中提取具体内容
                    })
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
                
            self.update_status(f"对话已保存到: {filename}", ft.Colors.GREEN_600)
            
        except Exception as e:
            self.update_status(f"保存失败: {str(e)}", ft.Colors.RED_600)
            
    def load_conversation(self, e):
        """加载对话"""
        # 这里可以实现文件选择器，暂时跳过
        self.update_status("加载对话功能待实现", ft.Colors.ORANGE_600)
        
    def show_history(self, e):
        """显示对话历史"""
        def close_history(e):
            history_dialog.open = False
            self.page.update()
            
        # 创建历史显示内容
        history_content = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(10)
        )
        
        # 添加历史记录
        for i, msg in enumerate(self.monitor.conversation_history):
            role = "用户" if msg["role"] == "user" else "助手"
            history_item = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"[{i+1}] {role}", weight=ft.FontWeight.BOLD),
                        ft.Text(msg['content'], size=12)
                    ], spacing=5),
                    padding=10
                )
            )
            history_content.controls.append(history_item)
        
        history_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("对话历史"),
            content=ft.Container(
                content=history_content,
                width=600,
                height=400
            ),
            actions=[
                ft.TextButton("关闭", on_click=close_history)
            ],
        )
        
        self.page.dialog = history_dialog
        history_dialog.open = True
        self.page.update()

def main(page: ft.Page):
    """主函数"""
    app = FletDesktopMonitorApp(page)

if __name__ == "__main__":
    ft.app(target=main)
