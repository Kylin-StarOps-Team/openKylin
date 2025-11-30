# -*- coding: utf-8 -*-
"""
智能系统监控助手 - 桌面应用
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SmartMonitor
from utils import Config, HistoryManager, UIUtils

class DesktopMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能系统监控助手 - 桌面版")
        
        # 初始化配置和历史管理
        self.config = Config()
        self.history_manager = HistoryManager()
        
        # 设置窗口大小
        window_width = self.config.ui_config.get('window_width', 1200)
        window_height = self.config.ui_config.get('window_height', 800)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化智能监控器
        self.monitor = SmartMonitor(self.config.api_key)
        self.monitor.conversation_history = self.history_manager.conversation_history
        
        # 创建界面
        self.create_widgets()
        
        # 绑定回车键发送消息
        self.root.bind('<Return>', self.send_message)
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="智能系统监控助手", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 创建左右分栏
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：对话区域
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)
        
        # 对话显示区域
        chat_frame = ttk.LabelFrame(left_frame, text="对话区域", padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = UIUtils.create_chat_display(chat_frame)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_input = ttk.Entry(input_frame, font=('Arial', 11))
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_button = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 右侧：工具调用和状态区域
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # 工具调用链显示
        tools_frame = ttk.LabelFrame(right_frame, text="工具调用链", padding=10)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tools_display = UIUtils.create_tools_display(tools_frame)
        self.tools_display.pack(fill=tk.BOTH, expand=True)
        
        # 状态信息
        status_frame = ttk.LabelFrame(right_frame, text="状态信息", padding=10)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="就绪", font=('Arial', 10))
        self.status_label.pack()
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="清空对话", command=self.clear_chat).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="保存对话", command=self.save_conversation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="加载对话", command=self.load_conversation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="显示历史", command=self.show_history).pack(side=tk.LEFT)
        
        # 显示欢迎信息
        self.add_system_message("欢迎使用智能系统监控助手！\n\n"
                               "我可以帮您监控系统状态，包括：\n"
                               "• CPU使用率和系统负载\n"
                               "• 内存使用情况\n"
                               "• 磁盘IO状态和存储空间\n"
                               "• 网络流量和连通性探测\n"
                               "• MySQL数据库性能监控\n"
                               "• 系统日志分析和异常检测\n"
                               "• 安全漏洞扫描\n\n"
                               "支持7种监控协议，提供十级制异常评分。\n"
                               "请直接输入您的问题，我会自动调用相应的监控工具。")
    
    def add_system_message(self, message):
        """添加系统消息到对话区域"""
        timestamp = time.strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] 系统: {message}\n\n")
        self.chat_display.see(tk.END)
    
    def add_user_message(self, message):
        """添加用户消息到对话区域"""
        timestamp = time.strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] 用户: {message}\n")
        self.chat_display.see(tk.END)
    
    def add_assistant_message(self, message, thinking_process=None, tool_calls=None):
        """添加助手消息到对话区域"""
        UIUtils.add_message_with_timestamp(
            self.chat_display, "助手", message, thinking_process, tool_calls
        )
    
    def update_tools_display(self, tool_info):
        """更新工具调用链显示"""
        UIUtils.update_tools_display(self.tools_display, tool_info)
    
    def update_status(self, status):
        """更新状态信息"""
        self.status_label.config(text=status)
    
    def send_message(self, event=None):
        """发送消息"""
        message = self.message_input.get().strip()
        if not message:
            return
        
        # 清空输入框
        self.message_input.delete(0, tk.END)
        
        # 添加用户消息
        self.add_user_message(message)
        
        # 禁用发送按钮，防止重复发送
        self.send_button.config(state='disabled')
        self.update_status("正在处理...")
        
        # 在新线程中处理请求
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        """处理用户消息"""
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 更新工具调用显示
            self.update_tools_display(f"开始处理用户问题: {message}")
            
            # 调用智能监控器
            result = self.monitor.smart_query(message)
            
            # 记录处理时间
            processing_time = time.time() - start_time
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.handle_response(result, processing_time))
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            self.root.after(0, lambda: self.handle_error(error_msg))
    
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
                
                # 构建工具调用信息
                tool_calls.append(f"协议: {protocol}")
                tool_calls.append(f"参数: {params}")
                tool_calls.append(f"状态: {mcp_result.get('status', 'unknown')}")
                
                if mcp_result.get('status') == 'success':
                    summary = mcp_result.get('summary', {})
                    if summary.get('key_findings'):
                        tool_calls.append("关键发现:")
                        for finding in summary['key_findings']:
                            tool_calls.append(f"  • {finding}")
                
                # 更新工具调用显示
                self.update_tools_display(f"执行MCP协议: {protocol} (耗时: {processing_time:.2f}s)")
                
                # 添加助手回复
                self.add_assistant_message(analysis, "\n".join(thinking_process), tool_calls)
                
            elif result["type"] == "direct_answer":
                # 直接回答
                thinking_process.append("无需调用监控工具，直接回答")
                self.update_tools_display(f"直接回答 (耗时: {processing_time:.2f}s)")
                self.add_assistant_message(result["answer"], "\n".join(thinking_process))
                
            else:
                # 错误情况
                self.handle_error(result.get("message", "未知错误"))
            
            # 更新状态
            self.update_status(f"处理完成 (耗时: {processing_time:.2f}s)")
            
        except Exception as e:
            self.handle_error(f"处理响应时出错: {str(e)}")
        finally:
            # 重新启用发送按钮
            self.send_button.config(state='normal')
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.add_assistant_message(f"❌ 错误: {error_msg}")
        self.update_status("处理出错")
        self.send_button.config(state='normal')
    
    def clear_chat(self):
        """清空对话"""
        if UIUtils.show_confirm_dialog("确认", "确定要清空当前对话吗？"):
            self.chat_display.delete(1.0, tk.END)
            self.tools_display.delete(1.0, tk.END)
            self.add_system_message("对话已清空")
    
    def save_conversation(self):
        """保存对话"""
        try:
            filename = UIUtils.show_file_dialog(
                "保存对话",
                [("文本文件", "*.txt"), ("所有文件", "*.*")],
                save=True
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== 智能系统监控助手 - 对话记录 ===\n\n")
                    f.write(f"保存时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("对话内容:\n")
                    f.write(self.chat_display.get(1.0, tk.END))
                    f.write("\n\n工具调用链:\n")
                    f.write(self.tools_display.get(1.0, tk.END))
                
                UIUtils.show_info_dialog("成功", f"对话已保存到: {filename}")
        except Exception as e:
            UIUtils.show_error_dialog("错误", f"保存失败: {str(e)}")
    
    def load_conversation(self):
        """加载对话"""
        try:
            filename = UIUtils.show_file_dialog(
                "加载对话",
                [("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 清空当前显示
                self.chat_display.delete(1.0, tk.END)
                self.tools_display.delete(1.0, tk.END)
                
                # 简单解析并显示内容
                lines = content.split('\n')
                in_tools_section = False
                
                for line in lines:
                    if "工具调用链:" in line:
                        in_tools_section = True
                        continue
                    
                    if in_tools_section:
                        self.tools_display.insert(tk.END, line + '\n')
                    else:
                        self.chat_display.insert(tk.END, line + '\n')
                
                UIUtils.show_info_dialog("成功", f"对话已从文件加载: {filename}")
        except Exception as e:
            UIUtils.show_error_dialog("错误", f"加载失败: {str(e)}")
    
    def show_history(self):
        """显示对话历史"""
        history_window = tk.Toplevel(self.root)
        history_window.title("对话历史")
        history_window.geometry("800x600")
        
        history_text = UIUtils.create_chat_display(history_window)
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示对话历史
        history_text.insert(tk.END, "=== 对话历史 ===\n\n")
        for i, msg in enumerate(self.monitor.conversation_history):
            role = "用户" if msg["role"] == "user" else "助手"
            history_text.insert(tk.END, f"[{i+1}] {role}: {msg['content']}\n\n")
        
        history_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        # 同步历史数据
        self.history_manager.conversation_history = self.monitor.conversation_history
        self.history_manager.save_history()
        self.root.destroy()

def main():
    """主函数"""
    # 检查GUI环境
    if not UIUtils.check_gui_environment():
        print("❌ 无法启动图形界面，当前环境不支持GUI")
        print("请在有图形界面的环境中运行此应用")
        print("或者使用命令行版本: python3 cli_app.py")
        return
    
    try:
        root = tk.Tk()
        app = DesktopMonitorApp(root)
        
        # 设置关闭窗口的处理
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # 启动应用
        root.mainloop()
        
    except Exception as e:
        print(f"启动桌面应用失败: {e}")
        print("请检查依赖和环境配置")

if __name__ == "__main__":
    main() 