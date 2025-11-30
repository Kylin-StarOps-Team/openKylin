# -*- coding: utf-8 -*-
"""
智能系统监控助手 - PyQt悬浮球桌面应用
基于原有Flet应用功能，实现悬浮球交互界面
"""

import sys
import os
import time
import json
import threading
import webbrowser
import glob
import re
import platform
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QTabWidget, QMessageBox, QDialog,
    QDialogButtonBox, QSizePolicy, QSpacerItem, QSystemTrayIcon, QMenu,
    QTextBrowser, QLineEdit
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPoint, QSize, 
    QPropertyAnimation, QEasingCurve, QRect, pyqtSlot
)
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, QPen, QFont, QIcon, 
    QPixmap, QPalette, QLinearGradient, QRadialGradient
)

# Markdown支持
try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("[警告] Markdown支持未安装，将使用纯文本显示")
    print("[提示] 安装方法: pip install markdown pygments")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SmartMonitor
from utils import Config, HistoryManager


class IconManager:
    """现代化图标管理类 - Linux兼容的纯文本图标系统"""
    
    # 现代化图标映射表 - 完全使用文本，简约而不失设计感
    ICONS = {
        'web': 'WEB',
        'database': 'DB',
        'refresh': 'REFRESH',
        'time': 'TIME',
        'size': 'SIZE',
        'info': 'INFO',
        'user': 'USER',
        'assistant': 'AI',
        'system': 'SYS',
        'chat': 'CHAT',
        'report': 'REPORT',
        'arrow': '>',
        'close': 'X',
        'check': 'OK',
        'error': 'ERR',
        'warning': 'WARN',
        'success': 'OK',
        'search': 'FIND',
        'settings': 'SET',
        'tool': 'TOOL',
        'analysis': 'SCAN'
    }
    
    # 现代化配色方案
    COLORS = {
        'primary': '#2563eb',      # 现代蓝色
        'secondary': '#64748b',    # 中性灰
        'success': '#10b981',      # 现代绿色
        'warning': '#f59e0b',      # 现代橙色
        'error': '#ef4444',        # 现代红色
        'info': '#06b6d4',         # 现代青色
        'background': '#f8fafc',   # 浅灰背景
        'surface': '#ffffff',      # 白色表面
        'text': '#1e293b',         # 深色文本
        'text_secondary': '#64748b' # 次要文本
    }
    
    @staticmethod
    def get_icon(icon_name):
        """获取图标文本"""
        return IconManager.ICONS.get(icon_name, icon_name.upper())
    
    @staticmethod
    def get_color(color_name):
        """获取主题颜色"""
        return IconManager.COLORS.get(color_name, IconManager.COLORS['text'])
    
    @staticmethod
    def create_icon_button(text, size=24, bg_color=None, text_color=None):
        """创建现代化图标按钮样式的QPixmap"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制现代化背景
        if bg_color:
            painter.setBrush(QBrush(QColor(bg_color)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(0, 0, size, size, size//4, size//4)
        
        # 绘制文本
        painter.setPen(QColor(text_color or IconManager.COLORS['text']))
        font = QFont('SF Pro Display', size//3, QFont.Bold)
        if not font.exactMatch():
            font = QFont('Arial', size//3, QFont.Bold)
        painter.setFont(font)
        
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        
        return pixmap
    
    @staticmethod
    def get_modern_style():
        """获取现代化全局样式表"""
        return f"""
            QWidget {{
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                color: {IconManager.COLORS['text']};
                background-color: {IconManager.COLORS['background']};
            }}
            
            QPushButton {{
                background-color: {IconManager.COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: #1d4ed8;
                transform: translateY(-1px);
            }}
            
            QPushButton:pressed {{
                background-color: #1e40af;
                transform: translateY(0px);
            }}
            
            QPushButton:disabled {{
                background-color: {IconManager.COLORS['secondary']};
                color: #94a3b8;
            }}
            
            QLineEdit, QTextEdit {{
                background-color: {IconManager.COLORS['surface']};
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {IconManager.COLORS['primary']};
                outline: none;
            }}
            
            QLabel {{
                color: {IconManager.COLORS['text']};
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background-color: #f1f5f9;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {IconManager.COLORS['secondary']};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #475569;
            }}
        """


class MarkdownRenderer:
    """Markdown渲染器"""
    
    def __init__(self):
        self.md = None
        if MARKDOWN_AVAILABLE:
            self.md = markdown.Markdown(
                extensions=[
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.toc'
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': True
                    }
                }
            )
    
    def render(self, text):
        """渲染Markdown文本为HTML"""
        if not self.md or not text:
            return self._plain_text_to_html(text)
        
        try:
            # 渲染Markdown
            html = self.md.convert(text)
            
            # 添加CSS样式
            styled_html = f"""
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 10px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2196F3;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                h1 {{ font-size: 24px; }}
                h2 {{ font-size: 20px; }}
                h3 {{ font-size: 18px; }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                }}
                pre {{
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 12px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                blockquote {{
                    border-left: 4px solid #2196F3;
                    margin: 0;
                    padding-left: 16px;
                    color: #666;
                    font-style: italic;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                ul, ol {{
                    padding-left: 24px;
                    margin: 12px 0;
                }}
                li {{
                    margin: 6px 0;
                    line-height: 1.5;
                }}
                ul li {{
                    list-style-type: disc;
                    padding-left: 4px;
                }}
                ul ul li {{
                    list-style-type: circle;
                }}
                ul ul ul li {{
                    list-style-type: square;
                }}
                ol li {{
                    list-style-type: decimal;
                    padding-left: 4px;
                }}
                a {{
                    color: #2196F3;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .highlight {{
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 12px;
                }}
            </style>
            <body>{html}</body>
            """
            
            return styled_html
            
        except Exception as e:
            print(f"Markdown渲染失败: {e}")
            return self._plain_text_to_html(text)
    
    def _plain_text_to_html(self, text):
        """将纯文本转换为HTML"""
        if not text:
            return ""
        
        # 简单的文本到HTML转换
        html = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html = html.replace('\n', '<br>')
        
        # 简单的Markdown风格转换
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)  # 粗体
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)  # 斜体
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)  # 代码
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)  # 标题1
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)  # 标题2
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)  # 标题3
        
        # 处理列表
        lines = html.split('<br>')
        processed_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            # 检查是否是列表项
            if re.match(r'^[•\-\*]\s+', line):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                # 移除列表标记并创建列表项
                content = re.sub(r'^[•\-\*]\s+', '', line)
                processed_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                if line:  # 非空行
                    processed_lines.append(line + '<br>')
        
        # 如果最后还在列表中，关闭列表
        if in_list:
            processed_lines.append('</ul>')
        
        html = ''.join(processed_lines)
        
        return f"""
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 10px;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2196F3;
                margin-top: 16px;
                margin-bottom: 8px;
            }}
            h1 {{ font-size: 20px; }}
            h2 {{ font-size: 18px; }}
            h3 {{ font-size: 16px; }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            }}
            ul, ol {{
                padding-left: 24px;
                margin: 12px 0;
            }}
            li {{
                margin: 6px 0;
                line-height: 1.5;
            }}
            ul li {{
                list-style-type: disc;
                padding-left: 4px;
            }}
            strong {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            em {{
                font-style: italic;
                color: #555;
            }}
        </style>
        <body>{html}</body>
        """


class FloatingBall(QWidget):
    """悬浮球组件"""
    double_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.drag_position = QPoint()
        self.is_dragging = False
        self.hover_scale = 1.0
        self.shadow_opacity = 0.3
        
        # 设置动画
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def init_ui(self):
        """初始化悬浮球界面"""
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置大小和位置 - iOS风格更大一些
        self.setFixedSize(90, 90)
        
        # 默认位置在屏幕右侧中央
        screen = QApplication.desktop().screenGeometry()
        self.move(screen.width() - 110, screen.height() // 2 - 45)
        
    def paintEvent(self, event):
        """绘制现代化悬浮球 - 简约设计风格"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算中心和半径
        center_x, center_y = 45, 45
        radius = 35 * self.hover_scale
        
        # 现代化阴影 - 更加精致
        shadow_offset = 2
        shadow_gradient = QRadialGradient(center_x + shadow_offset, center_y + shadow_offset, radius + 3)
        shadow_gradient.setColorAt(0, QColor(37, 99, 235, int(30 * self.shadow_opacity)))
        shadow_gradient.setColorAt(0.8, QColor(37, 99, 235, int(10 * self.shadow_opacity)))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(shadow_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - radius + shadow_offset), int(center_y - radius + shadow_offset), 
                          int(radius * 2), int(radius * 2))
        
        # 主体设计 - 现代化渐变
        main_gradient = QLinearGradient(0, center_y - radius, 0, center_y + radius)
        if self.hover_scale > 1.0:
            # 悬停时的现代蓝色
            main_gradient.setColorAt(0, QColor(59, 130, 246, 255))   # blue-500
            main_gradient.setColorAt(0.5, QColor(37, 99, 235, 255))  # blue-600
            main_gradient.setColorAt(1, QColor(29, 78, 216, 255))    # blue-700
        else:
            # 正常状态的现代蓝色
            main_gradient.setColorAt(0, QColor(96, 165, 250, 255))   # blue-400
            main_gradient.setColorAt(0.5, QColor(59, 130, 246, 255)) # blue-500
            main_gradient.setColorAt(1, QColor(37, 99, 235, 255))    # blue-600
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2))
        
        # 现代化高光效果
        highlight_gradient = QRadialGradient(center_x - 10, center_y - 10, radius * 0.5)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
        highlight_gradient.setColorAt(0.7, QColor(255, 255, 255, 20))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(int(center_x - radius * 0.6), int(center_y - radius * 0.6), 
                          int(radius * 1.2), int(radius * 1.2))
        
        # 绘制应用标识 - 现代化设计
        painter.setPen(QPen(QColor(255, 255, 255, 255), 2))
        
        # 使用现代字体
        font = QFont("SF Pro Display", 13, QFont.Bold)
        if not font.exactMatch():
            font = QFont("Arial", 13, QFont.Bold)
            
        painter.setFont(font)
        
        # 居中绘制"AI"文字，更加简洁现代
        text_rect = self.rect()
        # 分行显示"Star"和"Ops"
        # 计算上下两行的矩形区域，使其垂直居中排版
        # 让两行更靠近，减小行高
        total_height = text_rect.height()
        line_height = int(total_height * 0.42)  # 比原来略小
        gap = int(total_height * 0.08)          # 两行之间的间隙
        star_rect = QRect(text_rect.left(), text_rect.top() + gap, text_rect.width(), line_height)
        ops_rect = QRect(text_rect.left(), text_rect.top() + line_height + gap, text_rect.width(), line_height)
        painter.drawText(star_rect, Qt.AlignHCenter | Qt.AlignBottom, "Star")
        painter.drawText(ops_rect, Qt.AlignHCenter | Qt.AlignTop, "Ops")
        # painter.drawText(text_rect, Qt.AlignCenter, "StarOps")
        
        # 现代化细边框
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2))
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            # 计算移动距离，如果超过阈值则认为是拖拽
            move_distance = (event.globalPos() - self.drag_position - self.frameGeometry().topLeft()).manhattanLength()
            if move_distance > 5:  # 5像素阈值
                self.is_dragging = True
                self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = QPoint()
            self.is_dragging = False
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton and not self.is_dragging:
            self.double_clicked.emit()
            event.accept()
            
    def enterEvent(self, event):
        """鼠标进入事件 - 添加iOS风格动画"""
        self.hover_scale = 1.1
        self.shadow_opacity = 0.5
        
        # 创建放大动画
        current_geometry = self.geometry()
        target_size = 95
        new_geometry = QRect(
            current_geometry.x() - 2,
            current_geometry.y() - 2,
            target_size,
            target_size
        )
        
        self.scale_animation.setStartValue(current_geometry)
        self.scale_animation.setEndValue(new_geometry)
        self.scale_animation.start()
        
        self.update()
        
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复原大小"""
        self.hover_scale = 1.0
        self.shadow_opacity = 0.3
        
        # 创建缩小动画
        current_geometry = self.geometry()
        target_size = 90
        new_geometry = QRect(
            current_geometry.x() + 2,
            current_geometry.y() + 2,
            target_size,
            target_size
        )
        
        self.scale_animation.setStartValue(current_geometry)
        self.scale_animation.setEndValue(new_geometry)
        self.scale_animation.start()
        
        self.update()


class ChatMessage(QWidget):
    """聊天消息组件"""
    
    def __init__(self, message, sender, timestamp=None, thinking_process=None, tool_calls=None):
        super().__init__()
        self.message = message
        self.sender = sender  # 'user', 'assistant', 'system'
        self.timestamp = timestamp or time.strftime("%H:%M:%S")
        self.thinking_process = thinking_process
        self.tool_calls = tool_calls
        self.markdown_renderer = MarkdownRenderer()
        self.init_ui()
        
    def init_ui(self):
        """初始化现代化消息界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 消息容器
        message_container = QWidget()
        container_layout = QVBoxLayout(message_container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(8)
        
        # 消息头部（发送者和时间）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # 发送者图标和信息
        if self.sender == 'user':
            icon = IconManager.get_icon('user')
            name = "用户"
            primary_color = IconManager.get_color('success')
            bg_color = f"{IconManager.get_color('success')}15"
            align_right = True
        elif self.sender == 'assistant':
            icon = IconManager.get_icon('assistant')
            name = "AI助手"
            primary_color = IconManager.get_color('primary')
            bg_color = f"{IconManager.get_color('primary')}10"
            align_right = False
        else:  # system
            icon = IconManager.get_icon('system')
            name = "系统"
            primary_color = IconManager.get_color('info')
            bg_color = f"{IconManager.get_color('info')}10"
            align_right = False
        
        # 头像
        avatar = QLabel()
        avatar.setText(icon)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {primary_color};
                color: white;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }}
        """)
        avatar.setAlignment(Qt.AlignCenter)
        
        # 发送者信息
        sender_info = QVBoxLayout()
        sender_info.setSpacing(2)
        
        sender_name = QLabel(name)
        sender_name.setStyleSheet(f"""
            font-weight: 600;
            font-size: 14px;
            color: {primary_color};
            margin: 0;
        """)
        
        timestamp = QLabel(self.timestamp)
        timestamp.setStyleSheet(f"""
            font-size: 12px;
            color: {IconManager.get_color('text_secondary')};
            margin: 0;
        """)
        
        sender_info.addWidget(sender_name)
        sender_info.addWidget(timestamp)
        
        if align_right:
            header_layout.addStretch()
            header_layout.addLayout(sender_info)
            header_layout.addWidget(avatar)
        else:
            header_layout.addWidget(avatar)
            header_layout.addLayout(sender_info)
            header_layout.addStretch()
        
        container_layout.addLayout(header_layout)
        
        # 消息内容
        if MARKDOWN_AVAILABLE and self.sender in ['assistant', 'system']:
            content_browser = QTextBrowser()
            content_browser.setHtml(self.markdown_renderer.render(self.message))
            content_browser.setMaximumHeight(600)
            content_browser.setStyleSheet(f"""
                QTextBrowser {{
                    border: none;
                    background-color: transparent;
                    padding: 0;
                    color: {IconManager.get_color('text')};
                }}
            """)
            container_layout.addWidget(content_browser)
        else:
            content_label = QLabel(self.message)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"""
                padding: 0;
                background-color: transparent;
                color: {IconManager.get_color('text')};
                font-size: 14px;
                line-height: 1.5;
            """)
            container_layout.addWidget(content_label)
        
        # 详情按钮
        if self.thinking_process or self.tool_calls:
            details_button = QPushButton(f"{IconManager.get_icon('info')} 查看详情")
            details_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {IconManager.get_color('background')};
                    color: {IconManager.get_color('text_secondary')};
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #f1f5f9;
                    color: {IconManager.get_color('text')};
                }}
            """)
            details_button.clicked.connect(self.show_details)
            container_layout.addWidget(details_button)
        
        # 设置消息容器样式
        message_container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {primary_color}20;
            }}
        """)
        
        layout.addWidget(message_container)
        self.setLayout(layout)
        
    def show_details(self):
        """显示详细信息"""
        dialog = QDialog(self)
        dialog.setWindowTitle("消息详情")
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # 思考过程
        if self.thinking_process:
            thinking_label = QLabel(f"{IconManager.get_icon('info')} 思考过程:")
            thinking_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 14px; margin-bottom: 5px;")
            layout.addWidget(thinking_label)
            
            thinking_browser = QTextBrowser()
            thinking_content = self.thinking_process if isinstance(self.thinking_process, str) else "\n".join(self.thinking_process)
            
            if MARKDOWN_AVAILABLE:
                thinking_browser.setHtml(self.markdown_renderer.render(thinking_content))
            else:
                thinking_browser.setPlainText(thinking_content)
                
            thinking_browser.setMaximumHeight(180)
            thinking_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #fff8e1;
                    border: 1px solid #ffcc02;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            layout.addWidget(thinking_browser)
        
        # 工具调用
        if self.tool_calls:
            tools_label = QLabel(f"{IconManager.get_icon('report')} 工具调用:")
            tools_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px; margin-bottom: 5px;")
            layout.addWidget(tools_label)
            
            tools_browser = QTextBrowser()
            tools_content = "\n".join(self.tool_calls) if isinstance(self.tool_calls, list) else str(self.tool_calls)
            
            if MARKDOWN_AVAILABLE:
                tools_browser.setHtml(self.markdown_renderer.render(tools_content))
            else:
                tools_browser.setPlainText(tools_content)
                
            tools_browser.setMaximumHeight(180)
            tools_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #e8f5e8;
                    border: 1px solid #4CAF50;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            layout.addWidget(tools_browser)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_button = buttons.button(QDialogButtonBox.Close)
        close_button.setText("关闭")
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()


class ProcessingThread(QThread):
    """消息处理线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    thinking_step = pyqtSignal(str)
    tool_call = pyqtSignal(str)
    
    def __init__(self, monitor, message):
        super().__init__()
        self.monitor = monitor
        self.message = message
        
    def run(self):
        """执行消息处理"""
        try:
            self.thinking_step.emit(f"开始处理用户问题: {self.message}")
            self.tool_call.emit(f"调用智能监控器分析问题")
            
            # 调用智能监控器 - 与cli_app.py中的逻辑完全一致
            result = self.monitor.smart_query(self.message)
            
            # 确保返回结果包含所有必要信息
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("智能监控器返回空结果")
            
        except Exception as e:
            import traceback
            error_msg = f"处理消息时出错: {str(e)}\n{traceback.format_exc()}"
            print(f"[DEBUG] ProcessingThread error: {error_msg}")
            self.error.emit(f"处理消息时出错: {str(e)}")


class ChatInterface(QWidget):
    """聊天界面"""
    
    def __init__(self, monitor, history_manager):
        super().__init__()
        self.monitor = monitor
        self.history_manager = history_manager
        self.is_processing = False
        self.processing_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化现代化聊天界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)
        
        # 现代化标题区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # AI图标
        ai_icon = QLabel()
        ai_icon.setText("AI")
        ai_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {IconManager.get_color('primary')};
                color: white;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                min-width: 36px;
                max-width: 36px;
                min-height: 36px;
                max-height: 36px;
            }}
        """)
        ai_icon.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(ai_icon)
        
        # 标题文本
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("智能监控助手")
        title.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: 700; 
            color: {IconManager.get_color('text')};
            margin: 0;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("专业的系统监控与分析服务")
        subtitle.setStyleSheet(f"""
            font-size: 12px; 
            color: {IconManager.get_color('text_secondary')};
            margin: 0;
        """)
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 现代化聊天显示区域
        self.chat_scroll = QScrollArea()
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(16)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_widget.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_widget)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background-color: {IconManager.get_color('surface')};
            }}
        """)
        layout.addWidget(self.chat_scroll)
        
        # 现代化输入区域
        input_container = QWidget()
        input_container.setStyleSheet(f"""
            QWidget {{
                background-color: {IconManager.get_color('surface')};
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 4px;
            }}
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 6, 12, 6)
        input_layout.setSpacing(12)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("请输入您的问题...")
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: transparent;
                font-size: 14px;
                color: {IconManager.get_color('text')};
                selection-background-color: {IconManager.get_color('primary')};
                padding: 8px 0px;
            }}
        """)
        
        # 添加回车键发送功能
        self.message_input.returnPressed.connect(self.send_message)
        
        # 发送按钮
        self.send_button = QPushButton(f"{IconManager.get_icon('arrow')} 发送")
        self.send_button.setFixedSize(80, 36)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {IconManager.get_color('primary')};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
            QPushButton:disabled {{
                background-color: {IconManager.get_color('secondary')};
                color: #94a3b8;
            }}
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_container)
        
        # 现代化状态栏
        self.status_label = QLabel("READY")
        self.status_label.setStyleSheet(f"""
            padding: 8px 16px; 
            background-color: {IconManager.get_color('success')}22; 
            border-radius: 8px; 
            color: {IconManager.get_color('success')};
            font-weight: 600;
            font-size: 12px;
        """)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # 显示欢迎消息
        self.show_welcome_message()
        
    def show_welcome_message(self):
        """显示现代化欢迎消息"""
        welcome_text = """**欢迎使用智能系统监控助手**

**核心功能**
我是您的专业系统运维助手，支持10种强大的监控协议，为您提供全方位的系统监控和安全检测服务。

**系统监控能力**
- CPU 使用率和系统负载监控
- 内存使用情况和性能分析  
- 磁盘IO状态和存储空间监控
- 网络流量和连通性探测
- Prometheus指标收集和分析

**数据库专项服务**
- MySQL数据库性能实时监控
- MySQL配置优化和性能调优
- 生成专业的数据库优化报告

**安全和日志分析**
- Trivy容器和应用安全扫描
- 系统日志分析和异常检测
- Web应用配置和安全检测

**使用方式**
直接输入您的问题，我会智能识别并自动调用最适合的监控工具。例如：

- "检查CPU使用情况"
- "分析MySQL数据库配置优化"  
- "扫描Docker镜像安全漏洞"
- "检测网站配置和性能"

**智能特性**
支持10种监控协议，提供专业级异常评分，让运维工作更高效！"""
        
        self.add_message(welcome_text, 'system')
        
    def add_message(self, message, sender, thinking_process=None, tool_calls=None):
        """添加消息到聊天区域"""
        chat_message = ChatMessage(message, sender, thinking_process=thinking_process, tool_calls=tool_calls)
        self.chat_layout.addWidget(chat_message)
        
        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        """发送消息"""
        if self.is_processing:
            return
            
        message = self.message_input.text().strip()
        if not message:
            return
            
        # 清空输入框
        self.message_input.clear()
        
        # 添加用户消息
        self.add_message(message, 'user')
        
        # 设置处理状态
        self.is_processing = True
        self.send_button.setEnabled(False)
        self.update_status("正在处理...", "#FF9800")
        
        # 启动处理线程
        self.processing_thread = ProcessingThread(self.monitor, message)
        self.processing_thread.finished.connect(self.handle_response)
        self.processing_thread.error.connect(self.handle_error)
        self.processing_thread.thinking_step.connect(lambda step: None)  # 可以添加思考步骤显示
        self.processing_thread.tool_call.connect(lambda call: None)  # 可以添加工具调用显示
        self.processing_thread.start()
        
    def handle_response(self, result):
        """处理响应结果 - 与cli_app.py保持一致的逻辑"""
        try:
            thinking_process = []
            tool_calls = []
            
            print(f"[DEBUG] 收到结果类型: {result.get('type', 'unknown')}")
            
            if result["type"] == "mcp_analysis":
                # MCP协议分析结果 - 与cli_app.py中process_message方法逻辑一致
                protocol = result["protocol"]
                params = result.get("params", {})
                mcp_result = result["mcp_result"]
                analysis = result["analysis"]
                
                # 构建思考过程和工具调用信息
                thinking_process.append(f"检测到需要调用MCP协议: {protocol}")
                thinking_process.append(f"协议参数: {params}")
                thinking_process.append(f"执行状态: {mcp_result.get('status', 'unknown')}")
                
                tool_calls.append(f"TOOL 工具调用: {protocol}")
                tool_calls.append(f"PARAM 参数: {params}")
                tool_calls.append(f"STATUS 状态: {mcp_result.get('status', 'unknown')}")
                
                if mcp_result.get('status') == 'success':
                    summary = mcp_result.get('summary', {})
                    if summary.get('key_findings'):
                        tool_calls.append("FIND 关键发现:")
                        for finding in summary['key_findings']:
                            tool_calls.append(f"  - {finding}")
                
                # 添加助手回复 - 显示AI分析结果
                formatted_response = f"**AI分析结果:**\n\n{analysis}"
                self.add_message(formatted_response, 'assistant', thinking_process, tool_calls)
                
            elif result["type"] == "direct_answer":
                # 直接回答 - 与cli_app.py逻辑一致
                thinking_process.append("无需调用监控工具，AI直接回答")
                formatted_response = f"**直接回答:**\n\n{result['answer']}"
                self.add_message(formatted_response, 'assistant', thinking_process)
                
            elif result["type"] == "skywalking_direct_output":
                # SkyWalking直接输出 - 与cli_app.py逻辑一致
                protocol = result["protocol"]
                mcp_result = result["mcp_result"]
                
                thinking_process.append(f"检测到微服务相关问题，调用SkyWalking协议")
                thinking_process.append("SkyWalking分析结果已直接输出到终端")
                
                tool_calls.append(f"EXEC 执行SkyWalking分析")
                tool_calls.append(f"STATUS 状态: {mcp_result.get('status', 'unknown')}")
                
                # 根据执行状态显示不同的消息 - 与cli_app.py的消息格式保持一致
                if mcp_result.get("status") == "success":
                    response_msg = "**SkyWalking分布式追踪分析已完成！**\n\n分析结果已输出到控制台，请查看终端窗口获取详细信息。\n\n**分析包含：**\n- 微服务拓扑关系\n- 异常检测结果\n- 根因分析报告\n- 资源依赖关系\n\n等待您的下一个问题..."
                else:
                    response_msg = f"**SkyWalking分析执行失败：**\n\n{mcp_result.get('message', '未知错误')}\n\n请检查SkyWalking服务状态和配置。"
                
                self.add_message(response_msg, 'assistant', thinking_process, tool_calls)
                
            elif result["type"] == "error":
                # 错误情况 - 与cli_app.py逻辑一致
                error_msg = f"**处理错误：**\n\n{result.get('message', '未知错误')}"
                self.add_message(error_msg, 'assistant')
                
            else:
                # 未知结果类型
                unknown_msg = f"**未知结果类型：**\n\n{result.get('type', 'unknown')}\n\n{result.get('message', '无详细信息')}"
                self.add_message(unknown_msg, 'assistant')
            
            # 更新状态
            self.update_status("处理完成", "#4CAF50")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[DEBUG] handle_response error: {error_details}")
            self.handle_error(f"处理响应时出错: {str(e)}")
        finally:
            # 重新启用发送按钮
            self.is_processing = False
            self.send_button.setEnabled(True)
            
    def handle_error(self, error_msg):
        """处理错误 - 与cli_app.py的错误格式保持一致"""
        formatted_error = f"**处理消息时出错:**\n\n{error_msg}"
        self.add_message(formatted_error, 'assistant')
        self.update_status("处理出错", "#f44336")
        self.is_processing = False
        self.send_button.setEnabled(True)
        
    def update_status(self, status, color="#4CAF50"):
        """更新状态"""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"padding: 5px; background-color: {color}22; border-radius: 4px; color: {color};")


class ReportCard(QWidget):
    """报告卡片组件 - iOS风格设计"""
    
    def __init__(self, title, subtitle, time, size, extra_info=None, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.init_ui(title, subtitle, time, size, extra_info)
        
    def init_ui(self, title, subtitle, time, size, extra_info):
        """初始化卡片界面"""
        self.setFixedHeight(100)
        self.setCursor(Qt.PointingHandCursor)
        
        # 设置样式 - iOS风格卡片，增强视觉效果
        self.setStyleSheet("""
            ReportCard {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #f0f0f0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }
            ReportCard:hover {
                background-color: #f8f9fa;
                border: 1px solid #e3f2fd;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 左侧图标
        icon_label = QLabel()
        if "Web" in title:
            icon_text = IconManager.get_icon('web')
        else:
            icon_text = IconManager.get_icon('database')
        icon_label.setText(icon_text)
        icon_label.setStyleSheet("""
            font-size: 26px;
            background-color: #f8f9fa;
            border-radius: 22px;
            padding: 10px;
            min-width: 44px;
            max-width: 44px;
            min-height: 44px;
            max-height: 44px;
            border: 1px solid #e9ecef;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 中间内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 17px;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        """)
        content_layout.addWidget(title_label)
        
        # 副标题
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                font-size: 14px;
                color: #6c757d;
                margin: 0;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            """)
            content_layout.addWidget(subtitle_label)
        
        # 时间和大小信息
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        
        time_label = QLabel(f"{IconManager.get_icon('time')} {time}")
        time_label.setStyleSheet("""
            font-size: 13px;
            color: #6c757d;
            background-color: #f1f3f4;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
            border: 1px solid #e9ecef;
        """)
        info_layout.addWidget(time_label)
        
        size_label = QLabel(f"{IconManager.get_icon('size')} {size}")
        size_label.setStyleSheet("""
            font-size: 13px;
            color: #6c757d;
            background-color: #f1f3f4;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
            border: 1px solid #e9ecef;
        """)
        info_layout.addWidget(size_label)
        
        if extra_info:
            extra_label = QLabel(f"{IconManager.get_icon('info')} {extra_info}")
            extra_label.setStyleSheet("""
                font-size: 13px;
                color: #007AFF;
                background-color: #e3f2fd;
                padding: 4px 10px;
                border-radius: 12px;
                font-weight: 500;
                border: 1px solid #bbdefb;
            """)
            info_layout.addWidget(extra_label)
        
        info_layout.addStretch()
        content_layout.addLayout(info_layout)
        
        layout.addLayout(content_layout)
        
        # 右侧箭头
        arrow_label = QLabel(IconManager.get_icon('arrow'))
        arrow_label.setStyleSheet("""
            font-size: 24px;
            color: #c8c9ca;
            font-weight: 300;
            padding: 5px;
        """)
        arrow_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(arrow_label)
        
        self.setLayout(layout)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton and self.file_path:
            self.open_report()
            
    def open_report(self):
        """打开报告"""
        if self.file_path:
            self.open_html_file(self.file_path)
            
    def open_html_file(self, file_path):
        """使用默认浏览器打开HTML文件"""
        try:
            abs_path = os.path.abspath(file_path)
            file_url = f"file://{abs_path}"
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(abs_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_url])
            else:  # Linux and others
                commands = [
                    ["google-chrome", file_url],
                    ["firefox", file_url],
                    ["chromium-browser", file_url],
                    ["xdg-open", file_url]
                ]
                
                opened = False
                for cmd in commands:
                    try:
                        subprocess.run(cmd)
                        opened = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                if not opened:
                    webbrowser.open(file_url)
            
        except Exception as e:
            print(f"[错误] 打开报告失败: {str(e)}")


class ReportsViewer(QWidget):
    """报告查看器"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化报告查看界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题区域 - 更现代的设计
        header_layout = QHBoxLayout()
        
        title = QLabel("检测报告")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 800;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            letter-spacing: -0.5px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮 - iOS风格
        refresh_btn = QPushButton(f"{IconManager.get_icon('refresh')} 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #0056CC;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background-color: #004299;
                transform: scale(0.98);
            }
        """)
        refresh_btn.clicked.connect(self.refresh_all_reports)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 选项卡 - 更简洁的设计
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #f1f3f4;
                color: #6c757d;
                padding: 14px 28px;
                margin-right: 10px;
                border-radius: 22px;
                font-size: 15px;
                font-weight: 600;
                border: 1px solid #e9ecef;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            }
            QTabBar::tab:selected {
                background-color: #007AFF;
                color: white;
                border: 1px solid #007AFF;
                box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
            }
        """)
        
        # Web报告选项卡
        web_tab = self.create_web_reports_tab()
        self.tabs.addTab(web_tab, f"{IconManager.get_icon('web')} Web检测")
        
        # MySQL报告选项卡
        mysql_tab = self.create_mysql_reports_tab()
        self.tabs.addTab(mysql_tab, f"{IconManager.get_icon('database')} MySQL优化")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def refresh_all_reports(self):
        """刷新所有报告"""
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            self.refresh_web_reports()
        else:
            self.refresh_mysql_reports()
        
    def create_web_reports_tab(self):
        """创建Web报告选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(12)
        
        # 报告列表容器
        self.web_reports_scroll = QScrollArea()
        self.web_reports_widget = QWidget()
        self.web_reports_layout = QVBoxLayout()
        self.web_reports_layout.setAlignment(Qt.AlignTop)
        self.web_reports_layout.setSpacing(8)
        self.web_reports_widget.setLayout(self.web_reports_layout)
        self.web_reports_scroll.setWidget(self.web_reports_widget)
        self.web_reports_scroll.setWidgetResizable(True)
        self.web_reports_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #aaaaaa;
            }
        """)
        
        layout.addWidget(self.web_reports_scroll)
        widget.setLayout(layout)
        self.refresh_web_reports()
        return widget
        
    def create_mysql_reports_tab(self):
        """创建MySQL报告选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(12)
        
        # 报告列表容器
        self.mysql_reports_scroll = QScrollArea()
        self.mysql_reports_widget = QWidget()
        self.mysql_reports_layout = QVBoxLayout()
        self.mysql_reports_layout.setAlignment(Qt.AlignTop)
        self.mysql_reports_layout.setSpacing(8)
        self.mysql_reports_widget.setLayout(self.mysql_reports_layout)
        self.mysql_reports_scroll.setWidget(self.mysql_reports_widget)
        self.mysql_reports_scroll.setWidgetResizable(True)
        self.mysql_reports_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #aaaaaa;
            }
        """)
        
        layout.addWidget(self.mysql_reports_scroll)
        widget.setLayout(layout)
        self.refresh_mysql_reports()
        return widget
        
    def refresh_web_reports(self):
        """刷新Web报告列表"""
        # 清空现有内容
        for i in reversed(range(self.web_reports_layout.count())):
            child = self.web_reports_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
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
                    report_title = "Web配置检测"
                    subtitle = target_url if target_url else "配置安全检测"
                    
                    # 创建报告卡片
                    report_card = ReportCard(
                        title=report_title,
                        subtitle=subtitle,
                        time=formatted_time,
                        size=f"{size_mb:.1f}MB",
                        file_path=html_file
                    )
                    self.web_reports_layout.addWidget(report_card)
            else:
                # 没有找到报告文件
                empty_widget = QWidget()
                empty_layout = QVBoxLayout()
                empty_layout.setAlignment(Qt.AlignCenter)
                empty_layout.setSpacing(16)
                
                empty_icon = QLabel(IconManager.get_icon('web'))
                empty_icon.setAlignment(Qt.AlignCenter)
                empty_icon.setStyleSheet("""
                    font-size: 48px;
                    color: #c8c9ca;
                    margin-bottom: 8px;
                """)
                
                empty_title = QLabel("暂无Web检测报告")
                empty_title.setAlignment(Qt.AlignCenter)
                empty_title.setStyleSheet("""
                    font-size: 18px;
                    font-weight: 600;
                    color: #6c757d;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                """)
                
                empty_desc = QLabel("进行Web配置检测后，报告将显示在这里")
                empty_desc.setAlignment(Qt.AlignCenter)
                empty_desc.setStyleSheet("""
                    font-size: 14px;
                    color: #9ca3af;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                """)
                
                empty_layout.addWidget(empty_icon)
                empty_layout.addWidget(empty_title)
                empty_layout.addWidget(empty_desc)
                empty_widget.setLayout(empty_layout)
                
                empty_container = QWidget()
                empty_container.setStyleSheet("""
                    background-color: #f8f9fa;
                    border-radius: 16px;
                    border: 2px dashed #e9ecef;
                    padding: 60px 40px;
                """)
                container_layout = QVBoxLayout()
                container_layout.addWidget(empty_widget)
                empty_container.setLayout(container_layout)
                
                self.web_reports_layout.addWidget(empty_container)
                
        except Exception as e:
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_layout.setAlignment(Qt.AlignCenter)
            error_layout.setSpacing(12)
            
            error_icon = QLabel(IconManager.get_icon('error'))
            error_icon.setAlignment(Qt.AlignCenter)
            error_icon.setStyleSheet("""
                font-size: 40px;
                color: #dc3545;
                margin-bottom: 8px;
            """)
            
            error_title = QLabel("加载报告失败")
            error_title.setAlignment(Qt.AlignCenter)
            error_title.setStyleSheet("""
                font-size: 16px;
                font-weight: 600;
                color: #dc3545;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            """)
            
            error_desc = QLabel(f"错误信息: {str(e)}")
            error_desc.setAlignment(Qt.AlignCenter)
            error_desc.setWordWrap(True)
            error_desc.setStyleSheet("""
                font-size: 13px;
                color: #6c757d;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            """)
            
            error_layout.addWidget(error_icon)
            error_layout.addWidget(error_title)
            error_layout.addWidget(error_desc)
            error_widget.setLayout(error_layout)
            
            error_container = QWidget()
            error_container.setStyleSheet("""
                background-color: #fff5f5;
                border-radius: 16px;
                border: 2px solid #fecaca;
                padding: 40px 30px;
            """)
            container_layout = QVBoxLayout()
            container_layout.addWidget(error_widget)
            error_container.setLayout(container_layout)
            
            self.web_reports_layout.addWidget(error_container)
        
    def refresh_mysql_reports(self):
        """刷新MySQL报告列表"""
        # 清空现有内容
        for i in reversed(range(self.mysql_reports_layout.count())):
            child = self.mysql_reports_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
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
                    
                    # 创建报告卡片
                    report_card = ReportCard(
                        title=f"MySQL优化报告 #{detection_num}",
                        subtitle="数据库性能配置优化",
                        time=modified_time,
                        size=f"{size_kb:.1f}KB",
                        extra_info=f"{suggestions_count}条建议",
                        file_path=html_file
                    )
                    self.mysql_reports_layout.addWidget(report_card)
            else:
                # 没有找到报告文件
                empty_widget = QWidget()
                empty_layout = QVBoxLayout()
                empty_layout.setAlignment(Qt.AlignCenter)
                empty_layout.setSpacing(16)
                
                empty_icon = QLabel(IconManager.get_icon('database'))
                empty_icon.setAlignment(Qt.AlignCenter)
                empty_icon.setStyleSheet("""
                    font-size: 48px;
                    color: #c8c9ca;
                    margin-bottom: 8px;
                """)
                
                empty_title = QLabel("暂无MySQL优化报告")
                empty_title.setAlignment(Qt.AlignCenter)
                empty_title.setStyleSheet("""
                    font-size: 18px;
                    font-weight: 600;
                    color: #6c757d;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                """)
                
                empty_desc = QLabel("进行MySQL配置优化检测后，报告将显示在这里")
                empty_desc.setAlignment(Qt.AlignCenter)
                empty_desc.setStyleSheet("""
                    font-size: 14px;
                    color: #9ca3af;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                """)
                
                empty_layout.addWidget(empty_icon)
                empty_layout.addWidget(empty_title)
                empty_layout.addWidget(empty_desc)
                empty_widget.setLayout(empty_layout)
                
                empty_container = QWidget()
                empty_container.setStyleSheet("""
                    background-color: #f8f9fa;
                    border-radius: 16px;
                    border: 2px dashed #e9ecef;
                    padding: 60px 40px;
                """)
                container_layout = QVBoxLayout()
                container_layout.addWidget(empty_widget)
                empty_container.setLayout(container_layout)
                
                self.mysql_reports_layout.addWidget(empty_container)
                
        except Exception as e:
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_layout.setAlignment(Qt.AlignCenter)
            error_layout.setSpacing(12)
            
            error_icon = QLabel(IconManager.get_icon('error'))
            error_icon.setAlignment(Qt.AlignCenter)
            error_icon.setStyleSheet("""
                font-size: 40px;
                color: #dc3545;
                margin-bottom: 8px;
            """)
            
            error_title = QLabel("加载报告失败")
            error_title.setAlignment(Qt.AlignCenter)
            error_title.setStyleSheet("""
                font-size: 16px;
                font-weight: 600;
                color: #dc3545;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            """)
            
            error_desc = QLabel(f"错误信息: {str(e)}")
            error_desc.setAlignment(Qt.AlignCenter)
            error_desc.setWordWrap(True)
            error_desc.setStyleSheet("""
                font-size: 13px;
                color: #6c757d;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            """)
            
            error_layout.addWidget(error_icon)
            error_layout.addWidget(error_title)
            error_layout.addWidget(error_desc)
            error_widget.setLayout(error_layout)
            
            error_container = QWidget()
            error_container.setStyleSheet("""
                background-color: #fff5f5;
                border-radius: 16px;
                border: 2px solid #fecaca;
                padding: 40px 30px;
            """)
            container_layout = QVBoxLayout()
            container_layout.addWidget(error_widget)
            error_container.setLayout(container_layout)
            
            self.mysql_reports_layout.addWidget(error_container)
        
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


class MainWindow(QWidget):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.history_manager = HistoryManager()
        
        # 初始化智能监控器
        self.monitor = SmartMonitor(self.config.api_key)
        self.monitor.conversation_history = self.history_manager.conversation_history
        
        self.init_ui()
        
    def init_ui(self):
        """初始化现代化主窗口界面"""
        self.setWindowTitle("智能系统监控助手")
        self.setWindowIcon(QIcon())
        self.resize(1000, 750)
        
        # 应用现代化全局样式
        self.setStyleSheet(IconManager.get_modern_style())
        
        # 创建现代化选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: {IconManager.get_color('surface')};
                margin-top: 8px;
            }}
            QTabBar::tab {{
                background-color: {IconManager.get_color('background')};
                color: {IconManager.get_color('text_secondary')};
                padding: 12px 24px;
                margin-right: 4px;
                border: 1px solid #e2e8f0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {IconManager.get_color('surface')};
                color: {IconManager.get_color('primary')};
                border-color: #e2e8f0;
                border-bottom: 2px solid {IconManager.get_color('primary')};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #f8fafc;
                color: {IconManager.get_color('text')};
            }}
        """)
        
        # 聊天选项卡
        self.chat_interface = ChatInterface(self.monitor, self.history_manager)
        self.tabs.addTab(self.chat_interface, f"{IconManager.get_icon('chat')}")
        
        # 报告选项卡
        self.reports_viewer = ReportsViewer()
        self.tabs.addTab(self.reports_viewer, f"{IconManager.get_icon('report')}")
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # 窗口居中
        self.center_window()
        
    def center_window(self):
        """窗口居中"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 同步历史数据
            self.history_manager.conversation_history = self.monitor.conversation_history
            self.history_manager.save_history()
            # 清理历史
            self.history_manager.clear_history()
        except Exception as ex:
            print(f"关闭时清理历史数据失败: {ex}")
        
        # 隐藏主窗口并显示悬浮球
        self.hide()
        # 显示悬浮球
        if hasattr(self, 'floating_ball') and self.floating_ball:
            self.floating_ball.show()
        
        event.ignore()  # 不关闭应用，只是隐藏窗口


class FloatingBallApp:
    """悬浮球应用主类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # 防止关闭主窗口时退出应用
        
        # 创建悬浮球
        self.floating_ball = FloatingBall()
        self.floating_ball.double_clicked.connect(self.show_main_window)
        
        # 创建主窗口（初始隐藏）
        self.main_window = MainWindow()
        # 将悬浮球引用传递给主窗口
        self.main_window.floating_ball = self.floating_ball
        
        # 创建系统托盘
        self.create_tray_icon()
        
    def create_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("显示主界面")
        show_action.triggered.connect(self.show_main_window)
        
        hide_action = tray_menu.addAction("隐藏主界面")
        hide_action.triggered.connect(self.hide_main_window)
        
        tray_menu.addSeparator()
        
        show_ball_action = tray_menu.addAction("显示悬浮球")
        show_ball_action.triggered.connect(self.show_floating_ball)
        
        hide_ball_action = tray_menu.addAction("隐藏悬浮球")
        hide_ball_action.triggered.connect(self.hide_floating_ball)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置托盘图标（使用简单的文字图标）
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(64, 158, 255))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        self.tray_icon.show()
        
    def show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        # 隐藏悬浮球
        self.floating_ball.hide()
        
    def hide_main_window(self):
        """隐藏主窗口"""
        self.main_window.hide()
        # 显示悬浮球
        self.floating_ball.show()
        
    def show_floating_ball(self):
        """显示悬浮球"""
        self.floating_ball.show()
        
    def hide_floating_ball(self):
        """隐藏悬浮球"""
        self.floating_ball.hide()
        
    def quit_app(self):
        """退出应用"""
        self.floating_ball.close()
        self.main_window.close()
        self.tray_icon.hide()
        self.app.quit()
        
    def run(self):
        """运行应用"""
        # 显示悬浮球
        self.floating_ball.show()
        
        # 运行应用
        sys.exit(self.app.exec_())


def main():
    """主函数"""
    app = FloatingBallApp()
    app.run()


if __name__ == "__main__":
    main()
