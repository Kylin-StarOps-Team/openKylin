import json
from jinja2 import Template
import datetime
import os

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MySQL配置优化报告</title>
    <style>
        .critical { background-color: #ffdddd; }
        .high { background-color: #ffeedd; }
        .medium { background-color: #ffffdd; }
        .low { background-color: #ddffdd; }
    </style>
</head>
<body>
    <h1>MySQL配置优化报告 #{{ detection_number }} - {{ timestamp }}</h1>
    <div class="summary">
        <h2>系统概览</h2>
        <ul>
            <li>文件句柄限制: {{ system.file_handles }}</li>
            <li>SWAP策略: {{ system.swappiness }}</li>
            <li>I/O调度: {{ system.io_scheduler }}</li>
        </ul>
    </div>
    <div class="issues">
        <h2>配置优化建议</h2>
        <table border="1">
            <tr>
                <th>问题</th>
                <th>严重性</th>
                <th>当前值</th>
                <th>建议值</th>
                <th>解决方案</th>
            </tr>
            {% for item in suggestions %}
            <tr class="{{ item.severity }}">
                <td>{{ item.issue }}</td>
                <td>{{ item.severity }}</td>
                <td>{{ item.current }}</td>
                <td>{{ item.recommended }}</td>
                <td><pre>{{ item.solution }}</pre></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <div class="percona-report">
        <h2>Percona分析摘要</h2>
        <pre>{{ analysis.summary }}</pre>
    </div>
</body>
</html>
'''

if __name__ == "__main__":
    # 读取当前检测信息
    if os.path.exists("current_detection.json"):
        with open("current_detection.json") as f:
            detection_info = json.load(f)
            detection_number = detection_info["detection_number"]
            files = detection_info["files"]
    else:
        print("错误: 未找到当前检测信息，请先运行 mysql_optimizer.py 和 analyze_config.py")
        exit(1)
    
    print(f"生成第 {detection_number} 次检测的HTML报告...")
    
    with open(files['optimization_report']) as f:
        data = json.load(f)
    with open(files['suggestions']) as f:
        suggestions = json.load(f)
    
    html = Template(HTML_TEMPLATE).render(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        detection_number=detection_number,
        system=data['system'],
        suggestions=suggestions,
        analysis=data['analysis']
    )
    with open(files['html_report'], "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML报告已生成: {files['html_report']}") 