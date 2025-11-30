# -*- coding: utf-8 -*-
"""
MCP协议实现模块
"""

import json
import requests
import subprocess
import os
import shutil
from datetime import datetime
from .monitor_utils import query_sys_io

class WindowsIOMonitorProtocol:
    @staticmethod
    def execute(params=None):
        """
        Windows版IO监控协议
        :param params: 字典参数 (支持interval/count)
        """
        # 设置默认参数
        interval = 1
        count = 3
        if params:
            interval = params.get("interval", interval)
            count = params.get("count", count)
        
        # 执行监控
        data = query_sys_io(interval=int(interval), count=int(count))
        
        # 简化输出格式
        summary = {
            "total_read": sum(item["read_bytes"] for item in data),
            "total_write": sum(item["write_bytes"] for item in data),
            "busiest_partition": max(
                (p for item in data for p in item["partitions"]),
                key=lambda x: x["percent"],
                default={"device": "N/A", "percent": 0}
            )
        }
        
        return {
            "status": "success",
            "summary": summary,
            "raw_data": data
        }

class PrometheusMonitorProtocol:
    @staticmethod
    def execute(params=None):
        """
        Prometheus监控协议
        :param params: 字典参数 (支持query_type, time_range等)
        """
        prometheus_url = "http://101.42.92.21:9090"
        
        # 设置默认参数
        query_type = "cpu"
        time_range = "5m"
        
        if params:
            query_type = params.get("query_type", query_type)
            time_range = params.get("time_range", time_range)
        
        # 预定义的PromQL查询语句
        queries = {
            "cpu": f"100 - (avg by(instance)(rate(node_cpu_seconds_total{{mode='idle'}}[{time_range}])) * 100)",
            "memory": f"(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "disk_usage": f"100 - ((node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100)",
            "disk_io": f"rate(node_disk_io_time_seconds_total[{time_range}]) * 100",
            "network": f"rate(node_network_receive_bytes_total[{time_range}])",
            "load": f"node_load1",
            "uptime": f"node_time_seconds - node_boot_time_seconds"
        }
        
        try:
            results = {}
            
            # 如果指定了具体查询类型
            if query_type in queries:
                query = queries[query_type]
                result = PrometheusMonitorProtocol._execute_prometheus_query(prometheus_url, query)
                results[query_type] = result
            elif query_type == "overview":
                # 获取系统概览信息
                for metric_name, query in queries.items():
                    if metric_name in ["cpu", "memory", "load"]:  # 只获取关键指标
                        result = PrometheusMonitorProtocol._execute_prometheus_query(prometheus_url, query)
                        results[metric_name] = result
            else:
                # 自定义查询
                custom_query = params.get("custom_query", queries["cpu"])
                result = PrometheusMonitorProtocol._execute_prometheus_query(prometheus_url, custom_query)
                results["custom"] = result
            
            # 生成摘要
            summary = PrometheusMonitorProtocol._generate_summary(results, query_type)
            
            return {
                "status": "success",
                "query_type": query_type,
                "time_range": time_range,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "raw_data": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Prometheus查询失败: {str(e)}",
                "query_type": query_type
            }
    
    @staticmethod
    def _execute_prometheus_query(prometheus_url, query):
        """执行单个Prometheus查询"""
        try:
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "success":
                return {
                    "query": query,
                    "result_type": data["data"]["resultType"],
                    "result": data["data"]["result"]
                }
            else:
                return {
                    "query": query,
                    "error": data.get("error", "Unknown error")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "query": query,
                "error": f"请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "query": query,
                "error": f"解析失败: {str(e)}"
            }
    
    @staticmethod
    def _generate_summary(results, query_type):
        """生成查询结果摘要"""
        summary = {
            "total_metrics": len(results),
            "successful_queries": 0,
            "failed_queries": 0,
            "key_findings": []
        }
        
        for metric_name, result in results.items():
            if "error" not in result:
                summary["successful_queries"] += 1
                
                # 提取关键数值
                if result.get("result"):
                    for item in result["result"]:
                        if "value" in item and len(item["value"]) >= 2:
                            value = float(item["value"][1])
                            instance = item.get("metric", {}).get("instance", "unknown")
                            
                            if metric_name == "cpu":
                                summary["key_findings"].append(f"CPU使用率: {value:.2f}% (实例: {instance})")
                            elif metric_name == "memory":
                                summary["key_findings"].append(f"内存使用率: {value:.2f}% (实例: {instance})")
                            elif metric_name == "load":
                                summary["key_findings"].append(f"系统负载: {value:.2f} (实例: {instance})")
            else:
                summary["failed_queries"] += 1
        
        return summary 

class NodeExporterProtocol:
    """Node Exporter监控协议 - 采集系统级指标(CPU、内存、磁盘、网络等)"""
    
    @staticmethod
    def execute(params=None):
        """
        Node Exporter监控协议
        :param params: 字典参数 (支持metric_type等)
        """
        log_file_path = "/var/log/node_exporter_metrics.log"
        
        # 设置默认参数
        metric_type = "overview"
        if params:
            metric_type = params.get("metric_type", metric_type)
        
        try:
            # 从日志文件读取Node Exporter数据
            metrics_data = NodeExporterProtocol._read_node_metrics_from_log(log_file_path)
            
            # 根据请求类型过滤和处理数据
            filtered_data = NodeExporterProtocol._filter_metrics(metrics_data, metric_type)
            
            # 生成摘要和异常分析
            summary = NodeExporterProtocol._generate_summary(filtered_data, metric_type)
            anomaly_analysis = NodeExporterProtocol._analyze_anomalies(filtered_data)
            
            return {
                "status": "success",
                "metric_type": metric_type,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "anomaly_analysis": anomaly_analysis,
                "raw_data": filtered_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Node Exporter数据读取失败: {str(e)}",
                "metric_type": metric_type
            }
    
    @staticmethod
    def _read_node_metrics_from_log(log_file_path):
        """从日志文件读取Node Exporter数据"""
        import os
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
        
        metrics = {}
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析日志文件内容，根据文档示例格式解析
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('=') or line.startswith('Timestamp'):
                    continue
                
                try:
                    # 解析格式: metric_name{labels} value
                    if '{' in line:
                        metric_part, value_part = line.rsplit(' ', 1)
                        metric_name = metric_part.split('{')[0]
                        labels_part = metric_part.split('{')[1].rstrip('}')
                        
                        # 解析标签
                        labels = {}
                        if labels_part:
                            for label_pair in labels_part.split(','):
                                if '=' in label_pair:
                                    key, value = label_pair.split('=', 1)
                                    labels[key.strip()] = value.strip('"')
                    else:
                        parts = line.split()
                        if len(parts) >= 2:
                            metric_name = parts[0]
                            value_part = parts[1]
                            labels = {}
                        else:
                            continue
                    
                    # 尝试转换为数字
                    try:
                        value = float(value_part)
                    except ValueError:
                        continue
                    
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    
                    metrics[metric_name].append({
                        "labels": labels,
                        "value": value
                    })
                    
                except Exception:
                    continue
        
        except Exception as e:
            raise Exception(f"读取日志文件失败: {str(e)}")
        
        return metrics
    
    @staticmethod
    def _filter_metrics(metrics_data, metric_type):
        """根据指标类型过滤数据"""
        if metric_type == "cpu":
            return {k: v for k, v in metrics_data.items() if 'cpu' in k.lower()}
        elif metric_type == "memory":
            return {k: v for k, v in metrics_data.items() if 'memory' in k.lower() or 'mem' in k.lower()}
        elif metric_type == "disk":
            return {k: v for k, v in metrics_data.items() if 'disk' in k.lower() or 'filesystem' in k.lower()}
        elif metric_type == "network":
            return {k: v for k, v in metrics_data.items() if 'network' in k.lower()}
        elif metric_type == "system":
            return {k: v for k, v in metrics_data.items() if any(keyword in k.lower() for keyword in ['load', 'boot', 'uptime'])}
        else:  # overview
            key_metrics = ['node_cpu_seconds_total', 'node_memory_MemTotal_bytes', 'node_memory_MemAvailable_bytes', 
                          'node_filesystem_size_bytes', 'node_filesystem_avail_bytes', 'node_load1', 'node_load5', 'node_load15',
                          'node_network_receive_bytes_total', 'node_network_transmit_bytes_total']
            return {k: v for k, v in metrics_data.items() if k in key_metrics}
    
    @staticmethod
    def _generate_summary(filtered_data, metric_type):
        """生成指标摘要"""
        summary = {"metric_type": metric_type, "key_findings": []}
        
        if metric_type == "cpu" or metric_type == "overview":
            # CPU使用率计算
            cpu_metrics = filtered_data.get('node_cpu_seconds_total', [])
            if cpu_metrics:
                idle_total = sum(m['value'] for m in cpu_metrics if m['labels'].get('mode') == 'idle')
                total_cpu_time = sum(m['value'] for m in cpu_metrics)
                if total_cpu_time > 0:
                    cpu_usage = (1 - idle_total / total_cpu_time) * 100
                    summary["key_findings"].append(f"CPU使用率: {cpu_usage:.2f}%")
        
        if metric_type == "memory" or metric_type == "overview":
            # 内存使用率计算
            mem_total = filtered_data.get('node_memory_MemTotal_bytes', [])
            mem_available = filtered_data.get('node_memory_MemAvailable_bytes', [])
            if mem_total and mem_available:
                total = mem_total[0]['value']
                available = mem_available[0]['value']
                used_percent = (1 - available / total) * 100
                summary["key_findings"].append(f"内存使用率: {used_percent:.2f}%")
        
        if metric_type == "system" or metric_type == "overview":
            # 系统负载
            load1 = filtered_data.get('node_load1', [])
            if load1:
                summary["key_findings"].append(f"系统负载(1分钟): {load1[0]['value']:.2f}")
        
        return summary
    
    @staticmethod
    def _analyze_anomalies(filtered_data):
        """分析异常并给出十级制评分"""
        anomalies = []
        severity_score = 0  # 0-10级异常评分
        
        # CPU异常检测
        cpu_metrics = filtered_data.get('node_cpu_seconds_total', [])
        if cpu_metrics:
            idle_total = sum(m['value'] for m in cpu_metrics if m['labels'].get('mode') == 'idle')
            total_cpu_time = sum(m['value'] for m in cpu_metrics)
            if total_cpu_time > 0:
                cpu_usage = (1 - idle_total / total_cpu_time) * 100
                if cpu_usage > 90:
                    anomalies.append({"type": "CPU高使用率", "value": f"{cpu_usage:.2f}%", "severity": 8})
                    severity_score = max(severity_score, 8)
                elif cpu_usage > 80:
                    anomalies.append({"type": "CPU使用率偏高", "value": f"{cpu_usage:.2f}%", "severity": 6})
                    severity_score = max(severity_score, 6)
        
        # 内存异常检测
        mem_total = filtered_data.get('node_memory_MemTotal_bytes', [])
        mem_available = filtered_data.get('node_memory_MemAvailable_bytes', [])
        if mem_total and mem_available:
            total = mem_total[0]['value']
            available = mem_available[0]['value']
            used_percent = (1 - available / total) * 100
            if used_percent > 95:
                anomalies.append({"type": "内存严重不足", "value": f"{used_percent:.2f}%", "severity": 9})
                severity_score = max(severity_score, 9)
            elif used_percent > 85:
                anomalies.append({"type": "内存使用率偏高", "value": f"{used_percent:.2f}%", "severity": 7})
                severity_score = max(severity_score, 7)
        
        # 系统负载异常检测
        load1 = filtered_data.get('node_load1', [])
        if load1:
            load_value = load1[0]['value']
            if load_value > 10:
                anomalies.append({"type": "系统负载过高", "value": f"{load_value:.2f}", "severity": 8})
                severity_score = max(severity_score, 8)
            elif load_value > 5:
                anomalies.append({"type": "系统负载偏高", "value": f"{load_value:.2f}", "severity": 6})
                severity_score = max(severity_score, 6)
        
        return {
            "severity_score": severity_score,
            "severity_level": NodeExporterProtocol._get_severity_description(severity_score),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    @staticmethod
    def _get_severity_description(score):
        """根据评分获取严重程度描述"""
        if score == 0:
            return "正常"
        elif score <= 3:
            return "轻微异常"
        elif score <= 6:
            return "中等异常"
        elif score <= 8:
            return "严重异常"
        else:
            return "危急异常"

class BlackboxExporterProtocol:
    """Blackbox Exporter监控协议 - 进行黑盒探测(HTTP、TCP、ICMP、DNS等)"""
    
    @staticmethod
    def execute(params=None):
        """
        Blackbox Exporter监控协议
        :param params: 字典参数 (支持target, module, probe_type等)
        """
        log_file_path = "/var/log/blackbox_exporter_metrics.log"
        
        # 设置默认参数
        target = "https://www.baidu.com"
        probe_type = "http"
        
        if params:
            target = params.get("target", target)
            probe_type = params.get("probe_type", probe_type)
        
        try:
            # 从日志文件读取Blackbox Exporter数据
            metrics_data = BlackboxExporterProtocol._read_blackbox_metrics_from_log(log_file_path, target)
            
            # 生成摘要和异常分析
            summary = BlackboxExporterProtocol._generate_summary(metrics_data, target)
            anomaly_analysis = BlackboxExporterProtocol._analyze_anomalies(metrics_data, target)
            
            return {
                "status": "success",
                "target": target,
                "probe_type": probe_type,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "anomaly_analysis": anomaly_analysis,
                "raw_data": metrics_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Blackbox Exporter数据读取失败: {str(e)}",
                "target": target
            }
    
    @staticmethod
    def _read_blackbox_metrics_from_log(log_file_path, target_filter=None):
        """从JSON日志文件读取Blackbox Exporter数据"""
        import os
        import json
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
        
        metrics_by_module = {}
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析JSON格式的日志数据
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    target = data.get("target", "")
                    module = data.get("module", "")
                    metric = data.get("metric", "")
                    value = data.get("value", 0)
                    labels = data.get("labels", {})
                    
                    # 如果指定了目标过滤，只处理匹配的目标
                    if target_filter and target != target_filter:
                        continue
                    
                    if module not in metrics_by_module:
                        metrics_by_module[module] = {
                            "module": module,
                            "target": target,
                            "metrics": {},
                            "status": "success"
                        }
                    
                    metrics_by_module[module]["metrics"][metric] = {
                        "value": value,
                        "labels": labels
                    }
                    
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
        
        except Exception as e:
            raise Exception(f"读取日志文件失败: {str(e)}")
        
        return metrics_by_module
    
    @staticmethod
    def _generate_summary(results, target):
        """生成探测结果摘要"""
        summary = {
            "target": target,
            "total_probes": len(results),
            "successful_probes": 0,
            "failed_probes": 0,
            "key_findings": []
        }
        
        if not results:
            summary["key_findings"].append("未找到探测数据")
            return summary
        
        for module, result in results.items():
            if result.get("status") == "success":
                summary["successful_probes"] += 1
                metrics = result.get("metrics", {})
                
                # 检查探测成功状态
                probe_success = metrics.get("probe_success", {}).get("value", 0)
                probe_duration = metrics.get("probe_duration_seconds", {}).get("value", 0)
                
                if probe_success == 1.0:
                    summary["key_findings"].append(f"{module}: 成功 (耗时: {probe_duration:.3f}s)")
                else:
                    summary["key_findings"].append(f"{module}: 失败")
                
                # HTTP特定指标
                if "http" in module:
                    status_code = metrics.get("probe_http_status_code", {}).get("value")
                    if status_code:
                        summary["key_findings"].append(f"HTTP状态码: {int(status_code)}")
                
                # DNS特定指标
                dns_lookup_time = metrics.get("probe_dns_lookup_time_seconds", {}).get("value")
                if dns_lookup_time:
                    summary["key_findings"].append(f"DNS解析时间: {dns_lookup_time:.3f}s")
            else:
                summary["failed_probes"] += 1
                summary["key_findings"].append(f"{module}: 探测失败")
        
        return summary
    
    @staticmethod
    def _analyze_anomalies(results, target):
        """分析探测异常并给出十级制评分"""
        anomalies = []
        severity_score = 0
        
        for module, result in results.items():
            if result.get("status") == "success":
                metrics = result.get("metrics", {})
                
                # 检查探测失败
                probe_success = metrics.get("probe_success", {}).get("value", 0)
                if probe_success != 1.0:
                    if "http" in module:
                        anomalies.append({
                            "type": f"HTTP探测失败",
                            "module": module,
                            "target": target,
                            "severity": 7
                        })
                        severity_score = max(severity_score, 7)
                    elif "tcp" in module:
                        anomalies.append({
                            "type": f"TCP连接失败", 
                            "module": module,
                            "target": target,
                            "severity": 6
                        })
                        severity_score = max(severity_score, 6)
                    else:
                        anomalies.append({
                            "type": f"{module}探测失败",
                            "module": module, 
                            "target": target,
                            "severity": 5
                        })
                        severity_score = max(severity_score, 5)
                
                # 检查响应时间异常
                probe_duration = metrics.get("probe_duration_seconds", {}).get("value", 0)
                if probe_duration > 10:  # 超过10秒
                    anomalies.append({
                        "type": "响应时间过长",
                        "module": module,
                        "value": f"{probe_duration:.3f}s",
                        "severity": 6
                    })
                    severity_score = max(severity_score, 6)
                elif probe_duration > 5:  # 超过5秒
                    anomalies.append({
                        "type": "响应时间偏长",
                        "module": module,
                        "value": f"{probe_duration:.3f}s", 
                        "severity": 4
                    })
                    severity_score = max(severity_score, 4)
                
                # HTTP状态码检查
                if "http" in module:
                    status_code = metrics.get("probe_http_status_code", {}).get("value")
                    if status_code and status_code >= 500:
                        anomalies.append({
                            "type": "HTTP服务器错误",
                            "module": module,
                            "value": f"状态码: {int(status_code)}",
                            "severity": 8
                        })
                        severity_score = max(severity_score, 8)
                    elif status_code and status_code >= 400:
                        anomalies.append({
                            "type": "HTTP客户端错误", 
                            "module": module,
                            "value": f"状态码: {int(status_code)}",
                            "severity": 6
                        })
                        severity_score = max(severity_score, 6)
                
                # DNS解析时间检查
                dns_lookup_time = metrics.get("probe_dns_lookup_time_seconds", {}).get("value")
                if dns_lookup_time and dns_lookup_time > 2:
                    anomalies.append({
                        "type": "DNS解析缓慢",
                        "module": module,
                        "value": f"{dns_lookup_time:.3f}s",
                        "severity": 4
                    })
                    severity_score = max(severity_score, 4)
            
            else:
                # 探测本身失败
                anomalies.append({
                    "type": "探测执行失败",
                    "module": module,
                    "error": result.get("error", "未知错误"),
                    "severity": 7
                })
                severity_score = max(severity_score, 7)
        
        return {
            "severity_score": severity_score,
            "severity_level": BlackboxExporterProtocol._get_severity_description(severity_score),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    @staticmethod
    def _get_severity_description(score):
        """根据评分获取严重程度描述"""
        if score == 0:
            return "正常"
        elif score <= 3:
            return "轻微异常"
        elif score <= 6:
            return "中等异常"
        elif score <= 8:
            return "严重异常"
        else:
            return "危急异常"

class MysqldExporterProtocol:
    """Mysqld Exporter监控协议 - 采集MySQL数据库指标"""
    
    @staticmethod
    def execute(params=None):
        """
        Mysqld Exporter监控协议
        :param params: 字典参数 (支持metric_type等)
        """
        log_file_path = "/var/log/mysqld_exporter_metrics.log"
        
        # 设置默认参数
        metric_type = "overview"
        if params:
            metric_type = params.get("metric_type", metric_type)
        
        try:
            # 从日志文件读取Mysqld Exporter数据
            metrics_data = MysqldExporterProtocol._read_mysql_metrics_from_log(log_file_path)
            
            # 根据请求类型过滤和处理数据
            filtered_data = MysqldExporterProtocol._filter_metrics(metrics_data, metric_type)
            
            # 生成摘要和异常分析
            summary = MysqldExporterProtocol._generate_summary(filtered_data, metric_type)
            anomaly_analysis = MysqldExporterProtocol._analyze_anomalies(filtered_data)
            
            return {
                "status": "success",
                "metric_type": metric_type,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "anomaly_analysis": anomaly_analysis,
                "raw_data": filtered_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Mysqld Exporter数据读取失败: {str(e)}",
                "metric_type": metric_type
            }
    
    @staticmethod
    def _read_mysql_metrics_from_log(log_file_path):
        """从JSON日志文件读取Mysqld Exporter数据"""
        import os
        import json
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
        
        metrics = {}
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 解析JSON格式的日志数据
            if content:
                try:
                    # 尝试解析为完整的JSON对象
                    data = json.loads(content)
                    
                    # 根据文档示例格式解析
                    if "metrics" in data:
                        for metric_info in data["metrics"]:
                            metric_name = metric_info.get("metric", "")
                            value = metric_info.get("value", 0)
                            labels = metric_info.get("labels", {})
                            
                            if metric_name not in metrics:
                                metrics[metric_name] = []
                            
                            metrics[metric_name].append({
                                "labels": labels,
                                "value": value
                            })
                    
                except json.JSONDecodeError:
                    # 如果不是完整JSON，尝试按行解析
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            if "metrics" in data:
                                for metric_info in data["metrics"]:
                                    metric_name = metric_info.get("metric", "")
                                    value = metric_info.get("value", 0)
                                    labels = metric_info.get("labels", {})
                                    
                                    if metric_name not in metrics:
                                        metrics[metric_name] = []
                                    
                                    metrics[metric_name].append({
                                        "labels": labels,
                                        "value": value
                                    })
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            raise Exception(f"读取日志文件失败: {str(e)}")
        
        return metrics
    
    @staticmethod
    def _filter_metrics(metrics_data, metric_type):
        """根据指标类型过滤数据"""
        if metric_type == "connections":
            return {k: v for k, v in metrics_data.items() if 'connection' in k.lower()}
        elif metric_type == "queries":
            return {k: v for k, v in metrics_data.items() if 'queries' in k.lower() or 'query' in k.lower()}
        elif metric_type == "innodb":
            return {k: v for k, v in metrics_data.items() if 'innodb' in k.lower()}
        elif metric_type == "performance":
            return {k: v for k, v in metrics_data.items() if any(keyword in k.lower() for keyword in ['slow', 'lock', 'thread'])}
        else:  # overview
            key_metrics = [
                'mysql_global_status_connections',
                'mysql_global_status_queries', 
                'mysql_global_status_slow_queries',
                'mysql_global_status_threads_connected',
                'mysql_global_status_threads_running',
                'mysql_global_status_innodb_buffer_pool_read_requests',
                'mysql_global_status_innodb_buffer_pool_reads',
                'mysql_global_status_table_locks_waited',
                'mysql_global_status_uptime'
            ]
            return {k: v for k, v in metrics_data.items() if k in key_metrics}
    
    @staticmethod
    def _generate_summary(filtered_data, metric_type):
        """生成MySQL指标摘要"""
        summary = {"metric_type": metric_type, "key_findings": []}
        
        # 连接数统计
        connections = filtered_data.get('mysql_global_status_connections', [])
        if connections:
            summary["key_findings"].append(f"总连接数: {int(connections[0]['value'])}")
        
        threads_connected = filtered_data.get('mysql_global_status_threads_connected', [])
        if threads_connected:
            summary["key_findings"].append(f"当前连接数: {int(threads_connected[0]['value'])}")
        
        threads_running = filtered_data.get('mysql_global_status_threads_running', [])
        if threads_running:
            summary["key_findings"].append(f"活跃线程数: {int(threads_running[0]['value'])}")
        
        # 查询统计
        queries = filtered_data.get('mysql_global_status_queries', [])
        if queries:
            summary["key_findings"].append(f"总查询数: {int(queries[0]['value'])}")
        
        slow_queries = filtered_data.get('mysql_global_status_slow_queries', [])
        if slow_queries:
            summary["key_findings"].append(f"慢查询数: {int(slow_queries[0]['value'])}")
        
        # InnoDB缓存命中率
        buffer_pool_reads = filtered_data.get('mysql_global_status_innodb_buffer_pool_reads', [])
        buffer_pool_read_requests = filtered_data.get('mysql_global_status_innodb_buffer_pool_read_requests', [])
        if buffer_pool_reads and buffer_pool_read_requests:
            physical_reads = buffer_pool_reads[0]['value']
            logical_reads = buffer_pool_read_requests[0]['value']
            if logical_reads > 0:
                hit_rate = (1 - physical_reads / logical_reads) * 100
                summary["key_findings"].append(f"InnoDB缓存命中率: {hit_rate:.2f}%")
        
        # 运行时间
        uptime = filtered_data.get('mysql_global_status_uptime', [])
        if uptime:
            uptime_hours = uptime[0]['value'] / 3600
            summary["key_findings"].append(f"运行时间: {uptime_hours:.1f}小时")
        
        return summary
    
    @staticmethod
    def _analyze_anomalies(filtered_data):
        """分析MySQL异常并给出十级制评分"""
        anomalies = []
        severity_score = 0
        
        # 检查活跃线程数异常
        threads_running = filtered_data.get('mysql_global_status_threads_running', [])
        if threads_running:
            running_threads = threads_running[0]['value']
            if running_threads > 50:
                anomalies.append({
                    "type": "活跃线程数过多",
                    "value": f"{int(running_threads)}",
                    "severity": 7
                })
                severity_score = max(severity_score, 7)
            elif running_threads > 20:
                anomalies.append({
                    "type": "活跃线程数偏高", 
                    "value": f"{int(running_threads)}",
                    "severity": 5
                })
                severity_score = max(severity_score, 5)
        
        # 检查连接数异常
        threads_connected = filtered_data.get('mysql_global_status_threads_connected', [])
        if threads_connected:
            connected_threads = threads_connected[0]['value']
            if connected_threads > 100:
                anomalies.append({
                    "type": "连接数过多",
                    "value": f"{int(connected_threads)}",
                    "severity": 6
                })
                severity_score = max(severity_score, 6)
        
        # 检查慢查询异常
        slow_queries = filtered_data.get('mysql_global_status_slow_queries', [])
        queries = filtered_data.get('mysql_global_status_queries', [])
        if slow_queries and queries:
            slow_count = slow_queries[0]['value']
            total_count = queries[0]['value']
            if total_count > 0:
                slow_ratio = (slow_count / total_count) * 100
                if slow_ratio > 5:  # 慢查询比例超过5%
                    anomalies.append({
                        "type": "慢查询比例过高",
                        "value": f"{slow_ratio:.2f}%",
                        "severity": 8
                    })
                    severity_score = max(severity_score, 8)
                elif slow_ratio > 1:  # 慢查询比例超过1%
                    anomalies.append({
                        "type": "慢查询比例偏高",
                        "value": f"{slow_ratio:.2f}%", 
                        "severity": 6
                    })
                    severity_score = max(severity_score, 6)
        
        # 检查InnoDB缓存命中率异常
        buffer_pool_reads = filtered_data.get('mysql_global_status_innodb_buffer_pool_reads', [])
        buffer_pool_read_requests = filtered_data.get('mysql_global_status_innodb_buffer_pool_read_requests', [])
        if buffer_pool_reads and buffer_pool_read_requests:
            physical_reads = buffer_pool_reads[0]['value']
            logical_reads = buffer_pool_read_requests[0]['value']
            if logical_reads > 0:
                hit_rate = (1 - physical_reads / logical_reads) * 100
                if hit_rate < 90:  # 命中率低于90%
                    anomalies.append({
                        "type": "InnoDB缓存命中率过低",
                        "value": f"{hit_rate:.2f}%",
                        "severity": 7
                    })
                    severity_score = max(severity_score, 7)
                elif hit_rate < 95:  # 命中率低于95%
                    anomalies.append({
                        "type": "InnoDB缓存命中率偏低",
                        "value": f"{hit_rate:.2f}%",
                        "severity": 5
                    })
                    severity_score = max(severity_score, 5)
        
        # 检查表锁等待
        table_locks_waited = filtered_data.get('mysql_global_status_table_locks_waited', [])
        if table_locks_waited:
            locks_waited = table_locks_waited[0]['value']
            if locks_waited > 100:
                anomalies.append({
                    "type": "表锁等待过多",
                    "value": f"{int(locks_waited)}",
                    "severity": 6
                })
                severity_score = max(severity_score, 6)
        
        return {
            "severity_score": severity_score,
            "severity_level": MysqldExporterProtocol._get_severity_description(severity_score),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    @staticmethod
    def _get_severity_description(score):
        """根据评分获取严重程度描述"""
        if score == 0:
            return "正常"
        elif score <= 3:
            return "轻微异常"
        elif score <= 6:
            return "中等异常"
        elif score <= 8:
            return "严重异常"
        else:
            return "危急异常"

class LokiPromtailProtocol:
    """Loki + Promtail日志监控协议 - 日志收集和查询分析"""
    
    @staticmethod
    def execute(params=None):
        """
        Loki + Promtail日志监控协议
        :param params: 字典参数 (支持query_type, time_range, log_level等)
        """
        log_file_path = "/var/log/loki_monitor_log.json"
        
        # 设置默认参数
        query_type = "recent"
        time_range = "1h"
        log_level = "all"
        limit = 100
        
        if params:
            query_type = params.get("query_type", query_type)
            time_range = params.get("time_range", time_range)
            log_level = params.get("log_level", log_level)
            limit = params.get("limit", limit)
        
        try:
            # 从日志文件读取Loki数据
            logs_data = LokiPromtailProtocol._read_loki_logs_from_file(log_file_path, query_type, limit)
            
            # 分析日志内容
            log_analysis = LokiPromtailProtocol._analyze_logs(logs_data)
            
            # 生成摘要和异常分析
            summary = LokiPromtailProtocol._generate_summary(logs_data, log_analysis, query_type)
            anomaly_analysis = LokiPromtailProtocol._analyze_anomalies(logs_data, log_analysis)
            
            return {
                "status": "success",
                "query_type": query_type,
                "time_range": time_range,
                "log_level": log_level,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "anomaly_analysis": anomaly_analysis,
                "log_analysis": log_analysis,
                "raw_data": logs_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Loki日志数据读取失败: {str(e)}",
                "query_type": query_type
            }
    
    @staticmethod
    def _read_loki_logs_from_file(log_file_path, query_type, limit):
        """从JSON日志文件读取Loki数据"""
        import os
        import json
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
        
        logs = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析JSON格式的日志数据，每行一个JSON对象
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    timestamp = data.get("timestamp", "")
                    log_content = data.get("log", "")
                    
                    # 根据查询类型过滤日志
                    if LokiPromtailProtocol._filter_log_by_type(log_content, query_type):
                        logs.append({
                            "timestamp": timestamp,
                            "log": log_content,
                            "stream": {}
                        })
                    
                    # 限制返回数量
                    if len(logs) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
        
        except Exception as e:
            raise Exception(f"读取日志文件失败: {str(e)}")
        
        return {"logs": logs, "total_count": len(logs)}
    
    @staticmethod
    def _filter_log_by_type(log_content, query_type):
        """根据查询类型过滤日志内容"""
        log_lower = log_content.lower()
        
        if query_type == "errors":
            return any(keyword in log_lower for keyword in ["error", "failed", "exception", "critical"])
        elif query_type == "warnings":
            return any(keyword in log_lower for keyword in ["warning", "warn"])
        elif query_type == "system":
            return any(keyword in log_lower for keyword in ["system", "kernel", "systemd"])
        elif query_type == "network":
            return any(keyword in log_lower for keyword in ["network", "connection", "tcp", "udp", "dns"])
        else:  # recent - 返回所有日志
            return True
    
    @staticmethod
    def _analyze_logs(logs_data):
        """分析日志内容"""
        if "error" in logs_data:
            return {"error": logs_data["error"]}
        
        logs = logs_data.get("logs", [])
        analysis = {
            "total_logs": len(logs),
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "critical_count": 0,
            "error_patterns": {},
            "warning_patterns": {},
            "time_distribution": {},
            "service_distribution": {}
        }
        
        for log_entry in logs:
            log_line = log_entry["log"].lower()
            timestamp = log_entry["timestamp"]
            hour = timestamp.split("T")[1].split(":")[0]
            
            # 统计时间分布
            if hour not in analysis["time_distribution"]:
                analysis["time_distribution"][hour] = 0
            analysis["time_distribution"][hour] += 1
            
            # 分类日志级别
            if any(keyword in log_line for keyword in ["critical", "fatal"]):
                analysis["critical_count"] += 1
            elif any(keyword in log_line for keyword in ["error", "failed", "exception"]):
                analysis["error_count"] += 1
                # 提取错误模式
                for keyword in ["error", "failed", "exception"]:
                    if keyword in log_line:
                        if keyword not in analysis["error_patterns"]:
                            analysis["error_patterns"][keyword] = 0
                        analysis["error_patterns"][keyword] += 1
            elif any(keyword in log_line for keyword in ["warning", "warn"]):
                analysis["warning_count"] += 1
                # 提取警告模式
                for keyword in ["warning", "warn"]:
                    if keyword in log_line:
                        if keyword not in analysis["warning_patterns"]:
                            analysis["warning_patterns"][keyword] = 0
                        analysis["warning_patterns"][keyword] += 1
            else:
                analysis["info_count"] += 1
            
            # 分析服务分布
            if "systemd" in log_line:
                service = "systemd"
            elif "kernel" in log_line:
                service = "kernel"
            elif "mysql" in log_line:
                service = "mysql"
            elif "prometheus" in log_line:
                service = "prometheus"
            else:
                service = "other"
            
            if service not in analysis["service_distribution"]:
                analysis["service_distribution"][service] = 0
            analysis["service_distribution"][service] += 1
        
        return analysis
    
    @staticmethod
    def _generate_summary(logs_data, log_analysis, query_type):
        """生成日志分析摘要"""
        if "error" in logs_data:
            return {"error": logs_data["error"]}
        
        summary = {
            "query_type": query_type,
            "key_findings": []
        }
        
        total_logs = log_analysis["total_logs"]
        if total_logs > 0:
            summary["key_findings"].append(f"总日志条数: {total_logs}")
            
            # 日志级别统计
            if log_analysis["critical_count"] > 0:
                summary["key_findings"].append(f"严重错误: {log_analysis['critical_count']}")
            if log_analysis["error_count"] > 0:
                summary["key_findings"].append(f"错误日志: {log_analysis['error_count']}")
            if log_analysis["warning_count"] > 0:
                summary["key_findings"].append(f"警告日志: {log_analysis['warning_count']}")
            
            # 错误率
            error_rate = (log_analysis["error_count"] + log_analysis["critical_count"]) / total_logs * 100
            if error_rate > 0:
                summary["key_findings"].append(f"错误率: {error_rate:.2f}%")
            
            # 服务分布
            service_dist = log_analysis["service_distribution"]
            if service_dist:
                top_service = max(service_dist.items(), key=lambda x: x[1])
                summary["key_findings"].append(f"主要服务: {top_service[0]} ({top_service[1]}条)")
        else:
            summary["key_findings"].append("未找到日志数据")
        
        return summary
    
    @staticmethod
    def _analyze_anomalies(logs_data, log_analysis):
        """分析日志异常并给出十级制评分"""
        if "error" in logs_data:
            return {
                "severity_score": 5,
                "severity_level": "中等异常",
                "anomalies": [{"type": "日志查询失败", "error": logs_data["error"], "severity": 5}],
                "total_anomalies": 1
            }
        
        anomalies = []
        severity_score = 0
        
        total_logs = log_analysis["total_logs"]
        
        if total_logs == 0:
            return {
                "severity_score": 3,
                "severity_level": "轻微异常",
                "anomalies": [{"type": "无日志数据", "severity": 3}],
                "total_anomalies": 1
            }
        
        # 检查严重错误
        critical_count = log_analysis["critical_count"]
        if critical_count > 0:
            anomalies.append({
                "type": "发现严重错误",
                "count": critical_count,
                "severity": 9
            })
            severity_score = max(severity_score, 9)
        
        # 检查错误率
        error_count = log_analysis["error_count"]
        error_rate = (error_count + critical_count) / total_logs * 100
        
        if error_rate > 20:  # 错误率超过20%
            anomalies.append({
                "type": "错误率过高",
                "value": f"{error_rate:.2f}%",
                "severity": 8
            })
            severity_score = max(severity_score, 8)
        elif error_rate > 10:  # 错误率超过10%
            anomalies.append({
                "type": "错误率偏高",
                "value": f"{error_rate:.2f}%",
                "severity": 6
            })
            severity_score = max(severity_score, 6)
        elif error_rate > 5:  # 错误率超过5%
            anomalies.append({
                "type": "错误率异常",
                "value": f"{error_rate:.2f}%",
                "severity": 4
            })
            severity_score = max(severity_score, 4)
        
        # 检查警告数量
        warning_count = log_analysis["warning_count"]
        warning_rate = warning_count / total_logs * 100
        
        if warning_rate > 30:  # 警告率超过30%
            anomalies.append({
                "type": "警告过多",
                "value": f"{warning_rate:.2f}%",
                "severity": 5
            })
            severity_score = max(severity_score, 5)
        
        # 检查特定错误模式
        error_patterns = log_analysis["error_patterns"]
        for pattern, count in error_patterns.items():
            if count > 10:  # 同类错误超过10次
                anomalies.append({
                    "type": f"频繁{pattern}错误",
                    "count": count,
                    "severity": 6
                })
                severity_score = max(severity_score, 6)
        
        return {
            "severity_score": severity_score,
            "severity_level": LokiPromtailProtocol._get_severity_description(severity_score),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    @staticmethod
    def _get_severity_description(score):
        """根据评分获取严重程度描述"""
        if score == 0:
            return "正常"
        elif score <= 3:
            return "轻微异常"
        elif score <= 6:
            return "中等异常"
        elif score <= 8:
            return "严重异常"
        else:
            return "危急异常"

class TrivySecurityProtocol:
    """Trivy安全扫描协议 - 支持多种安全漏洞扫描"""
    
    def __init__(self):
        self.name = "TrivySecurityProtocol"
        self.scan_types = {
            "scan_image": "容器镜像扫描",
            "scan_filesystem": "本地文件系统/项目扫描", 
            "scan_repository": "Git仓库扫描",
            "scan_kubernetes": "Kubernetes集群扫描",
            "scan_config": "配置文件(IaC)扫描",
            "scan_sbom": "软件物料清单(SBOM)扫描",
            "scan_secrets": "敏感信息泄露检测"
        }
        
    @staticmethod
    def execute(params=None):
        """
        执行Trivy安全扫描
        :param params: 扫描参数
            - tool: 扫描类型 (scan_image, scan_filesystem, scan_repository, 等)
            - target: 扫描目标 (镜像名、路径、仓库URL等)
            - format: 输出格式 (json, table)
            - scanners: 扫描器类型 (vuln, secret, config)
            - severity: 严重程度过滤 (CRITICAL, HIGH, MEDIUM, LOW)
        """
        import subprocess
        import json
        import tempfile
        import os
        from datetime import datetime
        
        # 设置默认参数
        tool = params.get("tool", "scan_filesystem") if params else "scan_filesystem"
        target = params.get("target", ".") if params else "."
        output_format = params.get("format", "json") if params else "json"
        scanners = params.get("scanners", "vuln,secret,config") if params else "vuln,secret,config"
        severity = params.get("severity", "") if params else ""
        
        try:
            # 检查Trivy是否已安装
            try:
                subprocess.run(["trivy", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return {
                    "status": "error",
                    "message": "Trivy未安装或不在PATH中，请先安装Trivy",
                    "tool": tool,
                    "target": target,
                    "install_guide": "请访问 https://aquasecurity.github.io/trivy/ 获取安装指南"
                }
            
            # 构建Trivy命令
            cmd = TrivySecurityProtocol._build_trivy_command(tool, target, output_format, scanners, severity)
            
            if not cmd:
                return {
                    "status": "error", 
                    "message": f"不支持的扫描类型: {tool}",
                    "supported_tools": list(TrivySecurityProtocol().scan_types.keys())
                }
            
            # 创建临时文件保存输出
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 添加输出文件参数
            if output_format == "json":
                cmd.extend(["-f", "json", "-o", temp_path])
            
            print(f"🔍 执行Trivy扫描: {' '.join(cmd)}")
            
            # 执行Trivy命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3000  # 5分钟超时
            )
            
            print(f"📊 命令返回码: {result.returncode}")
            print(f"📁 临时文件路径: {temp_path}")
            
            # 检查命令执行状态
            if result.returncode != 0:
                # Trivy命令执行失败
                error_msg = f"Trivy命令执行失败 (返回码: {result.returncode})"
                if result.stderr:
                    error_msg += f"\n错误信息: {result.stderr}"
                return {
                    "status": "error",
                    "message": error_msg,
                    "tool": tool,
                    "target": target,
                    "command": " ".join(cmd),
                    "return_code": result.returncode,
                    "stderr": result.stderr
                }
            
            # 读取扫描结果
            scan_result = None
            print(f"📁 检查临时文件是否存在: {os.path.exists(temp_path)}")
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"📏 文件大小: {file_size} 字节")
                try:
                    if file_size > 0:
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            print(f"📖 读取内容长度: {len(content)} 字符")
                            if content:
                                scan_result = json.loads(content)
                                print(f"✅ JSON解析成功")
                            else:
                                # 空文件，表示没有发现问题
                                scan_result = {"Results": []}
                                print(f"📝 空文件，设置默认结果")
                    else:
                        # 空文件，表示没有发现问题
                        scan_result = {"Results": []}
                        print(f"📝 空文件，设置默认结果")
                except json.JSONDecodeError as e:
                    # JSON解析失败，尝试读取原始内容
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    print(f"⚠️ JSON解析失败: {e}")
                    print(f"📄 原始内容前500字符: {raw_content[:500]}")
                    scan_result = {"raw_output": raw_content, "parse_error": str(e)}
                except Exception as e:
                    print(f"❌ 读取扫描结果失败: {e}")
                    scan_result = {"error": f"读取结果失败: {str(e)}"}
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                        print(f"🗑️ 临时文件已清理")
                    except Exception as cleanup_error:
                        print(f"⚠️ 清理临时文件失败: {cleanup_error}")
            else:
                # 临时文件不存在，可能是Trivy没有输出结果
                print(f"⚠️ 临时文件不存在: {temp_path}")
                scan_result = {"Results": [], "message": "未生成扫描结果文件"}
            
            # 分析扫描结果
            analysis = TrivySecurityProtocol._analyze_scan_result(scan_result, tool, target)
            
            # 确定最终状态
            final_status = "success"
            if "error" in scan_result or "parse_error" in scan_result:
                final_status = "warning"  # 有警告但不是完全失败
            
            return {
                "status": final_status,
                "tool": tool,
                "target": target,
                "scanners": scanners,
                "timestamp": datetime.now().isoformat(),
                "command": " ".join(cmd),
                "return_code": result.returncode,
                "summary": analysis["summary"],
                "anomaly_analysis": analysis["anomaly_analysis"],
                "recommendations": analysis["recommendations"],
                "compressed_data": analysis.get("compressed_data", {}),  # 使用压缩后的数据而不是原始数据
                "stderr": result.stderr if result.stderr else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Trivy扫描超时（超过5分钟）",
                "tool": tool,
                "target": target
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Trivy扫描执行失败: {str(e)}",
                "tool": tool,
                "target": target
            }
        finally:
            # 清理临时文件
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    @staticmethod
    def _build_trivy_command(tool, target, output_format, scanners, severity):
        """构建Trivy命令"""
        cmd = ["trivy"]
        
        if tool == "scan_image":
            cmd.extend(["image", target])
        elif tool == "scan_filesystem":
            cmd.extend(["fs", target])
            if scanners:
                cmd.extend(["--scanners", scanners])
        elif tool == "scan_repository":
            cmd.extend(["repo", target])
        elif tool == "scan_kubernetes":
            if target == "cluster":
                cmd.extend(["k8s", "cluster"])
            else:
                cmd.extend(["k8s", target])
        elif tool == "scan_config":
            cmd.extend(["config", target])
        elif tool == "scan_sbom":
            cmd.extend(["sbom", target])
        elif tool == "scan_secrets":
            cmd.extend(["fs", "--scanners", "secret", target])
        else:
            return None
        
        # 添加严重程度过滤
        if severity:
            cmd.extend(["--severity", severity])
        
        # 添加通用选项
        cmd.extend(["--quiet"])  # 减少输出噪音
        
        return cmd
    
    @staticmethod
    def _analyze_scan_result(scan_result, tool, target):
        """分析Trivy扫描结果"""
        if not scan_result:
            return {
                "summary": {"total_vulnerabilities": 0, "status": "无扫描结果", "scan_type": TrivySecurityProtocol().scan_types.get(tool, tool), "target": target},
                "anomaly_analysis": {"anomaly_score": 0, "risk_level": "未知"},
                "recommendations": ["扫描未返回结果，请检查目标是否有效"]
            }
        
        # 处理解析错误的情况
        if "parse_error" in scan_result:
            return {
                "summary": {"total_vulnerabilities": 0, "status": "结果解析失败", "scan_type": TrivySecurityProtocol().scan_types.get(tool, tool), "target": target},
                "anomaly_analysis": {"anomaly_score": 1, "risk_level": "低风险"},
                "recommendations": [f"扫描结果JSON解析失败: {scan_result['parse_error']}", "建议检查Trivy版本兼容性"]
            }
        
        # 处理读取错误的情况    
        if "error" in scan_result:
            return {
                "summary": {"total_vulnerabilities": 0, "status": "读取失败", "scan_type": TrivySecurityProtocol().scan_types.get(tool, tool), "target": target},
                "anomaly_analysis": {"anomaly_score": 1, "risk_level": "低风险"}, 
                "recommendations": [f"扫描结果读取失败: {scan_result['error']}", "建议检查文件权限和磁盘空间"]
            }
        
        # 初始化统计
        summary = {
            "total_vulnerabilities": 0,
            "critical": 0,
            "high": 0, 
            "medium": 0,
            "low": 0,
            "unknown": 0,
            "secrets_found": 0,
            "config_issues": 0,
            "scan_type": TrivySecurityProtocol().scan_types.get(tool, tool),
            "target": target
        }
        
        # 用于存储关键漏洞信息的压缩数据（只保留最重要的信息）
        critical_vulnerabilities = []
        high_vulnerabilities = []
        sample_secrets = []
        sample_misconfigs = []
        
        # 处理不同格式的扫描结果
        vulnerabilities = []
        secrets = []
        misconfigurations = []
        
        if isinstance(scan_result, dict):
            # 处理JSON格式结果
            if "Results" in scan_result:
                for result in scan_result["Results"]:
                    # 处理漏洞
                    if "Vulnerabilities" in result:
                        vulnerabilities.extend(result["Vulnerabilities"])
                    
                    # 处理配置问题  
                    if "Misconfigurations" in result:
                        misconfigurations.extend(result["Misconfigurations"])
                        
                    # 处理敏感信息
                    if "Secrets" in result:
                        secrets.extend(result["Secrets"])
            
            # 直接在根级别的漏洞数据
            elif "Vulnerabilities" in scan_result:
                vulnerabilities = scan_result["Vulnerabilities"]
        
        # 统计漏洞严重程度并保留关键信息
        for vuln in vulnerabilities:
            severity = vuln.get("Severity", "UNKNOWN").upper()
            summary["total_vulnerabilities"] += 1
            
            if severity == "CRITICAL":
                summary["critical"] += 1
                # 只保留前5个严重漏洞的关键信息
                if len(critical_vulnerabilities) < 5:
                    critical_vulnerabilities.append({
                        "id": vuln.get("VulnerabilityID", "N/A"),
                        "title": vuln.get("Title", "")[:100],  # 限制标题长度
                        "severity": severity,
                        "package": vuln.get("PkgName", ""),
                        "installed_version": vuln.get("InstalledVersion", ""),
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "description": vuln.get("Description", "")[:200]  # 限制描述长度
                    })
            elif severity == "HIGH":
                summary["high"] += 1
                # 只保留前3个高危漏洞的关键信息
                if len(high_vulnerabilities) < 3:
                    high_vulnerabilities.append({
                        "id": vuln.get("VulnerabilityID", "N/A"),
                        "title": vuln.get("Title", "")[:100],
                        "severity": severity,
                        "package": vuln.get("PkgName", ""),
                        "installed_version": vuln.get("InstalledVersion", ""),
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "description": vuln.get("Description", "")[:200]
                    })
            elif severity == "MEDIUM":
                summary["medium"] += 1
            elif severity == "LOW":
                summary["low"] += 1
            else:
                summary["unknown"] += 1
        
        # 统计其他问题并保留样本
        summary["secrets_found"] = len(secrets)
        summary["config_issues"] = len(misconfigurations)
        
        # 保留前3个secrets样本
        for i, secret in enumerate(secrets[:3]):
            sample_secrets.append({
                "title": secret.get("Title", "")[:50],
                "category": secret.get("Category", ""),
                "severity": secret.get("Severity", ""),
                "match": secret.get("Match", "")[:100] if secret.get("Match") else ""
            })
        
        # 保留前3个错误配置样本
        for i, config in enumerate(misconfigurations[:3]):
            sample_misconfigs.append({
                "id": config.get("ID", ""),
                "title": config.get("Title", "")[:100],
                "severity": config.get("Severity", ""),
                "message": config.get("Message", "")[:150]
            })
        
        # 计算异常评分 (0-10级)
        anomaly_score = TrivySecurityProtocol._calculate_anomaly_score(summary)
        risk_level = TrivySecurityProtocol._get_risk_level(anomaly_score)
        
        # 生成建议
        recommendations = TrivySecurityProtocol._generate_recommendations(summary, tool)
        
        # 构建压缩数据，只包含关键信息
        compressed_data = {
            "scan_summary": {
                "total_vulnerabilities": summary["total_vulnerabilities"],
                "critical": summary["critical"],
                "high": summary["high"],
                "medium": summary["medium"],
                "low": summary["low"],
                "secrets_found": summary["secrets_found"],
                "config_issues": summary["config_issues"],
                "scan_type": summary["scan_type"],
                "target": summary["target"]
            },
            "critical_vulnerabilities": critical_vulnerabilities,
            "high_vulnerabilities": high_vulnerabilities,
            "sample_secrets": sample_secrets,
            "sample_misconfigs": sample_misconfigs,
            "risk_assessment": {
                "anomaly_score": anomaly_score,
                "risk_level": risk_level,
                "total_issues": summary["total_vulnerabilities"] + summary["secrets_found"] + summary["config_issues"]
            }
        }
        
        return {
            "summary": summary,
            "anomaly_analysis": {
                "anomaly_score": anomaly_score,
                "risk_level": risk_level,
                "total_issues": summary["total_vulnerabilities"] + summary["secrets_found"] + summary["config_issues"]
            },
            "recommendations": recommendations,
            "compressed_data": compressed_data
        }
    
    @staticmethod 
    def _calculate_anomaly_score(summary):
        """计算异常评分 (0-10级)"""
        score = 0
        
        # 基于漏洞严重程度计分
        score += summary["critical"] * 2.0  # 每个严重漏洞2分
        score += summary["high"] * 1.5      # 每个高危漏洞1.5分
        score += summary["medium"] * 1.0    # 每个中危漏洞1分
        score += summary["low"] * 0.5       # 每个低危漏洞0.5分
        
        # 基于其他问题计分
        score += summary["secrets_found"] * 1.5    # 每个敏感信息泄露1.5分
        score += summary["config_issues"] * 1.0    # 每个配置问题1分
        
        # 限制在0-10范围内
        return min(10, max(0, int(score)))
    
    @staticmethod
    def _get_risk_level(score):
        """根据评分获取风险等级"""
        if score == 0:
            return "无风险"
        elif score <= 2:
            return "低风险"
        elif score <= 4:
            return "中风险"
        elif score <= 6:
            return "高风险"
        elif score <= 8:
            return "严重风险"
        else:
            return "危急风险"
    
    @staticmethod
    def _generate_recommendations(summary, tool):
        """生成安全建议"""
        recommendations = []
        
        # 基于漏洞数量的建议
        if summary["critical"] > 0:
            recommendations.append(f"🚨 发现{summary['critical']}个严重漏洞，需要立即修复")
        
        if summary["high"] > 0:
            recommendations.append(f"⚠️ 发现{summary['high']}个高危漏洞，建议优先修复")
        
        if summary["medium"] > 0:
            recommendations.append(f"⚡ 发现{summary['medium']}个中危漏洞，建议及时修复")
        
        # 基于扫描类型的建议
        if tool == "scan_image":
            if summary["total_vulnerabilities"] > 0:
                recommendations.append("建议使用更安全的基础镜像或更新到最新版本")
            recommendations.append("建议定期扫描和更新容器镜像")
            
        elif tool == "scan_filesystem":
            if summary["total_vulnerabilities"] > 0:
                recommendations.append("建议更新项目依赖到最新的安全版本")
            if summary["secrets_found"] > 0:
                recommendations.append(f"⚠️ 发现{summary['secrets_found']}个敏感信息泄露，请立即清理")
                
        elif tool == "scan_config":
            if summary["config_issues"] > 0:
                recommendations.append(f"发现{summary['config_issues']}个配置问题，建议按照安全最佳实践修改")
                
        # 通用建议
        if summary["total_vulnerabilities"] == 0 and summary["secrets_found"] == 0 and summary["config_issues"] == 0:
            recommendations.append("✅ 扫描未发现安全问题，继续保持良好的安全实践")
        else:
            recommendations.append("建议建立定期安全扫描机制")
            recommendations.append("建议关注安全公告并及时应用补丁")
        
        return recommendations

class AutofixProtocol:
    @staticmethod
    def execute(params=None):
        """
        自动修复服务协议
        通过ansible执行系统自动修复
        :param params: 字典参数 (支持problem_description, confirm_permissions等)
        """
        import subprocess
        import os
        import sys
        
        # 确保权限分析器可用
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.permission_analyzer import PermissionAnalyzer
        
        if not params:
            params = {}
        
        problem_description = params.get("problem_description", "系统需要修复")
        confirm_permissions = params.get("confirm_permissions", False)
        ansible_playbook_path = "/home/denerate/ansible-autofix/playbook.yml"
        ansible_config_path = "/home/denerate/ansible-autofix/ansible.cfg"
        
        # 如果未确认权限，则先进行权限分析
        if not confirm_permissions:
            print("🔍 正在分析Ansible修复脚本的权限需求...")
            analyzer = PermissionAnalyzer()
            permission_analysis = analyzer.analyze_ansible_playbook_permissions()
            
            return {
                "status": "permission_required",
                "message": "需要用户确认执行权限",
                "problem_description": problem_description,
                "permission_analysis": permission_analysis,
                "next_action": {
                    "protocol": "AutofixProtocol",
                    "params": {
                        "problem_description": problem_description,
                        "confirm_permissions": True
                    }
                }
            }
        
        try:
            # 检查ansible配置文件是否存在
            if not os.path.exists(ansible_playbook_path):
                return {
                    "status": "error",
                    "error": f"Ansible playbook未找到: {ansible_playbook_path}",
                    "problem_description": problem_description
                }
            
            # 执行ansible-playbook命令
            cmd = [
                "ansible-playbook", 
                ansible_playbook_path,
                "-i", "/home/denerate/ansible-autofix/inventory",
                "-v"  # 增加详细输出
            ]
            
            # 输出要执行的命令
            cmd_str = " ".join(cmd)
            print(f"🔧 正在执行Ansible自动修复命令:")
            print(f"📋 命令: {cmd_str}")
            print(f"📂 工作目录: /home/denerate/ansible-autofix")
            print(f"📝 问题描述: {problem_description}")
            print("⏳ 开始执行修复任务...")
            
            # 设置环境变量
            env = os.environ.copy()
            env['ANSIBLE_CONFIG'] = ansible_config_path
            
            print("🚀 Ansible playbook 正在运行中...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env=env,
                cwd="/home/denerate/ansible-autofix"
            )
            
            print(f"📊 Ansible执行完成，返回码: {result.returncode}")
            if result.returncode == 0:
                print("✅ Ansible playbook执行成功")
            else:
                print("❌ Ansible playbook执行失败")
            
            # 分析执行结果
            success = result.returncode == 0
            
            # 解析ansible输出
            output_lines = result.stdout.split('\n')
            error_lines = result.stderr.split('\n')

            # print(f"debug - output_lines: {output_lines}")
            # print(f"debug - error_lines: {error_lines}")
            
            # 统计任务执行情况
            task_summary = {
                "changed": 0,
                "ok": 0,  
                "failed": 0,
                "skipped": 0
            }
            
            for line in output_lines:
                # print(f"debug - line: {line}")
                if "changed=" in line and ("ok=" in line or "failed=" in line):
                    # 解析类似: "localhost: ok=8 changed=4 unreachable=0 failed=0"
                    parts = line.split()
                    # print(f"debug - parts: {parts}")
                    for part in parts:
                        # print(f"debug - part: {part}")
                        if "=" in part:
                            try:
                                key, value = part.split("=", 1)
                                if key in ["changed", "ok", "failed", "skipped"]:
                                    # 确保value是数字
                                    if value.isdigit():
                                        task_summary[key] = int(value)
                                    else:
                                        task_summary["changed"] += 1
                            except ValueError:
                                print(f"⚠️ 跳过解析失败的部分: {part}")
                # print(f"debug - task_summary: {task_summary}")
            
            # 检查修复服务状态
            services_status = AutofixProtocol._check_autofix_services()
            
            # 输出详细的执行结果
            print(f"\n📋 Ansible执行摘要:")
            print(f"  ✅ 成功任务: {task_summary['ok']}")
            print(f"  🔄 变更任务: {task_summary['changed']}")
            print(f"  ❌ 失败任务: {task_summary['failed']}")
            print(f"  ⏭️ 跳过任务: {task_summary['skipped']}")
            
            if result.stdout:
                print(f"\n📄 Ansible输出:")
                print(result.stdout[-100:])  # 显示最后100字符
            
            if result.stderr:
                print(f"\n⚠️ Ansible错误信息:")
                print(result.stderr[-100:])   # 显示最后100字符
            
            return {
                "status": "success" if success else "error",
                "problem_description": problem_description,
                "execution_time": datetime.now().isoformat(),
                "command_executed": cmd_str,
                "working_directory": "/home/denerate/ansible-autofix",
                "ansible_result": {
                    "return_code": result.returncode,
                    "success": success,
                    "task_summary": task_summary,
                    "stdout": result.stdout[-1500:] if result.stdout else "",  # 最后1500字符
                    "stderr": result.stderr[-800:] if result.stderr else ""    # 最后800字符
                },
                "services_status": services_status,
                "next_actions": AutofixProtocol._get_next_actions(success, problem_description)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error", 
                "error": "Ansible执行超时（超过5分钟）",
                "problem_description": problem_description
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"自动修复执行失败: {str(e)}",
                "problem_description": problem_description
            }
    
    @staticmethod
    def _check_autofix_services():
        """检查自动修复服务的运行状态"""
        import subprocess
        
        services = [
            "disk-autoheal.timer",
            "deadlock-autoheal.timer", 
            "memory_autoheal.timer",
            "cpu_autoheal.timer",
            "network_autoheal.timer",
            "system_autoheal.timer"
        ]
        
        service_status = {}
        print("\n🔍 检查自动修复服务状态:")
        
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                is_active = result.returncode == 0
                status_text = result.stdout.strip()
                
                service_status[service] = {
                    "active": is_active,
                    "status": status_text
                }
                
                # 输出服务状态
                status_icon = "✅" if is_active else "❌"
                print(f"  {status_icon} {service}: {status_text}")
                
            except Exception as e:
                service_status[service] = {
                    "active": False,
                    "status": f"检查失败: {str(e)}"
                }
                print(f"  ❌ {service}: 检查失败 - {str(e)}")
        
        # 统计服务状态
        active_count = sum(1 for s in service_status.values() if s["active"])
        total_count = len(services)
        print(f"\n📊 服务状态摘要: {active_count}/{total_count} 个服务正在运行")
        
        return service_status
    
    @staticmethod  
    def _get_next_actions(success, problem_description):
        """根据修复结果提供下一步建议"""
        if success:
            actions = [
                "监控系统状态变化",
                "检查自动修复服务是否正常运行", 
                "使用相应的监控协议验证问题是否解决"
            ]
            
            # 根据问题描述提供具体建议
            if any(keyword in problem_description.lower() for keyword in ["内存", "memory"]):
                actions.append("建议使用NodeExporterProtocol检查内存使用率")
            elif any(keyword in problem_description.lower() for keyword in ["cpu", "负载"]):
                actions.append("建议使用NodeExporterProtocol检查CPU使用率")
            elif any(keyword in problem_description.lower() for keyword in ["磁盘", "disk", "存储"]):
                actions.append("建议使用NodeExporterProtocol检查磁盘使用率")
            elif any(keyword in problem_description.lower() for keyword in ["网络", "network", "连接"]):
                actions.append("建议使用BlackboxExporterProtocol检查网络连通性")
            else:
                actions.append("建议使用NodeExporterProtocol检查系统整体状态")
                
        else:
            actions = [
                "检查ansible执行日志查看详细错误信息",
                "确认目标服务器的连接状态",
                "手动检查系统资源和服务状态",
                "考虑联系系统管理员进行人工干预"
            ]
        print("🔑 next_action", actions)
        return actions

class WebScanProtocol:
    """
    Web应用配置优化检测协议
    集成web_config_check功能，提供网站配置分析和安全检测
    """
    
    @staticmethod
    def execute(params=None):
        """
        执行Web配置扫描
        :param params: 字典参数，支持url, mode, output_dir等
        """
        import sys
        import os
        from datetime import datetime
        
        # 注意：现在使用远程API获取检测数据，不再需要本地的collector和analyzer模块
        
        # 设置默认参数
        target_url = "http://localhost:8080"
        scan_mode = "quick"
        output_dir = "reports"
        
        if params:
            target_url = params.get("url", target_url)
            scan_mode = params.get("mode", scan_mode)
            output_dir = params.get("output_dir", output_dir)
        
        # 提取URL如果在文本中
        if params and "text" in params:
            extracted_url = WebScanProtocol._extract_url_from_text(params["text"])
            if extracted_url:
                target_url = extracted_url
        
        try:
            print(f"🌐 开始扫描网站: {target_url}")
            print(f"📋 扫描模式: {scan_mode}")
            
            # 调用远程API获取检测数据
            api_url = "http://101.42.92.21:5000/detect"
            print(f"🔗 调用远程API: {api_url}?url={target_url}")
            
            try:
                # 发送API请求
                response = requests.get(api_url, params={"url": target_url}, timeout=60)
                response.raise_for_status()
                api_data = response.json()
                
                # 检查API响应状态
                if api_data.get('status') != 'success':
                    return {
                        "status": "error",
                        "message": f"远程API检测失败: {api_data.get('message', '未知错误')}",
                        "target_url": target_url,
                        "error_type": "api_error"
                    }
                
                # 从API响应中提取数据
                config_data = api_data.get('config', {})
                analysis_dict = api_data.get('analysis', {})
                
                print(f"✅ 成功获取远程检测数据")
                print(f"🔍 配置数据字段数量: {len(config_data)}")
                print(f"🔍 分析建议数量: {len(analysis_dict.get('suggestions', []))}")
                
            except requests.exceptions.RequestException as e:
                return {
                    "status": "error",
                    "message": f"远程API调用失败: {str(e)}",
                    "target_url": target_url,
                    "error_type": "network_error"
                }
            except (ValueError, KeyError) as e:
                return {
                    "status": "error",
                    "message": f"API响应数据格式错误: {str(e)}",
                    "target_url": target_url,
                    "error_type": "data_format_error"
                }
            
            # 创建本地报告生成器实例
            from .web_report_generator import WebReportGenerator
            report_generator = WebReportGenerator()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 确保analysis_dict有正确的结构
            suggestions = analysis_dict.get('suggestions', [])
            if 'summary' not in analysis_dict:
                analysis_dict['summary'] = {
                    'total': len(suggestions),
                    'critical': len([s for s in suggestions if s.get('severity') == 'critical']),
                    'high': len([s for s in suggestions if s.get('severity') == 'high']),
                    'medium': len([s for s in suggestions if s.get('severity') == 'medium']),
                    'low': len([s for s in suggestions if s.get('severity') == 'low'])
                }
            
            # 生成摘要结果
            summary = WebScanProtocol._generate_scan_summary(analysis_dict, target_url, scan_mode)
            
            # 生成并保存HTML报告（所有模式都生成）
            print("📄 生成HTML报告...")
            report_files = {}
            try:
                # 确保reports目录存在
                reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
                os.makedirs(reports_dir, exist_ok=True)
                
                print(f"🔍 suggestions数量: {len(suggestions)}")
                print(f"🔍 各级别问题统计: critical={analysis_dict['summary']['critical']}, high={analysis_dict['summary']['high']}, medium={analysis_dict['summary']['medium']}, low={analysis_dict['summary']['low']}")
                
                # 生成并保存HTML报告
                html_file = report_generator.generate_and_save_report(
                    summary=analysis_dict['summary'],
                    suggestions=suggestions,
                    target_url=target_url,
                    scan_mode=scan_mode,
                    output_dir=reports_dir
                )
                report_files["html"] = html_file
                print(f"✅ HTML报告已保存: {html_file}")
                
            except Exception as e:
                print(f"⚠️  报告生成失败: {str(e)}")
                import traceback
                traceback.print_exc()
                # 即使报告生成失败，也继续返回分析结果
            
            return {
                "status": "success",
                "scan_mode": scan_mode,
                "target_url": target_url,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "report_files": report_files,
                "raw_analysis": analysis_dict if scan_mode == "full" else {},
                "next_actions": WebScanProtocol._get_recommendations(analysis_dict)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Web配置扫描执行失败: {str(e)}",
                "target_url": target_url,
                "error_type": "execution_error"
            }
    
    @staticmethod
    def _extract_url_from_text(text):
        """从文本中提取URL"""
        import re
        
        # URL正则表达式模式
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?' 
        
        urls = re.findall(url_pattern, text)
        if urls:
            url = urls[0]
            # 确保URL有协议前缀
            if not url.startswith(('http://', 'https://')):
                if url.startswith('www.'):
                    url = 'https://' + url
                else:
                    url = 'https://' + url
            return url
        return None
    
    @staticmethod
    def _generate_scan_summary(analysis_result, target_url, scan_mode):
        """生成扫描摘要"""
        if not analysis_result or 'suggestions' not in analysis_result:
            return {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "security_score": "N/A",
                "performance_score": "N/A",
                "recommendations": ["无法获取分析结果，请检查目标网站是否可访问"]
            }
        
        suggestions = analysis_result.get('suggestions', [])
        
        # 统计问题数量
        severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for suggestion in suggestions:
            severity = suggestion.get('severity', 'low').lower()
            if severity in severity_count:
                severity_count[severity] += 1
        
        # 计算安全和性能评分
        security_suggestions = [s for s in suggestions if 'security' in s.get('category', '').lower()]
        performance_suggestions = [s for s in suggestions if 'performance' in s.get('category', '').lower()]
        
        security_score = max(0, 100 - len(security_suggestions) * 10)
        performance_score = max(0, 100 - len(performance_suggestions) * 5)
        
        # 生成建议
        recommendations = []
        if severity_count["critical"] > 0:
            recommendations.append(f"🚨 发现{severity_count['critical']}个严重问题，需要立即处理")
        if severity_count["high"] > 0:
            recommendations.append(f"⚠️  发现{severity_count['high']}个高危问题，建议优先处理")
        if len(security_suggestions) > 5:
            recommendations.append("🔒 安全配置需要重点关注")
        if len(performance_suggestions) > 3:
            recommendations.append("⚡ 性能优化有较大提升空间")
        
        if not recommendations:
            recommendations.append("✅ 网站配置整体良好，建议定期检查")
        
        return {
            "total_issues": len(suggestions),
            "critical_issues": severity_count["critical"],
            "high_issues": severity_count["high"],
            "medium_issues": severity_count["medium"],
            "low_issues": severity_count["low"],
            "security_score": f"{security_score}/100",
            "performance_score": f"{performance_score}/100",
            "recommendations": recommendations
        }
    
    @staticmethod
    def _get_recommendations(analysis_result):
        """获取下一步建议"""
        if not analysis_result or 'suggestions' not in analysis_result:
            return [
                "检查目标网站是否可正常访问",
                "确认网络连接是否正常",
                "尝试使用完整扫描模式获取更多信息"
            ]
        
        suggestions = analysis_result.get('suggestions', [])
        critical_suggestions = [s for s in suggestions if s.get('severity', '').lower() == 'critical']
        security_suggestions = [s for s in suggestions if 'security' in s.get('category', '').lower()]
        
        recommendations = []
        
        if critical_suggestions:
            recommendations.append("立即处理发现的严重安全漏洞")
            recommendations.append("检查服务器安全配置")
        
        if security_suggestions:
            recommendations.append("配置HTTP安全头")
            recommendations.append("启用HTTPS并配置SSL证书")
        
        if len(suggestions) > 10:
            recommendations.append("建议使用完整扫描模式获取详细报告")
            recommendations.append("制定系统性的配置优化计划")
        
        recommendations.extend([
            "定期进行网站安全扫描",
            "监控网站性能指标变化",
            "建立配置管理最佳实践"
        ])
        
        return recommendations[:5]  # 限制建议数量

class MySQLOptimizationProtocol:
    @staticmethod
    def execute(params=None):
        """
        MySQL数据库配置优化协议
        按顺序执行 mysql_optimizer.py -> analyze_config.py -> generate_report.py
        生成优化建议报告并保存到 mysql_report/ 目录
        """
        try:
            import sys
            import os
            
            # 智能查找mysql_report目录
            current_dir = os.getcwd()
            script_dir = None
            
            # 方法1: 检查当前目录是否已经在MCPArchieve目录中
            if current_dir.endswith("MCPArchieve"):
                potential_dir = os.path.join(current_dir, "mysql_report")
                if os.path.exists(potential_dir):
                    script_dir = potential_dir
            
            # 方法2: 从当前目录向上查找MCPArchieve目录
            if script_dir is None:
                search_dir = current_dir
                while search_dir != "/" and search_dir != "":
                    mcp_dir = os.path.join(search_dir, "MCPArchieve")
                    if os.path.exists(mcp_dir):
                        potential_dir = os.path.join(mcp_dir, "mysql_report")
                        if os.path.exists(potential_dir):
                            script_dir = potential_dir
                            break
                    search_dir = os.path.dirname(search_dir)
            
            # 方法3: 使用脚本文件的相对路径
            if script_dir is None:
                script_path = os.path.abspath(__file__)
                mcp_archive_dir = os.path.dirname(os.path.dirname(script_path))
                potential_dir = os.path.join(mcp_archive_dir, "mysql_report")
                if os.path.exists(potential_dir):
                    script_dir = potential_dir
            
            if script_dir is None or not os.path.exists(script_dir):
                return {
                    "status": "error",
                    "message": f"无法找到MySQL优化脚本目录 mysql_report/。请确保目录结构正确。\n"
                              f"当前工作目录: {current_dir}\n"
                              f"查找的目录: {script_dir if script_dir else '未找到'}"
                }
            
            # 检查必要的脚本文件是否存在
            required_scripts = ["mysql_optimizer.py", "analyze_config.py", "generate_report.py"]
            missing_scripts = []
            for script in required_scripts:
                if not os.path.exists(os.path.join(script_dir, script)):
                    missing_scripts.append(script)
            
            if missing_scripts:
                return {
                    "status": "error", 
                    "message": f"缺少必要的脚本文件: {', '.join(missing_scripts)}"
                }
            
            # 记录执行步骤
            execution_steps = []
            generated_files = []
            
            # 切换到脚本目录并记录原始目录
            original_dir = os.getcwd()
            os.chdir(script_dir)
            
            # 添加调试信息
            execution_steps.append(f"切换到脚本目录: {script_dir}")
            execution_steps.append(f"原始工作目录: {original_dir}")
            
            # 第1步：执行mysql_optimizer.py
            execution_steps.append("正在收集MySQL配置和系统信息...")
            result1 = subprocess.run([sys.executable, "mysql_optimizer.py"], 
                                   capture_output=True, text=True, timeout=300)
            
            if result1.returncode != 0:
                os.chdir(original_dir)  # 恢复工作目录
                return {
                    "status": "error",
                    "message": f"mysql_optimizer.py执行失败: {result1.stderr}",
                    "steps": execution_steps
                }
            
            # 读取当前检测信息
            detection_number = 1
            current_files = {}
            if os.path.exists("current_detection.json"):
                try:
                    with open("current_detection.json") as f:
                        detection_info = json.load(f)
                        detection_number = detection_info["detection_number"]
                        current_files = detection_info["files"]
                except:
                    pass
            
            execution_steps.append(f"✅ MySQL配置收集完成 (检测 #{detection_number})")
            if current_files.get('optimization_report') and os.path.exists(current_files['optimization_report']):
                generated_files.append(current_files['optimization_report'])
            
            # 第2步：执行analyze_config.py
            execution_steps.append("正在分析配置并生成优化建议...")
            result2 = subprocess.run([sys.executable, "analyze_config.py"], 
                                   capture_output=True, text=True, timeout=60)
            
            if result2.returncode != 0:
                os.chdir(original_dir)  # 恢复工作目录
                return {
                    "status": "error",
                    "message": f"analyze_config.py执行失败: {result2.stderr}",
                    "steps": execution_steps
                }
            
            execution_steps.append("✅ 配置分析完成")
            if current_files.get('suggestions') and os.path.exists(current_files['suggestions']):
                generated_files.append(current_files['suggestions'])
            
            # 第3步：执行generate_report.py
            execution_steps.append("正在生成HTML报告...")
            result3 = subprocess.run([sys.executable, "generate_report.py"], 
                                   capture_output=True, text=True, timeout=60)
            
            if result3.returncode != 0:
                os.chdir(original_dir)  # 恢复工作目录
                return {
                    "status": "error",
                    "message": f"generate_report.py执行失败: {result3.stderr}",
                    "steps": execution_steps
                }
            
            execution_steps.append("✅ HTML报告生成完成")
            if current_files.get('html_report') and os.path.exists(current_files['html_report']):
                generated_files.append(current_files['html_report'])
            
            # 检查是否有其他生成的文件
            if current_files.get('summary') and os.path.exists(current_files['summary']):
                generated_files.append(current_files['summary'])
            if current_files.get('advisor') and os.path.exists(current_files['advisor']):
                generated_files.append(current_files['advisor'])
            
            # 恢复原始工作目录
            os.chdir(original_dir)
            execution_steps.append(f"恢复工作目录: {original_dir}")
            
            # 读取优化建议摘要
            suggestions_summary = []
            suggestions_file = os.path.join(script_dir, current_files.get('suggestions', 'mysql_suggestions.json'))
            if os.path.exists(suggestions_file):
                try:
                    with open(suggestions_file, 'r', encoding='utf-8') as f:
                        suggestions_data = json.load(f)
                        for suggestion in suggestions_data[:5]:  # 只显示前5个建议
                            suggestions_summary.append({
                                "issue": suggestion.get("issue", ""),
                                "severity": suggestion.get("severity", ""),
                                "current": suggestion.get("current", ""),
                                "recommended": suggestion.get("recommended", "")
                            })
                except:
                    suggestions_summary.append({"issue": "无法读取优化建议", "severity": "info"})
            
            # 构建结果摘要
            key_findings = []
            key_findings.append(f"成功生成 {len(generated_files)} 个文件")
            key_findings.append("已完成MySQL配置收集和分析")
            key_findings.append("已生成HTML优化报告")
            if suggestions_summary:
                key_findings.append(f"发现 {len(suggestions_summary)} 个配置优化建议")
            
            return {
                "status": "success",
                "summary": {
                    "key_findings": key_findings,
                    "execution_steps": execution_steps,
                    "generated_files": generated_files,
                    "report_location": os.path.relpath(script_dir, original_dir),
                    "absolute_path": script_dir,
                    "detection_number": detection_number,
                    "main_report": current_files.get('html_report', 'mysql_optimization_report.html'),
                    "optimization_suggestions": suggestions_summary
                },
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "total_files": len(generated_files),
                    "script_location": script_dir,
                    "scripts_executed": ["mysql_optimizer.py", "analyze_config.py", "generate_report.py"]
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "脚本执行超时，请检查MySQL连接和配置"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行MySQL配置优化分析时出错: {str(e)}"
            }

class SkyWalkingProtocol:
    @staticmethod
    def execute(params=None):
        """
        SkyWalking分布式追踪和微服务监控协议
        当用户询问微服务、分布式、异常服务、资源关联、资源依赖关系、异常根因定位等问题时调用
        """
        try:
            # 设置脚本路径
            script_path = "/home/denerate/rca_sky-main/main.py"
            
            # 检查脚本是否存在
            if not os.path.exists(script_path):
                return {
                    "status": "error",
                    "message": f"SkyWalking分析脚本不存在: {script_path}"
                }
            
            # 执行SkyWalking根因分析脚本，实时输出到终端
            import sys
            from io import StringIO
            
            print(f"🚀 开始执行SkyWalking分析脚本: {script_path}")
            print("=" * 80)
            
            # 使用Popen来实现实时输出
            process = subprocess.Popen(
                ["python3", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
                cwd=os.path.dirname(script_path)
            )
            
            # 实时读取并输出，同时收集所有输出
            output_lines = []
            try:
                while True:
                    line = process.stdout.readline()
                    if line == '' and process.poll() is not None:
                        break
                    if line:
                        # 实时输出到终端
                        print(line.rstrip())
                        sys.stdout.flush()
                        # 同时收集输出
                        output_lines.append(line.rstrip())
                
                # 等待进程完成
                return_code = process.wait(timeout=300)  # 5分钟超时
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise subprocess.TimeoutExpired(process.args, 300)
            
            # 合并所有输出
            full_output = '\n'.join(output_lines)
            
            print("=" * 80)
            print(f"✅ SkyWalking分析脚本执行完成，退出码: {return_code}")
            
            # 处理执行结果
            if return_code == 0:
                return {
                    "status": "success",
                    "message": "SkyWalking分布式追踪分析完成",
                    "output": full_output,
                    "summary": {
                        "analysis_type": "微服务分布式追踪与根因分析",
                        "tool": "SkyWalking + AI智能分析",
                        "execution_time": "实时分析",
                        "output_files": "结果已导出到文件",
                        "next_steps": "查看分析报告获取详细信息"
                    },
                    "raw_output": full_output,
                    "error_output": None
                }
            else:
                return {
                    "status": "error", 
                    "message": f"SkyWalking分析脚本执行失败 (退出码: {return_code})",
                    "error": "详细错误信息已在上方输出中显示",
                    "output": full_output
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "SkyWalking分析脚本执行超时（超过5分钟）"
            }
        except FileNotFoundError:
            return {
                "status": "error", 
                "message": "未找到python3命令，请确保Python已正确安装"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行SkyWalking分析时出错: {str(e)}"
            }

class AnomalyPatternDetectionProtocol:
    """异常模式检测协议 - 集成abnormal_pattern_detect功能"""
    
    @staticmethod
    def execute(params=None):
        """
        执行异常模式检测和扫描
        :param params: 字典参数
            - action: 执行动作 (run_pipeline, run_scanner, status)
            - service: 服务名称 (mysql, nginx, system, loki, promptail, node_exporter)
            - scanner_type: 扫描器类型 (metrics, logs)
        """
        import subprocess
        import os
        import json
        from datetime import datetime
        
        # 设置默认参数
        action = "run_pipeline"
        service = None
        scanner_type = "metrics"
        
        if params:
            action = params.get("action", action)
            service = params.get("service", service)
            scanner_type = params.get("scanner_type", scanner_type)
        
        # 异常模式检测系统路径
        anomaly_detect_path = "/home/denerate/abnormal_pattern_detect"
        
        try:
            if action == "run_pipeline":
                return AnomalyPatternDetectionProtocol._run_complete_pipeline(anomaly_detect_path)
            elif action == "analyze_existing_risks":
                return AnomalyPatternDetectionProtocol._analyze_existing_risks(anomaly_detect_path)
            elif action == "run_scanner":
                return AnomalyPatternDetectionProtocol._run_scanner(anomaly_detect_path, service, scanner_type)
            elif action == "status":
                return AnomalyPatternDetectionProtocol._get_system_status(anomaly_detect_path)
            elif action == "list_scanners":
                return AnomalyPatternDetectionProtocol._list_available_scanners(anomaly_detect_path)
            else:
                return {
                    "status": "error",
                    "message": f"不支持的操作: {action}",
                    "supported_actions": ["run_pipeline", "analyze_existing_risks", "run_scanner", "status", "list_scanners"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"异常模式检测执行失败: {str(e)}",
                "action": action
            }
    
    @staticmethod
    def _run_complete_pipeline(anomaly_detect_path):
        """运行完整的异常模式检测流程"""
        try:
            print(f"🚀 开始执行异常模式检测完整流程")
            print(f"📂 工作目录: {anomaly_detect_path}")
            
            # 检查目录是否存在
            if not os.path.exists(anomaly_detect_path):
                return {
                    "status": "error",
                    "message": f"异常模式检测目录不存在: {anomaly_detect_path}"
                }
            
            # 切换到工作目录
            original_dir = os.getcwd()
            os.chdir(anomaly_detect_path)
            
            # 执行主程序
            cmd = ["python3", "main.py", "run"]
            print(f"📋 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            # 恢复工作目录
            os.chdir(original_dir)
            
            # 分析执行结果
            if result.returncode == 0:
                # 检查生成的文件
                generated_files = AnomalyPatternDetectionProtocol._check_generated_files(anomaly_detect_path)
                
                # 自动执行所有生成的扫描器
                scan_results = AnomalyPatternDetectionProtocol._execute_all_scanners(anomaly_detect_path)
                
                return {
                    "status": "success",
                    "message": "异常模式检测完整流程执行成功",
                    "execution_time": datetime.now().isoformat(),
                    "command": " ".join(cmd),
                    "summary": {
                        "pipeline_steps": [
                            "数据采集 - 收集系统指标和日志",
                            "异常检测 - 识别异常模式",
                            "模式提取 - 提取异常特征",
                            "扫描器生成 - 生成检测脚本",
                            "扫描器执行 - 执行所有生成的扫描器"
                        ],
                        "generated_files": generated_files,
                        "scanners_available": len(generated_files.get("scanners", [])),
                        "patterns_extracted": len(generated_files.get("patterns", [])),
                        "data_collected": len(generated_files.get("data", [])),
                        "scanners_executed": len(scan_results),
                        "scan_results": scan_results
                    },
                    "raw_output": result.stdout[-2000:] if result.stdout else "",  # 最后2000字符
                    "risk_assessment": AnomalyPatternDetectionProtocol._calculate_risk_probability(scan_results)
                }
            else:
                return {
                    "status": "error",
                    "message": f"异常模式检测流程执行失败 (返回码: {result.returncode})",
                    "command": " ".join(cmd),
                    "stderr": result.stderr[-1000:] if result.stderr else "",
                    "stdout": result.stdout[-1000:] if result.stdout else ""
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "异常模式检测流程执行超时（超过10分钟）"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行异常模式检测流程时出错: {str(e)}"
            }
    
    @staticmethod
    def _analyze_existing_risks(anomaly_detect_path):
        """分析现有风险 - 利用现有所有扫描器进行扫描并分析机器风险情况"""
        try:
            print(f"🔍 开始分析现有风险")
            print(f"📂 工作目录: {anomaly_detect_path}")
            
            # 检查目录是否存在
            if not os.path.exists(anomaly_detect_path):
                return {
                    "status": "error",
                    "message": f"异常模式检测目录不存在: {anomaly_detect_path}"
                }
            
            # 获取所有可用的扫描器
            available_scanners = AnomalyPatternDetectionProtocol._list_available_scanners(anomaly_detect_path)
            
            if not available_scanners.get("scanners"):
                return {
                    "status": "error",
                    "message": "未找到可用的扫描器",
                    "available_scanners": available_scanners
                }
            
            # 执行所有可用的扫描器
            print(f"🚀 开始执行所有可用扫描器进行风险分析")
            scan_results = AnomalyPatternDetectionProtocol._execute_all_scanners(anomaly_detect_path)
            
            # 分析扫描结果
            risk_analysis = AnomalyPatternDetectionProtocol._analyze_comprehensive_risks(scan_results)
            
            # 精简返回结果，避免token超限
            return {
                "status": "success",
                "message": "现有风险分析完成",
                "execution_time": datetime.now().isoformat(),
                "analysis_type": "comprehensive_risk_analysis",
                "scanners_count": len(available_scanners.get("scanners", [])),
                "services_scanned": len(scan_results) if isinstance(scan_results, dict) else 0,
                "risk_analysis": {
                    "overall_risk_level": risk_analysis.get("overall_risk_level", "未知"),
                    "high_risk_count": len(risk_analysis.get("high_risk_services", [])),
                    "medium_risk_count": len(risk_analysis.get("medium_risk_services", [])),
                    "low_risk_count": len(risk_analysis.get("low_risk_services", [])),
                    "critical_issues": risk_analysis.get("critical_issues", [])[:5],  # 只返回前5个关键问题
                    "recommendations": risk_analysis.get("recommendations", [])[:3],  # 只返回前3个建议
                    "risk_summary": risk_analysis.get("risk_summary", "")
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"分析现有风险时出错: {str(e)}"
            }
    
    @staticmethod
    def _run_scanner(anomaly_detect_path, service, scanner_type):
        """运行特定的扫描器"""
        try:
            if not service:
                return {
                    "status": "error",
                    "message": "必须指定服务名称",
                    "supported_services": ["mysql", "nginx", "system", "loki", "promptail", "node_exporter"]
                }
            
            # 构建扫描器文件名
            scanner_file = f"scan_{service}_{scanner_type}.py"
            scanner_path = os.path.join(anomaly_detect_path, "scanners", scanner_file)
            
            # 检查扫描器是否存在
            if not os.path.exists(scanner_path):
                # 尝试其他可能的文件名
                alternative_files = [
                    f"scan_{service}_logs.py",
                    f"scan_{service}_metrics.py",
                    f"scan_{service}.py"
                ]
                
                for alt_file in alternative_files:
                    alt_path = os.path.join(anomaly_detect_path, "scanners", alt_file)
                    if os.path.exists(alt_path):
                        scanner_path = alt_path
                        scanner_file = alt_file
                        break
                else:
                    return {
                        "status": "error",
                        "message": f"未找到服务 {service} 的扫描器",
                        "searched_files": [scanner_file] + alternative_files,
                        "available_scanners": AnomalyPatternDetectionProtocol._list_scanner_files(anomaly_detect_path)
                    }
            
            print(f"🔍 开始执行扫描器: {scanner_file}")
            print(f"📂 扫描器路径: {scanner_path}")
            
            # 切换到工作目录
            original_dir = os.getcwd()
            os.chdir(os.path.dirname(scanner_path))
            
            # 执行扫描器
            cmd = ["python3", scanner_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 恢复工作目录
            os.chdir(original_dir)
            
            # 分析扫描结果
            scan_results = AnomalyPatternDetectionProtocol._parse_scan_results(anomaly_detect_path, service)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"{service} 服务扫描完成",
                    "service": service,
                    "scanner_type": scanner_type,
                    "scanner_file": scanner_file,
                    "execution_time": datetime.now().isoformat(),
                    "command": " ".join(cmd),
                    "scan_results": scan_results,
                    "raw_output": result.stdout[-1500:] if result.stdout else "",
                    "anomaly_analysis": AnomalyPatternDetectionProtocol._analyze_scan_anomalies(scan_results)
                }
            else:
                return {
                    "status": "error",
                    "message": f"{service} 服务扫描失败 (返回码: {result.returncode})",
                    "service": service,
                    "scanner_file": scanner_file,
                    "command": " ".join(cmd),
                    "stderr": result.stderr[-800:] if result.stderr else "",
                    "stdout": result.stdout[-800:] if result.stdout else ""
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"{service} 服务扫描超时（超过5分钟）"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行 {service} 服务扫描时出错: {str(e)}"
            }
    
    @staticmethod
    def _get_system_status(anomaly_detect_path):
        """获取系统状态"""
        try:
            status_file = os.path.join(anomaly_detect_path, "data", "system_status.json")
            
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            else:
                status = {
                    'last_collection_time': None,
                    'last_pattern_extraction_time': None,
                    'last_scanner_generation_time': None,
                    'total_patterns_extracted': 0,
                    'total_scanners_generated': 0,
                    'system_initialized': False
                }
            
            # 检查生成的文件
            generated_files = AnomalyPatternDetectionProtocol._check_generated_files(anomaly_detect_path)
            
            return {
                "status": "success",
                "message": "系统状态获取成功",
                "system_status": status,
                "generated_files": generated_files,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取系统状态失败: {str(e)}"
            }
    
    @staticmethod
    def _list_available_scanners(anomaly_detect_path):
        """列出可用的扫描器"""
        try:
            scanner_files = AnomalyPatternDetectionProtocol._list_scanner_files(anomaly_detect_path)
            
            # 解析扫描器信息
            scanners_info = []
            for scanner_file in scanner_files:
                if scanner_file.endswith('.py') and scanner_file.startswith('scan_'):
                    service_name = scanner_file[5:-3]  # 去掉 'scan_' 前缀和 '.py' 后缀
                    scanners_info.append({
                        "file": scanner_file,
                        "service": service_name,
                        "type": "logs" if "logs" in scanner_file else "metrics"
                    })
            
            return {
                "status": "success",
                "message": "可用扫描器列表获取成功",
                "scanners": scanners_info,
                "total_scanners": len(scanners_info),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取扫描器列表失败: {str(e)}"
            }
    
    @staticmethod
    def _check_generated_files(anomaly_detect_path):
        """检查生成的文件"""
        files = {
            "data": [],
            "patterns": [],
            "scanners": [],
            "reports": []
        }
        
        # 检查数据目录
        data_dir = os.path.join(anomaly_detect_path, "data")
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                file_path = os.path.join(data_dir, file)
                if os.path.isfile(file_path):
                    if file.endswith('.json'):
                        if 'pattern' in file:
                            files["patterns"].append(file)
                        else:
                            files["data"].append(file)
                    elif file.endswith('.log'):
                        files["data"].append(file)
        
        # 检查扫描器目录
        scanners_dir = os.path.join(anomaly_detect_path, "scanners")
        if os.path.exists(scanners_dir):
            for file in os.listdir(scanners_dir):
                if file.endswith('.py') and file.startswith('scan_'):
                    files["scanners"].append(file)
        
        return files
    
    @staticmethod
    def _list_scanner_files(anomaly_detect_path):
        """列出扫描器文件"""
        scanners_dir = os.path.join(anomaly_detect_path, "scanners")
        if os.path.exists(scanners_dir):
            return [f for f in os.listdir(scanners_dir) if f.endswith('.py')]
        return []
    
    @staticmethod
    def _parse_scan_results(anomaly_detect_path, service):
        """解析扫描结果"""
        # 查找最新的扫描结果文件 - 从scanners/results目录
        results_dir = os.path.join(anomaly_detect_path, "scanners", "results")
        if not os.path.exists(results_dir):
            return {}
        
        # 查找包含服务名的扫描结果文件
        scan_files = []
        for file in os.listdir(results_dir):
            if file.startswith(f"scan_results_{service}_") and file.endswith('.json'):
                scan_files.append(file)
        
        if not scan_files:
            # 如果没有找到特定服务的扫描结果，尝试查找根目录下的扫描结果（兼容旧格式）
            root_scan_files = []
            for file in os.listdir(anomaly_detect_path):
                if file.startswith(f"scan_results_{service}_") and file.endswith('.json'):
                    root_scan_files.append(file)
            
            if root_scan_files:
                latest_file = max(root_scan_files, key=lambda x: os.path.getmtime(os.path.join(anomaly_detect_path, x)))
                latest_path = os.path.join(anomaly_detect_path, latest_file)
            else:
                return {}
        else:
            # 获取最新的扫描结果文件
            latest_file = max(scan_files, key=lambda x: os.path.getmtime(os.path.join(results_dir, x)))
            latest_path = os.path.join(results_dir, latest_file)
        
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                scan_data = json.load(f)
                
                # 转换新格式的扫描结果为标准格式
                if isinstance(scan_data, dict):
                    # 新格式的扫描器返回的是完整的扫描结果
                    return {
                        "scan_info": {
                            "service_name": scan_data.get("service_name", service),
                            "pattern_id": scan_data.get("pattern_id", "unknown"),
                            "scan_start_time": scan_data.get("scan_start_time"),
                            "scan_end_time": scan_data.get("scan_end_time")
                        },
                        "anomaly_analysis": scan_data.get("results", {}).get("anomaly_analysis", {}),
                        "summary": scan_data.get("summary", {}),
                        "results": scan_data.get("results", {}),
                        "pattern_statistics": scan_data.get("pattern_statistics", {})
                    }
                else:
                    return scan_data
                    
        except Exception as e:
            return {"error": f"解析扫描结果失败: {str(e)}"}
    
    @staticmethod
    def _analyze_scan_anomalies(scan_results):
        """分析扫描结果中的异常"""
        if not scan_results or isinstance(scan_results, dict) and "error" in scan_results:
            return {
                "severity_score": 0,
                "severity_level": "正常",
                "anomalies": [],
                "total_anomalies": 0
            }
        
        anomalies = []
        severity_score = 0
        
        # 分析新格式的扫描结果
        if isinstance(scan_results, dict):
            # 检查异常分析结果
            if "anomaly_analysis" in scan_results:
                anomaly_analysis = scan_results["anomaly_analysis"]
                severity_score = anomaly_analysis.get("severity_score", 0)
                total_anomalies = anomaly_analysis.get("total_anomalies", 0)
                
                # 处理异常列表
                anomaly_list = anomaly_analysis.get("anomalies", [])
                for anomaly in anomaly_list:
                    anomaly_type = anomaly.get("type", "未知异常")
                    severity = anomaly.get("severity", "medium")
                    
                    # 转换严重程度为数值
                    severity_value = {
                        "critical": 10,
                        "high": 8,
                        "medium": 5,
                        "low": 2
                    }.get(severity, 5)
                    
                    anomalies.append({
                        "type": anomaly_type,
                        "details": anomaly,
                        "severity": severity_value,
                        "description": anomaly.get("description", "未知异常")
                    })
            
            # 检查摘要信息
            elif "summary" in scan_results:
                summary = scan_results["summary"]
                severity_score = summary.get("severity_score", 0)
                total_anomalies = summary.get("total_anomalies", 0)
                
                # 如果摘要中有异常信息
                if total_anomalies > 0:
                    anomalies.append({
                        "type": "综合异常",
                        "details": summary,
                        "severity": min(severity_score, 10),
                        "description": f"检测到 {total_anomalies} 个异常"
                    })
            
            # 检查结果中的异常
            elif "results" in scan_results:
                results = scan_results["results"]
                
                # 检查系统指标异常
                if "system_metrics" in results:
                    system_metrics = results["system_metrics"]
                    if system_metrics.get("status") != "normal":
                        system_anomalies = system_metrics.get("anomalies", [])
                        for anomaly in system_anomalies:
                            anomalies.append({
                                "type": "系统指标异常",
                                "details": anomaly,
                                "severity": 5,
                                "description": anomaly.get("description", "系统指标异常")
                            })
                        severity_score = max(severity_score, 5)
                
                # 检查进程指标异常
                if "process_metrics" in results:
                    process_metrics = results["process_metrics"]
                    if process_metrics.get("status") != "normal":
                        process_anomalies = process_metrics.get("anomalies", [])
                        for anomaly in process_anomalies:
                            anomalies.append({
                                "type": "进程异常",
                                "details": anomaly,
                                "severity": 6,
                                "description": anomaly.get("description", "进程异常")
                            })
                        severity_score = max(severity_score, 6)
                
                # 检查日志异常
                if "log_anomalies" in results:
                    log_anomalies = results["log_anomalies"]
                    if log_anomalies.get("status") != "normal":
                        log_anomaly_list = log_anomalies.get("anomalies", [])
                        for anomaly in log_anomaly_list:
                            anomalies.append({
                                "type": "日志异常",
                                "details": anomaly,
                                "severity": 7,
                                "description": anomaly.get("description", "日志异常")
                            })
                        severity_score = max(severity_score, 7)
        
        return {
            "severity_score": severity_score,
            "severity_level": AnomalyPatternDetectionProtocol._get_severity_description(severity_score),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    @staticmethod
    def _get_severity_description(score):
        """根据评分获取严重程度描述"""
        if score == 0:
            return "正常"
        elif score <= 3:
            return "轻微异常"
        elif score <= 6:
            return "中等异常"
        elif score <= 8:
            return "严重异常"
        else:
            return "危急异常"
    
    @staticmethod
    def _execute_all_scanners(anomaly_detect_path):
        """执行所有生成的扫描器"""
        scan_results = {}
        scanners_dir = os.path.join(anomaly_detect_path, "scanners")
        
        if not os.path.exists(scanners_dir):
            return scan_results
        
        # 获取所有扫描器文件
        scanner_files = [f for f in os.listdir(scanners_dir) if f.endswith('.py') and f.startswith('scan_')]
        
        print(f"🔍 发现 {len(scanner_files)} 个扫描器，开始执行...")
        
        for scanner_file in scanner_files:
            try:
                # 提取服务名称
                service_name = scanner_file[5:-3]  # 去掉 'scan_' 前缀和 '.py' 后缀
                
                print(f"🔍 执行扫描器: {scanner_file}")
                
                # 切换到扫描器目录
                original_dir = os.getcwd()
                os.chdir(scanners_dir)
                
                # 执行扫描器
                result = subprocess.run(
                    ["python3", scanner_file],
                    capture_output=True,
                    text=True,
                    timeout=120  # 2分钟超时
                )
                
                # 恢复工作目录
                os.chdir(original_dir)
                
                # 等待一小段时间确保文件写入完成
                import time
                time.sleep(2)
                
                # 解析扫描结果
                scan_data = AnomalyPatternDetectionProtocol._parse_scan_results(anomaly_detect_path, service_name)
                
                scan_results[service_name] = {
                    "scanner_file": scanner_file,
                    "execution_status": "success" if result.returncode == 0 else "failed",
                    "return_code": result.returncode,
                    "scan_data": scan_data,
                    "raw_output": result.stdout[-500:] if result.stdout else "",
                    "error": result.stderr[-200:] if result.stderr else ""
                }
                
            except Exception as e:
                scan_results[service_name] = {
                    "scanner_file": scanner_file,
                    "execution_status": "error",
                    "error": str(e)
                }
        
        return scan_results
    
    @staticmethod
    def _calculate_risk_probability(scan_results):
        """计算机器存在风险的概率"""
        if not scan_results:
            return {
                "risk_probability": 0,
                "risk_level": "极低风险",
                "calculation_details": {
                    "pattern_match_score": 0,
                    "historical_frequency": 0,
                    "service_importance": 0,
                    "environmental_factors": 0
                },
                "risk_analysis": "无扫描数据，无法评估风险"
            }
        
        # 计算模式匹配度 (40% 权重)
        pattern_match_score = 0
        total_anomalies = 0
        total_scanners = len(scan_results)
        
        for service, result in scan_results.items():
            if result.get("execution_status") == "success":
                scan_data = result.get("scan_data", {})
                if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                    anomaly_analysis = scan_data["anomaly_analysis"]
                    severity_score = anomaly_analysis.get("severity_score", 0)
                    total_anomalies += anomaly_analysis.get("total_anomalies", 0)
                    
                    # 根据严重程度计算匹配度
                    if severity_score > 0:
                        pattern_match_score += severity_score / 10.0  # 转换为0-1范围
        
        # 计算平均模式匹配度
        if total_scanners > 0:
            pattern_match_score = (pattern_match_score / total_scanners) * 100
        
        # 计算历史频率 (30% 权重) - 基于异常数量
        historical_frequency = min(total_anomalies * 10, 100)  # 每个异常10%概率，最大100%
        
        # 计算服务重要性 (20% 权重) - 基于关键服务数量
        critical_services = ["mysql", "nginx", "system", "loki"]
        service_importance = 0
        for service in critical_services:
            if service in scan_results:
                service_importance += 25  # 每个关键服务25%重要性
        service_importance = min(service_importance, 100)
        
        # 计算环境因素 (10% 权重) - 基于扫描成功率
        successful_scans = sum(1 for r in scan_results.values() if r.get("execution_status") == "success")
        environmental_factors = (successful_scans / total_scanners) * 100 if total_scanners > 0 else 0
        
        # 计算综合风险概率
        risk_probability = (
            pattern_match_score * 0.4 +
            historical_frequency * 0.3 +
            service_importance * 0.2 +
            environmental_factors * 0.1
        )
        
        # 确定风险等级
        if risk_probability <= 20:
            risk_level = "极低风险"
        elif risk_probability <= 40:
            risk_level = "低风险"
        elif risk_probability <= 60:
            risk_level = "中等风险"
        elif risk_probability <= 80:
            risk_level = "高风险"
        else:
            risk_level = "极高风险"
        
        return {
            "risk_probability": round(risk_probability, 2),
            "risk_level": risk_level,
            "calculation_details": {
                "pattern_match_score": round(pattern_match_score, 2),
                "historical_frequency": round(historical_frequency, 2),
                "service_importance": round(service_importance, 2),
                "environmental_factors": round(environmental_factors, 2)
            },
            "risk_analysis": f"基于{total_scanners}个服务的扫描结果，发现{total_anomalies}个异常，综合评估机器存在{risk_level}",
            "monitoring_suggestions": AnomalyPatternDetectionProtocol._generate_monitoring_suggestions(risk_probability, scan_results),
            "service_analysis": AnomalyPatternDetectionProtocol._generate_service_analysis(scan_results),
            "overall_summary": AnomalyPatternDetectionProtocol._generate_overall_summary(scan_results, risk_probability, risk_level)
        }
    
    @staticmethod
    def _generate_monitoring_suggestions(risk_probability, scan_results):
        """生成监控建议"""
        suggestions = []
        
        if risk_probability <= 20:
            suggestions.extend([
                "建议每周进行一次完整扫描",
                "保持常规系统监控",
                "关注关键服务的运行状态"
            ])
        elif risk_probability <= 40:
            suggestions.extend([
                "建议每3天进行一次扫描",
                "重点关注异常服务",
                "加强日志监控"
            ])
        elif risk_probability <= 60:
            suggestions.extend([
                "建议每天进行一次扫描",
                "设置异常告警",
                "准备应急响应预案"
            ])
        elif risk_probability <= 80:
            suggestions.extend([
                "建议每6小时进行一次扫描",
                "立即处理发现的异常",
                "启动应急响应机制"
            ])
        else:
            suggestions.extend([
                "建议每小时进行一次扫描",
                "立即采取紧急措施",
                "考虑系统隔离或重启"
            ])
        
        # 添加具体服务建议
        critical_services = []
        for service, result in scan_results.items():
            if result.get("execution_status") == "success":
                scan_data = result.get("scan_data", {})
                if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                    anomaly_analysis = scan_data["anomaly_analysis"]
                    if anomaly_analysis.get("severity_score", 0) > 5:
                        critical_services.append(service)
        
        if critical_services:
            suggestions.append(f"重点关注服务: {', '.join(critical_services)}")
        
        return suggestions
    
    @staticmethod
    def _generate_service_analysis(scan_results):
        """生成各服务的详细分析"""
        service_analysis = {}
        
        for service, result in scan_results.items():
            service_info = {
                "service_name": service,
                "execution_status": result.get("execution_status", "unknown"),
                "status": "未知",
                "anomaly_types": [],
                "severity_score": 0,
                "risk_points": [],
                "optimization_suggestions": []
            }
            
            if result.get("execution_status") == "success":
                scan_data = result.get("scan_data", {})
                
                if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                    anomaly_analysis = scan_data["anomaly_analysis"]
                    severity_score = anomaly_analysis.get("severity_score", 0)
                    total_anomalies = anomaly_analysis.get("total_anomalies", 0)
                    
                    service_info["severity_score"] = severity_score
                    
                    # 确定服务状态
                    if severity_score == 0:
                        service_info["status"] = "正常"
                    elif severity_score <= 3:
                        service_info["status"] = "轻微异常"
                    elif severity_score <= 6:
                        service_info["status"] = "异常"
                    else:
                        service_info["status"] = "严重异常"
                    
                    # 分析异常类型
                    anomalies = anomaly_analysis.get("anomalies", [])
                    for anomaly in anomalies:
                        anomaly_type = anomaly.get("type", "未知异常")
                        service_info["anomaly_types"].append(anomaly_type)
                        
                        # 根据异常类型生成风险点
                        if "进程" in anomaly_type:
                            service_info["risk_points"].append("进程运行异常，可能存在资源竞争或死锁")
                        elif "系统指标" in anomaly_type:
                            service_info["risk_points"].append("系统资源使用异常，可能存在性能瓶颈")
                        elif "日志" in anomaly_type:
                            service_info["risk_points"].append("日志异常，可能存在配置错误或服务故障")
                    
                    # 生成优化建议
                    if severity_score > 0:
                        if "mysql" in service.lower():
                            service_info["optimization_suggestions"].extend([
                                "检查MySQL连接池配置",
                                "优化慢查询",
                                "检查数据库索引使用情况"
                            ])
                        elif "nginx" in service.lower():
                            service_info["optimization_suggestions"].extend([
                                "检查Nginx配置文件",
                                "优化worker进程数",
                                "检查访问日志和错误日志"
                            ])
                        elif "system" in service.lower():
                            service_info["optimization_suggestions"].extend([
                                "检查系统资源使用情况",
                                "优化系统参数配置",
                                "清理临时文件和日志"
                            ])
                        elif "loki" in service.lower():
                            service_info["optimization_suggestions"].extend([
                                "检查Loki存储配置",
                                "优化日志收集性能",
                                "检查Promtail配置"
                            ])
                        else:
                            service_info["optimization_suggestions"].append("检查服务配置和运行状态")
                else:
                    service_info["status"] = "扫描失败"
                    service_info["risk_points"].append("无法获取扫描数据")
            else:
                service_info["status"] = "执行失败"
                service_info["risk_points"].append(f"扫描器执行失败: {result.get('error', '未知错误')}")
            
            service_analysis[service] = service_info
        
        return service_analysis
    
    @staticmethod
    def _generate_overall_summary(scan_results, risk_probability, risk_level):
        """生成总体情况摘要"""
        total_services = len(scan_results)
        successful_scans = sum(1 for r in scan_results.values() if r.get("execution_status") == "success")
        success_rate = (successful_scans / total_services) * 100 if total_services > 0 else 0
        
        # 统计各状态的服务数量
        status_counts = {"正常": 0, "轻微异常": 0, "异常": 0, "严重异常": 0, "执行失败": 0}
        critical_services_status = {}
        
        for service, result in scan_results.items():
            if result.get("execution_status") == "success":
                scan_data = result.get("scan_data", {})
                if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                    anomaly_analysis = scan_data["anomaly_analysis"]
                    severity_score = anomaly_analysis.get("severity_score", 0)
                    
                    if severity_score == 0:
                        status_counts["正常"] += 1
                    elif severity_score <= 3:
                        status_counts["轻微异常"] += 1
                    elif severity_score <= 6:
                        status_counts["异常"] += 1
                    else:
                        status_counts["严重异常"] += 1
                else:
                    status_counts["执行失败"] += 1
            else:
                status_counts["执行失败"] += 1
            
            # 记录关键服务状态
            if service in ["mysql", "nginx", "system", "loki"]:
                if result.get("execution_status") == "success":
                    scan_data = result.get("scan_data", {})
                    if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                        anomaly_analysis = scan_data["anomaly_analysis"]
                        severity_score = anomaly_analysis.get("severity_score", 0)
                        if severity_score == 0:
                            critical_services_status[service] = "正常"
                        elif severity_score <= 3:
                            critical_services_status[service] = "轻微异常"
                        elif severity_score <= 6:
                            critical_services_status[service] = "异常"
                        else:
                            critical_services_status[service] = "严重异常"
                    else:
                        critical_services_status[service] = "扫描失败"
                else:
                    critical_services_status[service] = "执行失败"
        
        # 确定整体健康状态
        if status_counts["严重异常"] > 0:
            overall_health = "异常"
        elif status_counts["异常"] > 0:
            overall_health = "警告"
        elif status_counts["轻微异常"] > 0:
            overall_health = "轻微异常"
        else:
            overall_health = "正常"
        
        return {
            "total_services": total_services,
            "successful_scans": successful_scans,
            "success_rate": round(success_rate, 2),
            "overall_health": overall_health,
            "status_distribution": status_counts,
            "critical_services_status": critical_services_status,
            "risk_probability": risk_probability,
            "risk_level": risk_level
        }
    
    @staticmethod
    def _analyze_comprehensive_risks(scan_results):
        """综合分析所有扫描结果，评估机器整体风险情况"""
        try:
            if not scan_results or not isinstance(scan_results, dict):
                return {
                    "overall_risk_level": "未知",
                    "high_risk_services": [],
                    "medium_risk_services": [],
                    "low_risk_services": [],
                    "critical_issues": [],
                    "recommendations": [],
                    "risk_summary": "无法获取扫描结果进行分析"
                }
            
            high_risk_services = []
            medium_risk_services = []
            low_risk_services = []
            critical_issues = []
            total_severity_score = 0
            service_count = 0
            
            # 分析每个服务的风险情况
            for service, result in scan_results.items():
                if result.get("execution_status") == "success":
                    scan_data = result.get("scan_data", {})
                    if isinstance(scan_data, dict) and "anomaly_analysis" in scan_data:
                        anomaly_analysis = scan_data["anomaly_analysis"]
                        severity_score = anomaly_analysis.get("severity_score", 0)
                        total_severity_score += severity_score
                        service_count += 1
                        
                        # 根据严重程度分类服务（精简版）
                        if severity_score >= 7:
                            high_risk_services.append({
                                "service": service,
                                "severity_score": severity_score,
                                "status": "严重异常"
                            })
                            critical_issues.append(f"{service}服务严重异常(评分{severity_score})")
                        elif severity_score >= 4:
                            medium_risk_services.append({
                                "service": service,
                                "severity_score": severity_score,
                                "status": "异常"
                            })
                        else:
                            low_risk_services.append({
                                "service": service,
                                "severity_score": severity_score,
                                "status": "正常" if severity_score == 0 else "轻微异常"
                            })
                    else:
                        critical_issues.append(f"{service}服务扫描数据异常，无法获取有效信息")
                else:
                    critical_issues.append(f"{service}服务扫描失败：{result.get('error', '未知错误')}")
            
            # 计算整体风险等级
            avg_severity = total_severity_score / service_count if service_count > 0 else 0
            
            if avg_severity >= 6 or len(high_risk_services) >= 2:
                overall_risk_level = "高风险"
            elif avg_severity >= 3 or len(medium_risk_services) >= 2:
                overall_risk_level = "中风险"
            elif avg_severity > 0:
                overall_risk_level = "低风险"
            else:
                overall_risk_level = "正常"
            
            # 生成精简建议
            recommendations = []
            
            if high_risk_services:
                recommendations.append("立即处理高风险服务异常")
            
            if medium_risk_services:
                recommendations.append("监控中风险服务状态")
            
            if len(critical_issues) > 0:
                recommendations.append("检查扫描器配置和权限")
            
            if not recommendations:
                recommendations.append("系统运行正常")
            
            # 生成精简风险摘要
            risk_summary = f"扫描{len(scan_results)}个服务: {len(high_risk_services)}个高风险, {len(medium_risk_services)}个中风险, {len(low_risk_services)}个低风险. 整体风险: {overall_risk_level}"
            
            return {
                "overall_risk_level": overall_risk_level,
                "high_risk_services": high_risk_services,
                "medium_risk_services": medium_risk_services,
                "low_risk_services": low_risk_services,
                "critical_issues": critical_issues,
                "recommendations": recommendations,
                "risk_summary": risk_summary,
                "statistics": {
                    "total_services": len(scan_results),
                    "high_risk_count": len(high_risk_services),
                    "medium_risk_count": len(medium_risk_services),
                    "low_risk_count": len(low_risk_services),
                    "average_severity": round(avg_severity, 2)
                }
            }
            
        except Exception as e:
            return {
                "overall_risk_level": "分析失败",
                "high_risk_services": [],
                "medium_risk_services": [],
                "low_risk_services": [],
                "critical_issues": [f"风险分析过程中出错：{str(e)}"],
                "recommendations": ["检查系统配置和扫描器状态"],
                "risk_summary": f"风险分析失败：{str(e)}"
            }

class FusionLLMAnomalyDetectionProtocol:
    """Fusion LLM异常检测协议"""
    
    @staticmethod
    def execute(params=None):
        """
        执行Fusion LLM异常检测
        :param params: 字典参数 (支持detection_type, window_size, step_size等)
        """
        try:
            # 设置默认参数
            detection_type = "comprehensive"  # comprehensive, logs_only, metrics_only
            window_size = 20
            step_size = 20
            batch_size = 32
            
            if params:
                detection_type = params.get("detection_type", detection_type)
                window_size = params.get("window_size", window_size)
                step_size = params.get("step_size", step_size)
                batch_size = params.get("batch_size", batch_size)
            
            # 导入fusion_client
            import sys
            import os
            sys.path.insert(0, '/home/denerate/anomly_detecti_fusionLLM')
            
            try:
                from fusion_client import FusionLogLLMClient
            except ImportError as e:
                return {
                    "status": "error",
                    "message": f"无法导入fusion_client: {str(e)}",
                    "detection_type": detection_type
                }
            
            # 创建客户端
            client = FusionLogLLMClient("http://i-2.gpushare.com:25909")
            
            # 健康检查
            health = client.health_check()
            if "error" in health:
                return {
                    "status": "error",
                    "message": f"Fusion LLM服务连接失败: {health['error']}",
                    "detection_type": detection_type
                }
            
            if not health.get('model_loaded', False):
                return {
                    "status": "error",
                    "message": "Fusion LLM模型未加载，请检查服务器状态",
                    "detection_type": detection_type
                }
            
            # 准备数据
            print("准备异常检测数据...")
            
            # 加载日志数据
            try:
                bgl_logs = FusionLLMAnomalyDetectionProtocol._load_log_data()
                print(f"✅ 成功加载日志数据: {len(bgl_logs)} 条")
            except Exception as e:
                print(f"❌ 加载日志数据失败: {str(e)}")
                bgl_logs = []
            
            # 加载Prometheus指标数据
            try:
                prometheus_data = client.load_prometheus_data_from_directory()
                print(f"✅ 成功加载Prometheus数据: {len(prometheus_data)} 个类别")
            except Exception as e:
                print(f"❌ 加载Prometheus数据失败: {str(e)}")
                prometheus_data = {}
            
            # 加载SkyWalking数据
            try:
                skywalking_data = FusionLLMAnomalyDetectionProtocol._load_skywalking_data()
                print(f"✅ 成功加载SkyWalking数据: {len(skywalking_data)} 条")
            except Exception as e:
                print(f"❌ 加载SkyWalking数据失败: {str(e)}")
                skywalking_data = []
            
            # 根据检测类型调整数据
            if detection_type == "logs_only":
                prometheus_data = None
                skywalking_data = None
            elif detection_type == "metrics_only":
                bgl_logs = []
            
            # 执行异常检测
            print(f"开始执行{detection_type}异常检测...")
            detection_result = client.detect_anomalies_fusion(
                logs=bgl_logs,
                prometheus_data=prometheus_data,
                skywalking_data=skywalking_data,
                window_size=window_size,
                step_size=step_size,
                batch_size=batch_size
            )
            
            # 检查检测结果
            if "error" in detection_result:
                return {
                    "status": "error",
                    "message": f"异常检测失败: {detection_result['error']}",
                    "detection_type": detection_type
                }
            
            # 提取异常信息
            anomaly_information = client.extract_anomaly_information(detection_result)
            
            # 分析异常信息
            analysis_result = FusionLLMAnomalyDetectionProtocol._analyze_anomaly_information(
                anomaly_information, detection_type
            )
            
            return {
                "status": "success",
                "detection_type": detection_type,
                "timestamp": detection_result.get("timestamp", ""),
                "processing_time": detection_result.get("processing_time", 0),
                "anomaly_information": anomaly_information,
                "analysis_result": analysis_result,
                "raw_detection_result": detection_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"异常检测执行失败: {str(e)}",
                "detection_type": detection_type if 'detection_type' in locals() else "unknown"
            }
    
    @staticmethod
    def _load_log_data():
        """加载日志数据"""
        import json
        from datetime import datetime
        
        def convert_loki_to_bgl(log_file_path):
            """将Loki监控日志转换为BGL格式的日志"""
            bgl_logs = []
            
            # 定义默认值
            default_label = "-"
            default_id = ""
            default_date = datetime.now().strftime("%Y.%m.%d")
            default_code1 = "UNKNOWN"
            default_component1 = "RAS"
            default_component2 = "SYSTEM"
            default_level = "INFO"
            
            try:
                with open(log_file_path, 'r') as f:
                    for line in f:
                        try:
                            # 解析JSON格式的日志行
                            log_entry = json.loads(line.strip())
                            log_content = log_entry.get("log", "")
                            timestamp = log_entry.get("timestamp", "")
                            
                            # 解析时间戳
                            try:
                                log_time = datetime.fromisoformat(timestamp.rstrip("Z")).strftime("%Y-%m-%d-%H.%M.%S.%f")[:-3]
                                log_date = datetime.fromisoformat(timestamp.rstrip("Z")).strftime("%Y.%m.%d")
                            except:
                                log_time = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")[:-3]
                                log_date = datetime.now().strftime("%Y.%m.%d")
                            
                            # 确定日志级别
                            if "ERROR" in log_content or "FATAL" in log_content or "无法将url解析为ip" in log_content:
                                level = "ERROR"
                            elif "WARN" in log_content or "WARNING" in log_content:
                                level = "WARN"
                            elif "INFO" in log_content:
                                level = "INFO"
                            else:
                                level = default_level
                            
                            # 确定组件
                            if "kylin_kms_daemon" in log_content:
                                component2 = "KMS"
                            elif "systemd" in log_content:
                                component2 = "SYSTEMD"
                            elif "kernel" in log_content:
                                component2 = "KERNEL"
                            elif "network" in log_content:
                                component2 = "NETWORK"
                            elif "memory" in log_content:
                                component2 = "MEMORY"
                            elif "cpu" in log_content:
                                component2 = "CPU"
                            elif "disk" in log_content:
                                component2 = "DISK"
                            else:
                                component2 = default_component2
                            
                            # 构建BGL日志行
                            bgl_line = f"{default_label} {default_id} {log_date} {default_code1} {log_time} {default_code1} {default_component1} {component2} {level} {log_content}"
                            bgl_logs.append(bgl_line)
                            
                        except json.JSONDecodeError:
                            # 如果行不是有效的JSON，跳过
                            continue
            except FileNotFoundError:
                print(f"日志文件不存在: {log_file_path}")
            except Exception as e:
                print(f"读取日志文件失败: {str(e)}")
            
            return bgl_logs
        
        # 尝试加载Loki监控日志
        log_file_path = '/var/log/loki_monitor_log.json'
        if os.path.exists(log_file_path):
            return convert_loki_to_bgl(log_file_path)
        else:
            # 返回示例日志数据
            return [
                "2024-01-01 10:00:01 INFO [Service] Service started successfully",
                "2024-01-01 10:00:02 INFO [Service] Processing request 12345",
                "2024-01-01 10:00:03 ERROR [Service] Database connection failed",
                "2024-01-01 10:00:04 WARN [Service] Retrying connection...",
                "2024-01-01 10:00:05 INFO [Service] Connection restored",
                "2024-01-01 10:00:06 ERROR [Service] Memory usage exceeded threshold",
                "2024-01-01 10:00:07 INFO [Service] Memory cleanup completed",
                "2024-01-01 10:00:08 INFO [Service] Request 12345 completed"
            ]
    
    @staticmethod
    def _load_skywalking_data():
        """加载SkyWalking数据"""
        import json
        
        try:
            skywalking_file = '/home/denerate/rca_sky-main/results/active_nodes_test.json'
            if os.path.exists(skywalking_file):
                with open(skywalking_file, 'r', encoding='utf-8') as f:
                    skywalking_json_data = json.load(f)
                
                # 将JSON数据转换为SkyWalking数据格式
                return [
                    {
                        "query_time": skywalking_json_data.get("query_time", ""),
                        "active_nodes": skywalking_json_data.get("active_nodes", []),
                        "summary": skywalking_json_data.get("summary", {}),
                        "topology": skywalking_json_data.get("topology", {})
                    }
                ]
        except Exception as e:
            print(f"加载SkyWalking数据失败: {str(e)}")
        
        # 返回默认测试数据
        return [
            {
                "query_time": "2024-01-01T10:00:00.000Z",
                "active_nodes": [
                    {
                        "service_name": "web-service",
                        "is_active": True,
                        "instances": [{"language": "JAVA", "status": "healthy"}]
                    },
                    {
                        "service_name": "database-service",
                        "is_active": True,
                        "instances": [{"language": "JAVA", "status": "warning"}]
                    }
                ],
                "summary": {
                    "total_active_nodes": 2,
                    "total_topology_nodes": 3,
                    "total_connections": 5
                }
            }
        ]
    
    @staticmethod
    def _analyze_anomaly_information(anomaly_information, detection_type):
        """分析异常信息"""
        try:
            global_info = anomaly_information.get("global_info", {})
            anomaly_windows = anomaly_information.get("anomaly_windows", [])
            
            # 计算异常统计
            total_sequences = global_info.get("total_sequences", 0)
            anomaly_count = global_info.get("anomaly_count", 0)
            log_anomaly_count = global_info.get("log_anomaly_count", 0)
            metrics_anomaly_count = global_info.get("metrics_anomaly_count", 0)
            processing_time = global_info.get("processing_time", 0)
            
            # 分析异常窗口
            high_severity_anomalies = []
            medium_severity_anomalies = []
            low_severity_anomalies = []
            
            for window in anomaly_windows:
                anomaly_score = window.get("anomaly_score", 0)
                confidence = window.get("confidence", 0)
                timestamp = window.get("timestamp", "")
                
                anomaly_info = {
                    "sequence_id": window.get("sequence_id"),
                    "timestamp": timestamp,
                    "anomaly_score": anomaly_score,
                    "confidence": confidence,
                    "log_anomaly_score": window.get("log_anomaly_score", 0),
                    "metrics_anomaly_score": window.get("metrics_anomaly_score", 0),
                    "logs_count": len(window.get("logs", [])),
                    "metrics_data_keys": list(window.get("metrics_data", {}).keys())
                }
                
                # 根据异常分数分类
                if anomaly_score >= 7:
                    high_severity_anomalies.append(anomaly_info)
                elif anomaly_score >= 4:
                    medium_severity_anomalies.append(anomaly_info)
                else:
                    low_severity_anomalies.append(anomaly_info)
            
            # 计算整体风险等级
            if len(high_severity_anomalies) > 0:
                overall_risk_level = "高风险"
            elif len(medium_severity_anomalies) > 0:
                overall_risk_level = "中风险"
            elif len(low_severity_anomalies) > 0:
                overall_risk_level = "低风险"
            else:
                overall_risk_level = "正常"
            
            # 生成建议
            recommendations = []
            
            if high_severity_anomalies:
                recommendations.append("立即处理高风险异常，检查系统关键组件")
            
            if medium_severity_anomalies:
                recommendations.append("监控中风险异常，准备应对措施")
            
            if log_anomaly_count > 0:
                recommendations.append("检查日志异常，分析错误模式")
            
            if metrics_anomaly_count > 0:
                recommendations.append("检查指标异常，监控系统性能")
            
            if not recommendations:
                recommendations.append("系统运行正常，继续监控")
            
            # 生成摘要
            summary = f"检测{total_sequences}个序列，发现{anomaly_count}个异常(日志{log_anomaly_count}个，指标{metrics_anomaly_count}个). 处理时间:{processing_time:.2f}秒. 整体风险:{overall_risk_level}"
            
            return {
                "overall_risk_level": overall_risk_level,
                "detection_summary": summary,
                "statistics": {
                    "total_sequences": total_sequences,
                    "anomaly_count": anomaly_count,
                    "log_anomaly_count": log_anomaly_count,
                    "metrics_anomaly_count": metrics_anomaly_count,
                    "processing_time": processing_time,
                    "high_severity_count": len(high_severity_anomalies),
                    "medium_severity_count": len(medium_severity_anomalies),
                    "low_severity_count": len(low_severity_anomalies)
                },
                "anomaly_details": {
                    "high_severity": high_severity_anomalies,
                    "medium_severity": medium_severity_anomalies,
                    "low_severity": low_severity_anomalies
                },
                "recommendations": recommendations,
                "detection_type": detection_type
            }
            
        except Exception as e:
            return {
                "overall_risk_level": "分析失败",
                "detection_summary": f"异常信息分析失败: {str(e)}",
                "statistics": {},
                "anomaly_details": {},
                "recommendations": ["检查异常检测配置和数据处理"],
                "detection_type": detection_type
            }
