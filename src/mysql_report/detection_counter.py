#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测次数管理器
"""

import os
import json
from datetime import datetime

COUNTER_FILE = "detection_counter.json"

def get_next_detection_number():
    """获取下一次检测的编号"""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                data = json.load(f)
                last_number = data.get('last_detection_number', 0)
                next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1
    
    # 更新计数器文件
    counter_data = {
        'last_detection_number': next_number,
        'last_detection_time': datetime.now().isoformat(),
        'total_detections': next_number
    }
    
    with open(COUNTER_FILE, 'w') as f:
        json.dump(counter_data, f, indent=2)
    
    return next_number

def get_current_detection_number():
    """获取当前检测编号"""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_detection_number', 1)
        except:
            return 1
    return 1

def get_detection_files(detection_number):
    """获取指定检测编号的文件名"""
    return {
        'optimization_report': f"mysql_optimization_report_{detection_number}.json",
        'suggestions': f"mysql_suggestions_{detection_number}.json", 
        'html_report': f"mysql_optimization_report_{detection_number}.html",
        'summary': f"mysql_summary_{detection_number}.txt",
        'advisor': f"variable_advisor_{detection_number}.txt"
    }

if __name__ == "__main__":
    # 测试功能
    print(f"下一次检测编号: {get_next_detection_number()}")
    print(f"当前检测编号: {get_current_detection_number()}")
    files = get_detection_files(get_current_detection_number())
    print("文件名映射:")
    for key, value in files.items():
        print(f"  {key}: {value}")