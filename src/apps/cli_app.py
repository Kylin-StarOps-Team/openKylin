# -*- coding: utf-8 -*-
"""
智能系统监控助手 - 命令行应用
"""

import sys
import os
import time
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SmartMonitor
from utils import Config, HistoryManager, UIUtils

class CLIMonitorApp:
    def __init__(self):
        # 初始化配置和历史管理
        self.config = Config()
        self.history_manager = HistoryManager()
        
        # 初始化智能监控器
        self.monitor = SmartMonitor(self.config.api_key)
        self.monitor.conversation_history = self.history_manager.conversation_history
        
        # 运行状态
        self.running = True
    
    def print_banner(self):
        """打印应用横幅"""
        print(UIUtils.create_banner())
    
    def print_help(self):
        """打印帮助信息"""
        print(UIUtils.create_help_text())
    
    def print_status(self):
        """显示系统状态"""
        status_text = f"""
📊 系统状态:
• 对话轮次: {self.history_manager.conversation_count}
• 历史文件: {self.history_manager.history_file}
• 运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
• 支持的MCP协议: {len(self.monitor.mcp_protocols)} 个
  - {', '.join(self.monitor.mcp_protocols.keys())}
        """
        print(status_text)
    
    def print_history(self):
        """显示对话历史"""
        if not self.monitor.conversation_history:
            print("📚 暂无对话历史")
            return
        
        print("\n📚 对话历史:")
        print("=" * 60)
        for i in range(0, len(self.monitor.conversation_history), 2):
            if i + 1 < len(self.monitor.conversation_history):
                user_msg = self.monitor.conversation_history[i]["content"]
                assistant_msg = self.monitor.conversation_history[i + 1]["content"]
                
                print(f"[{i//2 + 1}] 🤔 用户: {user_msg[:100]}{'...' if len(user_msg) > 100 else ''}")
                print(f"    🤖 助手: {assistant_msg[:100]}{'...' if len(assistant_msg) > 100 else ''}")
                print("-" * 60)
    
    def clear_conversation(self):
        """清空对话"""
        self.monitor.conversation_history = []
        self.history_manager.conversation_history = []
        self.history_manager.save_history()
        print("🗑️ 对话已清空")
    
    def save_conversation(self):
        """保存对话到文件"""
        filename = self.history_manager.export_history()
        if filename:
            print(f"✅ 对话已保存到: {filename}")
    
    def process_message(self, message):
        """处理用户消息"""
        print(f"\n🤔 用户: {message}")
        print("🤖 AI正在分析...")
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 调用智能监控器
            result = self.monitor.smart_query(message)
            
            # 记录处理时间
            processing_time = time.time() - start_time
            
            # 处理结果
            if result["type"] == "mcp_analysis":
                # MCP协议分析结果
                protocol = result["protocol"]
                params = result.get("params", {})
                mcp_result = result["mcp_result"]
                analysis = result["analysis"]
                
                print(f"🔧 工具调用: {protocol}")
                print(f"📋 参数: {json.dumps(params, ensure_ascii=False)}")
                print(f"📊 状态: {mcp_result.get('status', 'unknown')}")
                
                if mcp_result.get('status') == 'success':
                    summary = mcp_result.get('summary', {})
                    if summary.get('key_findings'):
                        print("🔍 关键发现:")
                        for finding in summary['key_findings']:
                            print(f"  • {finding}")
                
                print(f"🧠 AI分析结果:")
                print(f"   {analysis}")
                print(f"⏱️ 处理时间: {processing_time:.2f}秒")
                
            elif result["type"] == "direct_answer":
                # 直接回答
                print(f"💬 直接回答:")
                print(f"   {result['answer']}")
                print(f"⏱️ 处理时间: {processing_time:.2f}秒")
                
            elif result["type"] == "skywalking_direct_output":
                # SkyWalking直接输出（结果已在smart_monitor中输出）
                print(f"\n✅ {result['message']}")
                print(f"⏱️ 处理时间: {processing_time:.2f}秒")
                print("\n💡 等待下一轮对话...")
                
            else:
                # 错误情况
                print(f"❌ 错误: {result.get('message', '未知错误')}")
            
        except Exception as e:
            print(f"❌ 处理消息时出错: {e}")
    
    def run(self):
        """运行应用"""
        self.print_banner()
        self.print_help()
        
        print("\n🚀 应用已启动，请输入您的问题或命令:")
        print("=" * 60)
        
        while self.running:
            try:
                # 获取用户输入
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command in ['/quit', '/exit']:
                        print("👋 再见！")
                        # 同步历史数据
                        self.history_manager.conversation_history = self.monitor.conversation_history
                        self.history_manager.save_history()
                        self.running = False
                        break
                    elif command == '/help':
                        self.print_help()
                    elif command == '/history':
                        self.print_history()
                    elif command == '/clear':
                        self.clear_conversation()
                    elif command == '/save':
                        self.save_conversation()
                    elif command == '/status':
                        self.print_status()
                    else:
                        print(f"❓ 未知命令: {user_input}")
                        print("输入 /help 查看可用命令")
                
                else:
                    # 处理普通消息
                    self.process_message(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，正在退出...")
                # 同步历史数据
                self.history_manager.conversation_history = self.monitor.conversation_history
                self.history_manager.save_history()
                self.running = False
                break
            except EOFError:
                print("\n\n👋 输入结束，正在退出...")
                # 同步历史数据
                self.history_manager.conversation_history = self.monitor.conversation_history
                self.history_manager.save_history()
                self.running = False
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
        self.history_manager.clear_history()

def main():
    """主函数"""
    try:
        app = CLIMonitorApp()
        app.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 