import json
import subprocess
import os

def analyze_config(data):
    suggestions = []
    conf = data['mysql']['runtime_variables']
    status = data['mysql']['global_status']
    # 1. 缓冲池大小检查
    buffer_pool_size = int(conf.get('innodb_buffer_pool_size', 0))
    total_memory = int(subprocess.getoutput("grep MemTotal /proc/meminfo | awk '{print $2}'")) * 1024
    recommended_buffer = total_memory * 0.7
    if buffer_pool_size < recommended_buffer * 0.8:
        suggestions.append({
            "issue": "InnoDB缓冲池过小",
            "severity": "high",
            "current": f"{buffer_pool_size//(1024*1024)}MB",
            "recommended": f"{int(recommended_buffer)//(1024*1024)}MB",
            "solution": "在my.cnf中增加innodb_buffer_pool_size"
        })
    # 2. 连接数检查
    max_conn = int(conf.get('max_connections', 0))
    threads_connected = int(status.get('Threads_connected', 0))
    if threads_connected > max_conn * 0.8:
        suggestions.append({
            "issue": "连接数接近上限",
            "severity": "critical",
            "current": f"{threads_connected}/{max_conn}",
            "recommended": f"增加至{int(max_conn*1.2)}",
            "solution": "增加max_connections设置"
        })
    # 3. 日志文件检查
    log_file_size = int(conf.get('innodb_log_file_size', 0))
    recommended_log_size = min(4096, total_memory * 0.25 // (1024*1024))
    if log_file_size < recommended_log_size * 0.5:
        suggestions.append({
            "issue": "InnoDB日志文件过小",
            "severity": "medium",
            "current": f"{log_file_size//(1024*1024)}MB",
            "recommended": f"{recommended_log_size}MB",
            "solution": "增加innodb_log_file_size并重启"
        })
    # 4. 查询缓存检查
    if conf.get('query_cache_type') == 'ON' and int(conf.get('query_cache_size', 0)) > 0:
        qc_hits = int(status.get('Qcache_hits', 0))
        qc_inserts = int(status.get('Qcache_inserts', 0))
        hit_ratio = qc_hits / (qc_hits + qc_inserts) if (qc_hits + qc_inserts) > 0 else 0
        if hit_ratio < 0.2:
            suggestions.append({
                "issue": "查询缓存效率低下",
                "severity": "low",
                "current": f"命中率: {hit_ratio:.1%}",
                "recommended": "禁用查询缓存",
                "solution": "设置query_cache_type=OFF"
            })
    return suggestions

if __name__ == "__main__":
    # 读取当前检测信息
    if os.path.exists("current_detection.json"):
        with open("current_detection.json") as f:
            detection_info = json.load(f)
            detection_number = detection_info["detection_number"]
            files = detection_info["files"]
    else:
        print("错误: 未找到当前检测信息，请先运行 mysql_optimizer.py")
        exit(1)
    
    print(f"分析第 {detection_number} 次检测的配置数据...")
    
    with open(files['optimization_report']) as f:
        data = json.load(f)
    suggestions = analyze_config(data)
    with open(files['suggestions'], "w") as f:
        json.dump(suggestions, f, indent=2, ensure_ascii=False)
    print(f"优化建议已生成: {files['suggestions']}") 