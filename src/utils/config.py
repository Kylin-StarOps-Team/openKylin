# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import json
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "api_key": "sk-b71092665ded4282aa3ed6b6aab01ae4",
            "prometheus_url": "http://101.42.92.21:9090",
            "max_history_length": 20,
            "default_interval": 1,
            "default_count": 3,
            "default_time_range": "5m",
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "font_family": "Consolas",
                "font_size": 10
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    default_config.update(user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    @property
    def api_key(self):
        return self.get("api_key")
    
    @property
    def prometheus_url(self):
        return self.get("prometheus_url")
    
    @property
    def max_history_length(self):
        return self.get("max_history_length")
    
    @property
    def ui_config(self):
        return self.get("ui", {}) 