# -*- coding: utf-8 -*-
"""
监控工具函数模块
"""

import psutil
import time
from datetime import datetime

def query_sys_io(interval=1, count=3):
    """
    获取系统IO状态
    :param interval: 采样间隔(秒)
    :param count: 采样次数
    :return: IO状态字典列表
    """
    results = []
    
    for i in range(count):
        # 获取磁盘IO统计
        io = psutil.disk_io_counters(perdisk=False)
        
        # 获取分区使用情况
        partitions = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except Exception as e:
                print(f"跳过分区 {part.mountpoint}: {str(e)}")
        
        # 构建结果
        results.append({
            "timestamp": datetime.now().isoformat(),
            "read_count": io.read_count,
            "write_count": io.write_count,
            "read_bytes": io.read_bytes,
            "write_bytes": io.write_bytes,
            "partitions": partitions
        })
        
        if i < count - 1:  # 最后一次不等待
            time.sleep(interval)
    
    return results 