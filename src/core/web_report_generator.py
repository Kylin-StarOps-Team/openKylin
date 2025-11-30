#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web配置检测报告生成器
集成到fletMCP项目中，负责生成HTML格式的可视化报告
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
import logging
from jinja2 import Template

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebReportGenerator:
    """Web配置检测报告生成器"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
    
    def _get_html_template(self) -> str:
        """获取HTML报告模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web配置检测报告</title>
    <style>
        :root {
            --critical: #e74c3c;
            --high: #e67e22;
            --medium: #f1c40f;
            --low: #2ecc71;
            --bg-light: #f8f9fa;
            --border-color: #dee2e6;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: var(--bg-light);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
        }
        
        .critical-bg { 
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
            color: white;
        }
        
        .high-bg { 
            background: linear-gradient(135deg, #ffa726, #ff9800);
            color: white;
        }
        
        .medium-bg { 
            background: linear-gradient(135deg, #ffd54f, #ffc107);
            color: #333;
        }
        
        .low-bg { 
            background: linear-gradient(135deg, #66bb6a, #4caf50);
            color: white;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .issues-container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .issues-header {
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .issues-header h2 {
            font-size: 1.8em;
            color: #2c3e50;
        }
        
        .issue-card {
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 5px solid;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            transition: transform 0.2s;
        }
        
        .issue-card:hover {
            transform: translateX(5px);
        }
        
        .issue-card.critical { border-color: var(--critical); }
        .issue-card.high { border-color: var(--high); }
        .issue-card.medium { border-color: var(--medium); }
        .issue-card.low { border-color: var(--low); }
        
        .issue-header {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid var(--border-color);
        }
        
        .issue-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        
        .issue-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #666;
        }
        
        .severity-badge {
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .severity-badge.critical { background-color: var(--critical); color: white; }
        .severity-badge.high { background-color: var(--high); color: white; }
        .severity-badge.medium { background-color: var(--medium); color: #333; }
        .severity-badge.low { background-color: var(--low); color: white; }
        
        .issue-content {
            padding: 20px;
        }
        
        .solution {
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .solution h4 {
            color: #2e7d32;
            margin-bottom: 10px;
        }
        
        .solution pre {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.4;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            border-top: 1px solid var(--border-color);
        }
        
        .no-issues {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .no-issues h3 {
            color: var(--low);
            margin-bottom: 10px;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .summary-stats { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web配置检测报告</h1>
            <p>生成时间: {{ timestamp }}</p>
            <p>目标URL: {{ target_url }}</p>
            <p>检测模式: {{ scan_mode }}</p>
        </div>
        
        <div class="summary-stats">
            <div class="stat-card critical-bg">
                <div class="stat-value">{{ critical_count }}</div>
                <div class="stat-label">危急问题</div>
            </div>
            <div class="stat-card high-bg">
                <div class="stat-value">{{ high_count }}</div>
                <div class="stat-label">高危问题</div>
            </div>
            <div class="stat-card medium-bg">
                <div class="stat-value">{{ medium_count }}</div>
                <div class="stat-label">中等问题</div>
            </div>
            <div class="stat-card low-bg">
                <div class="stat-value">{{ low_count }}</div>
                <div class="stat-label">低危问题</div>
            </div>
        </div>
        
        <div class="issues-container">
            <div class="issues-header">
                <h2>检测结果详情</h2>
            </div>
            
            {% if suggestions %}
                {% for issue in suggestions %}
                <div class="issue-card {{ issue.severity }}">
                    <div class="issue-header">
                        <div class="issue-title">{{ issue.category }} · {{ issue.issue }}</div>
                        <div class="issue-meta">
                            <span class="severity-badge {{ issue.severity }}">{{ issue.severity }}</span>
                            <span>分类: {{ issue.category }}</span>
                        </div>
                    </div>
                    <div class="issue-content">
                        {% if issue.description %}
                        <p style="margin-bottom: 15px;">{{ issue.description }}</p>
                        {% endif %}
                        
                        {% if issue.current and issue.recommended %}
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                            <p><strong>当前配置:</strong> {{ issue.current }}</p>
                            <p><strong>推荐配置:</strong> {{ issue.recommended }}</p>
                        </div>
                        {% endif %}
                        
                        {% if issue.solution %}
                        <div class="solution">
                            <h4>解决方案:</h4>
                            <pre>{{ issue.solution }}</pre>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-issues">
                    <h3>🎉 恭喜！</h3>
                    <p>未发现需要优化的配置问题，您的Web应用配置已经很完善了！</p>
                </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>本报告由fletMCP Web配置检测工具生成</p>
            <p>建议定期运行检测以保持最佳配置状态</p>
        </div>
    </div>
</body>
</html>
        """
    
    def generate_html_report(self, summary: Dict[str, Any], suggestions: List[Dict], 
                           target_url: str, scan_mode: str) -> str:
        """生成HTML格式的报告"""
        logger.info("生成Web配置检测HTML报告...")
        
        try:
            # 统计各级别问题数量
            severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for suggestion in suggestions:
                severity = suggestion.get('severity', 'low').lower()
                if severity in severity_count:
                    severity_count[severity] += 1
            
            # 准备模板数据
            template_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": target_url,
                "scan_mode": scan_mode,
                "critical_count": severity_count["critical"],
                "high_count": severity_count["high"],
                "medium_count": severity_count["medium"],
                "low_count": severity_count["low"],
                "suggestions": suggestions
            }
            
            # 渲染模板
            template = Template(self.html_template)
            html_content = template.render(**template_data)
            
            return html_content
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
    
    def save_html_report(self, html_content: str, output_file: str) -> str:
        """保存HTML报告到指定文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Web配置检测报告已保存到: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"保存HTML报告失败: {e}")
            raise
    
    def generate_and_save_report(self, summary: Dict[str, Any], suggestions: List[Dict], 
                               target_url: str, scan_mode: str, 
                               output_dir: str = "reports") -> str:
        """生成并保存报告的便捷方法"""
        try:
            # 生成HTML内容
            html_content = self.generate_html_report(summary, suggestions, target_url, scan_mode)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"web_config_report_{timestamp}.html"
            output_file = os.path.join(output_dir, filename)
            
            # 保存文件
            return self.save_html_report(html_content, output_file)
            
        except Exception as e:
            logger.error(f"生成和保存报告失败: {e}")
            raise