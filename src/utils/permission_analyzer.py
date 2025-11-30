#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ansible脚本权限分析器
用于分析ansible-autofix脚本中涉及的权限操作
"""

import os
import re
import json
from typing import Dict, List, Set

class PermissionAnalyzer:
    """分析Ansible脚本权限需求"""
    
    def __init__(self):
        # 定义权限操作模式
        self.permission_patterns = {
            'file_write': {
                'patterns': [
                    r'echo\s+.*\s*>\s*/proc/',  # 写入proc文件系统
                    r'echo\s+.*\s*>\s*/sys/',   # 写入sys文件系统
                    r'>\s*/proc/',              # 直接重定向到proc
                    r'>\s*/sys/',               # 直接重定向到sys
                ],
                'description': '修改系统文件',
                'risk_level': 'high'
            },
            'file_delete': {
                'patterns': [
                    r'find\s+.*-delete',        # find删除文件
                    r'rm\s+-[rf]+',             # rm删除文件/目录
                    r'docker\s+.*prune.*-f',    # docker清理
                ],
                'description': '删除文件或目录',
                'risk_level': 'high'
            },
            'process_kill': {
                'patterns': [
                    r'kill\s+-[0-9]+',          # 发送信号
                    r'kill\s+-[A-Z]+',          # 发送命名信号
                    r'killall',                 # 批量杀进程
                ],
                'description': '终止系统进程',
                'risk_level': 'medium'
            },
            'service_control': {
                'patterns': [
                    r'systemctl\s+(start|stop|restart|reload)',
                    r'service\s+.*\s+(start|stop|restart)',
                ],
                'description': '控制系统服务',
                'risk_level': 'medium'
            },
            'package_management': {
                'patterns': [
                    r'apt-get\s+.*clean',
                    r'yum\s+.*clean',
                    r'docker\s+.*prune',
                ],
                'description': '管理软件包或容器',
                'risk_level': 'medium'
            },
            'network_access': {
                'patterns': [
                    r'curl\s+.*http',
                    r'wget\s+.*http',
                ],
                'description': '网络访问',
                'risk_level': 'low'
            },
            'memory_management': {
                'patterns': [
                    r'swapoff|swapon',
                    r'/proc/sys/vm/',
                ],
                'description': '内存管理操作',
                'risk_level': 'high'
            }
        }
    
    def analyze_script_permissions(self, script_path: str) -> Dict:
        """分析单个脚本的权限需求"""
        if not os.path.exists(script_path):
            return {
                'error': f'脚本文件不存在: {script_path}',
                'permissions': []
            }
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'error': f'读取脚本文件失败: {str(e)}',
                'permissions': []
            }
        
        permissions = []
        script_name = os.path.basename(script_path)
        
        # 分析每种权限类型
        for permission_type, config in self.permission_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    # 获取匹配行的上下文
                    lines = content.split('\n')
                    match_start = content[:match.start()].count('\n')
                    
                    # 获取前后2行作为上下文
                    context_start = max(0, match_start - 2)
                    context_end = min(len(lines), match_start + 3)
                    context_lines = lines[context_start:context_end]
                    
                    permissions.append({
                        'type': permission_type,
                        'description': config['description'],
                        'risk_level': config['risk_level'],
                        'matched_command': match.group(0),
                        'line_number': match_start + 1,
                        'context': '\n'.join(context_lines),
                        'script': script_name
                    })
        
        return {
            'script': script_name,
            'script_path': script_path,
            'permissions': permissions
        }
    
    def analyze_ansible_playbook_permissions(self, ansible_dir: str = "/home/denerate/ansible-autofix") -> Dict:
        """分析整个Ansible playbook的权限需求"""
        
        # 检查ansible目录
        if not os.path.exists(ansible_dir):
            return {
                'error': f'Ansible目录不存在: {ansible_dir}',
                'summary': {
                    'total_permissions': 0,
                    'high_risk': 0,
                    'medium_risk': 0,
                    'low_risk': 0
                },
                'scripts': []
            }
        
        # 查找所有脚本文件
        script_files = []
        files_dir = os.path.join(ansible_dir, 'roles/autofix/files')
        
        if os.path.exists(files_dir):
            for file in os.listdir(files_dir):
                if file.endswith('.sh'):
                    script_files.append(os.path.join(files_dir, file))
        
        if not script_files:
            return {
                'error': '未找到任何脚本文件',
                'summary': {
                    'total_permissions': 0,
                    'high_risk': 0,
                    'medium_risk': 0,
                    'low_risk': 0
                },
                'scripts': []
            }
        
        # 分析所有脚本
        all_scripts_analysis = []
        total_permissions = 0
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for script_path in script_files:
            analysis = self.analyze_script_permissions(script_path)
            all_scripts_analysis.append(analysis)
            
            if 'permissions' in analysis:
                total_permissions += len(analysis['permissions'])
                for perm in analysis['permissions']:
                    risk_level = perm.get('risk_level', 'low')
                    risk_counts[risk_level] += 1
        
        # 生成权限摘要
        unique_permissions = self._get_unique_permissions(all_scripts_analysis)
        
        return {
            'ansible_dir': ansible_dir,
            'summary': {
                'total_scripts': len(script_files),
                'total_permissions': total_permissions,
                'unique_permission_types': len(unique_permissions),
                'high_risk': risk_counts['high'],
                'medium_risk': risk_counts['medium'],
                'low_risk': risk_counts['low']
            },
            'unique_permissions': unique_permissions,
            'scripts': all_scripts_analysis,
            'recommendation': self._generate_recommendation(risk_counts)
        }
    
    def _get_unique_permissions(self, scripts_analysis: List[Dict]) -> List[Dict]:
        """获取去重后的权限类型"""
        unique_perms = {}
        
        for script_analysis in scripts_analysis:
            if 'permissions' in script_analysis:
                for perm in script_analysis['permissions']:
                    perm_type = perm['type']
                    if perm_type not in unique_perms:
                        unique_perms[perm_type] = {
                            'type': perm_type,
                            'description': perm['description'],
                            'risk_level': perm['risk_level'],
                            'affected_scripts': [],
                            'example_commands': []
                        }
                    
                    script_name = perm.get('script', '未知')
                    if script_name not in unique_perms[perm_type]['affected_scripts']:
                        unique_perms[perm_type]['affected_scripts'].append(script_name)
                    
                    cmd = perm.get('matched_command', '')
                    if cmd and cmd not in unique_perms[perm_type]['example_commands']:
                        unique_perms[perm_type]['example_commands'].append(cmd)
        
        return list(unique_perms.values())
    
    def _generate_recommendation(self, risk_counts: Dict) -> str:
        """生成权限风险建议"""
        total_risks = sum(risk_counts.values())
        
        if total_risks == 0:
            return "该修复脚本未检测到特殊权限需求，可以安全执行。"
        
        recommendations = []
        
        if risk_counts['high'] > 0:
            recommendations.append(f"⚠️ 发现 {risk_counts['high']} 个高风险操作，包括系统文件修改、内存管理等")
        
        if risk_counts['medium'] > 0:
            recommendations.append(f"⚡ 发现 {risk_counts['medium']} 个中风险操作，包括进程控制、服务管理等")
        
        if risk_counts['low'] > 0:
            recommendations.append(f"ℹ️ 发现 {risk_counts['low']} 个低风险操作，主要为网络访问等")
        
        recommendations.append("🔒 建议在了解修复内容后谨慎执行，确保系统安全。")
        
        return '\n'.join(recommendations)

def main():
    """命令行测试入口"""
    analyzer = PermissionAnalyzer()
    
    # 分析ansible权限
    result = analyzer.analyze_ansible_playbook_permissions()
    
    print("Ansible权限分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
