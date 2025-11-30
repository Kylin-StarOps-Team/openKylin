# -*- coding: utf-8 -*-
"""
对话历史管理模块
"""

import os
import json
from datetime import datetime

class HistoryManager:
    """对话历史管理类"""
    
    def __init__(self, history_file="conversation_history.json"):
        self.history_file = history_file
        self.conversation_history = []
        self.load_history()
    
    def load_history(self):
        """加载对话历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.conversation_history = history_data.get('conversation_history', [])
                print(f"[成功] 已加载 {len(self.conversation_history)//2} 轮对话历史")
        except Exception as e:
            print(f"[警告] 加载对话历史失败: {e}")
    
    def save_history(self):
        """保存对话历史"""
        try:
            history_data = {
                'conversation_history': self.conversation_history,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[错误] 保存对话历史失败: {e}")
    
    def add_conversation(self, user_question, assistant_response):
        """添加对话"""
        self.conversation_history.append({"role": "user", "content": user_question})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        self.save_history()
    
    def get_history_summary(self, max_items=10):
        """获取对话历史摘要"""
        if not self.conversation_history:
            return "暂无对话历史"
        
        summary = []
        for i in range(0, len(self.conversation_history), 2):
            if i + 1 < len(self.conversation_history):
                user_msg = self.conversation_history[i]["content"]
                assistant_msg = self.conversation_history[i + 1]["content"]
                summary.append(f"Q: {user_msg[:100]}...")
                summary.append(f"A: {assistant_msg[:100]}...")
        
        return "\n".join(summary[-max_items:])
    
    def export_history(self, filename=None):
        """导出对话历史"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== 智能系统监控助手 - 对话记录 ===\n\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("对话内容:\n")
                
                for i in range(0, len(self.conversation_history), 2):
                    if i + 1 < len(self.conversation_history):
                        user_msg = self.conversation_history[i]["content"]
                        assistant_msg = self.conversation_history[i + 1]["content"]
                        f.write(f"用户: {user_msg}\n")
                        f.write(f"助手: {assistant_msg}\n\n")
            
            print(f"[成功] 对话历史已导出到: {filename}")
            return filename
        except Exception as e:
            print(f"[错误] 导出失败: {e}")
            return None
    
    def import_history(self, filename):
        """导入对话历史"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单解析文本文件
            lines = content.split('\n')
            new_history = []
            
            for line in lines:
                if line.startswith('用户: '):
                    new_history.append({
                        "role": "user",
                        "content": line[3:].strip()
                    })
                elif line.startswith('助手: '):
                    new_history.append({
                        "role": "assistant", 
                        "content": line[3:].strip()
                    })
            
            if new_history:
                self.conversation_history = new_history
                self.save_history()
                print(f"[成功] 已导入 {len(new_history)//2} 轮对话")
                return True
            else:
                print("[错误] 未找到有效的对话内容")
                return False
                
        except Exception as e:
            print(f"[错误] 导入失败: {e}")
            return False
    
    @property
    def conversation_count(self):
        """获取对话轮次"""
        return len(self.conversation_history) // 2 