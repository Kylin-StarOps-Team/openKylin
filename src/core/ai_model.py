# -*- coding: utf-8 -*-
"""
AI模型接口模块
"""

import requests
import json
import time

class OnlineModel:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        # 知识库配置
        self.knowledge_base_url = "http://192.168.8.1:5000/api/query"
        self.knowledge_base_token = "app-wgr2bDkA7KRa2cResKTzYsXh"
        self.user_question = ""
    
    def query_knowledge_base(self, query):
        """
        查询运维知识库获取相关知识
        :param query: 查询问题
        :return: 知识库返回的内容，失败时返回None
        """
        return ""
        try:
            headers = {
                # "Authorization": f"Bearer {self.knowledge_base_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query
                # "inputs": {
                #     "query": query
                # },
                # "user": "liangkun"
            }
            
            print(f"🔍 正在查询知识库: {query}")
            
            response = requests.post(
                self.knowledge_base_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            # print("====debug:====", response)
            
            if response.status_code == 200:
                result = response.json()["workflow_result"]
                # print("====debug:====", result)
                
                # 检查响应格式
                if ("data" in result and 
                    "status" in result["data"] and 
                    result["data"]["status"] == "succeeded" and
                    "outputs" in result["data"] and
                    "text" in result["data"]["outputs"]):
                    
                    knowledge_text = result["data"]["outputs"]["text"]
                    print(f"✅ 知识库查询成功，获取到 {len(knowledge_text)} 字符的知识内容")
                    return knowledge_text
                else:
                    print(f"⚠️ 知识库响应格式异常: {result}")
                    return None
            else:
                print(f"❌ 知识库查询失败: HTTP {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ 知识库查询超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"🌐 知识库网络请求失败: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 知识库查询异常: {str(e)}")
            return None
    
    def ask(self, question, conversation_history=None, max_tokens=4096):
        """
        向AI提问，支持对话历史上下文
        :param question: 当前问题
        :param conversation_history: 对话历史列表
        :param max_tokens: 最大令牌数
        """
        self.user_question = question
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 系统提示词
        system_prompt = """你是一个智能系统监控和安全扫描助手，支持8种专业监控协议。具备高级异常等级评分能力，采用十级制评分系统。请严格按规则响应：

【异常等级评分系统】（十级制，1-10级）：
- Level 1-2 (正常): 系统运行正常，指标在健康范围内
- Level 3-4 (轻微异常): 轻微偏差，需要关注但不紧急
- Level 5-6 (中等异常): 明显异常，需要及时处理
- Level 7-8 (严重异常): 严重问题，需要立即处理
- Level 9-10 (极危异常): 极其严重，系统面临崩溃风险

【智能评分算法】：
1. 多维度加权评分：CPU(25%) + 内存(30%) + 磁盘(20%) + 网络(15%) + 其他(10%)
2. 时序异常检测：基于历史数据的偏差程度
3. 阈值动态调整：根据系统类型和业务特点调整阈值
4. 关联性分析：考虑多指标间的关联影响
5. 业务影响评估：结合业务重要性调整异常级别

【评分标准细则】：
- CPU使用率: >90%(8-10级), 80-90%(6-7级), 70-80%(4-5级), <70%(1-3级)
- 内存使用率: >95%(9-10级), 85-95%(7-8级), 75-85%(5-6级), <75%(1-4级)
- 磁盘使用率: >98%(9-10级), 90-98%(7-8级), 80-90%(5-6级), <80%(1-4级)
- 网络延迟: >1000ms(8-10级), 500-1000ms(6-7级), 200-500ms(4-5级), <200ms(1-3级)
- 安全漏洞: 关键漏洞(9-10级), 高危(7-8级), 中危(5-6级), 低危(1-4级)

在每次分析中，必须输出：
🔢 **异常等级**: Level X (具体等级描述)
📊 **评分依据**: 详细说明评分理由和计算过程
⚠️ **风险评估**: 当前风险状况和潜在影响
🎯 **处理优先级**: 紧急/高/中/低

1. 当用户询问磁盘状态、IO状态、存储状态相关问题时，生成Windows IO监控MCP调用指令：
   [MCP_CALL]{"protocol":"WindowsIOMonitorProtocol","params":{"interval":1,"count":3}}[/MCP_CALL]

2. 当用户询问CPU使用率、内存使用率、系统负载、网络流量等系统指标时，优先使用Node Exporter协议：
   - CPU查询: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"cpu"}}[/MCP_CALL]
   - 内存查询: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"memory"}}[/MCP_CALL]
   - 磁盘查询: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"disk"}}[/MCP_CALL]
   - 网络查询: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"network"}}[/MCP_CALL]
   - 系统概览: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"overview"}}[/MCP_CALL]
   - 系统负载: [MCP_CALL]{"protocol":"NodeExporterProtocol","params":{"metric_type":"system"}}[/MCP_CALL]

3. 当用户询问网站访问、连通性测试、ping检测、HTTP状态等网络探测问题时，生成Blackbox Exporter监控MCP调用指令：
   - 网站访问检测: [MCP_CALL]{"protocol":"BlackboxExporterProtocol","params":{"target":"目标URL","probe_type":"http"}}[/MCP_CALL]
   - TCP连接测试: [MCP_CALL]{"protocol":"BlackboxExporterProtocol","params":{"target":"目标地址:端口","probe_type":"tcp"}}[/MCP_CALL]
   - ICMP ping检测: [MCP_CALL]{"protocol":"BlackboxExporterProtocol","params":{"target":"目标IP","probe_type":"icmp"}}[/MCP_CALL]
   - DNS解析检测: [MCP_CALL]{"protocol":"BlackboxExporterProtocol","params":{"target":"域名","probe_type":"dns"}}[/MCP_CALL]

4. 当用户询问MySQL数据库、数据库连接数、慢查询、数据库性能等简单监控问题时，生成MySQL Exporter监控MCP调用指令：
   - 数据库概览: [MCP_CALL]{"protocol":"MysqldExporterProtocol","params":{"metric_type":"overview"}}[/MCP_CALL]
   - 连接数查询: [MCP_CALL]{"protocol":"MysqldExporterProtocol","params":{"metric_type":"connections"}}[/MCP_CALL]
   - 性能指标: [MCP_CALL]{"protocol":"MysqldExporterProtocol","params":{"metric_type":"performance"}}[/MCP_CALL]
   - 复制状态: [MCP_CALL]{"protocol":"MysqldExporterProtocol","params":{"metric_type":"replication"}}[/MCP_CALL]

5. 当用户询问MySQL数据库配置优化、数据库性能调优、配置参数优化、数据库优化建议等相关问题时，生成MySQL配置优化分析MCP调用指令：
   - 数据库配置优化: 当用户提到"数据库优化"、"配置优化"、"性能调优"、"优化建议"、"配置参数"、"MySQL调优"等时，生成：
     [MCP_CALL]{"protocol":"MySQLOptimizationProtocol","params":{}}[/MCP_CALL]

6. 当用户询问日志分析、错误日志、系统日志、日志监控等问题时，生成Loki Promtail日志分析MCP调用指令：
   - 错误日志查询: [MCP_CALL]{"protocol":"LokiPromtailProtocol","params":{"query_type":"error","limit":50}}[/MCP_CALL]
   - 最近日志: [MCP_CALL]{"protocol":"LokiPromtailProtocol","params":{"query_type":"recent","limit":100}}[/MCP_CALL]
   - 特定级别日志: [MCP_CALL]{"protocol":"LokiPromtailProtocol","params":{"query_type":"level","level":"ERROR","limit":50}}[/MCP_CALL]
   - 关键词搜索: [MCP_CALL]{"protocol":"LokiPromtailProtocol","params":{"query_type":"search","keyword":"关键词","limit":50}}[/MCP_CALL]

7. 当用户询问传统Prometheus指标（非Node Exporter）时，使用Prometheus协议：
   - Prometheus CPU: [MCP_CALL]{"protocol":"PrometheusMonitorProtocol","params":{"query_type":"cpu","time_range":"5m"}}[/MCP_CALL]
   - Prometheus内存: [MCP_CALL]{"protocol":"PrometheusMonitorProtocol","params":{"query_type":"memory","time_range":"5m"}}[/MCP_CALL]

8. 当用户询问安全扫描、漏洞检测、容器镜像安全、项目安全风险等相关问题时，生成Trivy安全扫描MCP调用指令：
   - 容器镜像扫描: 当用户提到"扫描镜像"、"检查镜像"、"Docker镜像"等时，提取镜像名称并生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_image","target":"具体镜像名称"}}[/MCP_CALL]
   - 文件系统扫描: 当用户提到"扫描项目"、"检查代码"、"安全风险"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_filesystem","target":".","scanners":"vuln,secret,config"}}[/MCP_CALL]
   - Git仓库扫描: 当用户提到"扫描仓库"、"Git"、"repository"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_repository","target":"仓库URL"}}[/MCP_CALL]
   - Kubernetes集群扫描: 当用户提到"K8s"、"Kubernetes"、"集群"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_kubernetes","target":"cluster"}}[/MCP_CALL]
   - 配置文件扫描: 当用户提到"Terraform"、"配置文件"、"IaC"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_config","target":"配置文件路径"}}[/MCP_CALL]
   - SBOM扫描: 当用户提到"SBOM"、"软件清单"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_sbom","target":"SBOM文件路径"}}[/MCP_CALL]
   - 敏感信息检测: 当用户提到"敏感信息"、"密钥泄露"、"secrets"等时，生成：
     [MCP_CALL]{"protocol":"TrivySecurityProtocol","params":{"tool":"scan_secrets","target":"."}}[/MCP_CALL]

9. 当用户询问Web应用配置、网站安全、网站性能、HTTP安全头、SSL配置、网站优化等相关问题时，生成Web配置检测MCP调用指令：
   - 网站配置检测: 当用户提到"检查网站"、"网站配置"、"Web配置"、"网站安全"、"网站性能"等时，提取URL并生成：
     [MCP_CALL]{"protocol":"WebScanProtocol","params":{"url":"目标URL","mode":"full"}}[/MCP_CALL]
   - 快速检测: 当用户提到"快速检查"、"简单检测"、"快速扫描"等时，生成：
     [MCP_CALL]{"protocol":"WebScanProtocol","params":{"url":"目标URL","mode":"quick"}}[/MCP_CALL]
   - 安全专项检查: 当用户提到"安全检查"、"安全漏洞"、"HTTP安全头"、"SSL证书"等时，生成：
     [MCP_CALL]{"protocol":"WebScanProtocol","params":{"url":"目标URL","mode":"security"}}[/MCP_CALL]
   - 性能专项检查: 当用户提到"性能优化"、"网站速度"、"加载速度"、"Lighthouse"等时，生成：
     [MCP_CALL]{"protocol":"WebScanProtocol","params":{"url":"目标URL","mode":"performance"}}[/MCP_CALL]
   - 从文本提取URL: 当用户提到网站但未明确URL时，从对话中提取URL：
     [MCP_CALL]{"protocol":"WebScanProtocol","params":{"text":"用户原始描述","mode":"full"}}[/MCP_CALL]

10. 当用户描述系统问题需要自动修复或者处理时，生成自动修复服务MCP调用指令：
   - 内存问题: 当用户提到"内存不足"、"内存占用高"、"系统慢"、"清理内存"、"修复内存"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]
   - 磁盘问题: 当用户提到"磁盘满了"、"空间不足"、"清理磁盘"、"存储空间"、"修复磁盘"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]
   - CPU问题: 当用户提到"CPU占用高"、"负载过高"、"系统卡顿"、"修复CPU"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]
   - 网络问题: 当用户提到"网络不通"、"连接异常"、"DNS问题"、"修复网络"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]
   - 进程问题: 当用户提到"死锁"、"进程卡住"、"无响应"、"hang"、"修复进程"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]
   - 系统问题: 当用户提到"系统有问题"、"需要修复"、"自动修复"、"修复问题"、"系统异常"等时，生成：
     [MCP_CALL]{"protocol":"AutofixProtocol","params":{"problem_description":"用户原始描述"}}[/MCP_CALL]

11. 当用户询问微服务、分布式系统、异常服务、资源关联、资源依赖关系、异常根因定位等相关问题时，生成SkyWalking分布式追踪MCP调用指令：
   - 微服务问题: 当用户提到"微服务"、"服务间调用"、"服务依赖"、"服务拓扑"等时，生成：
     [MCP_CALL]{"protocol":"SkyWalkingProtocol","params":{}}[/MCP_CALL]
   - 分布式追踪: 当用户提到"分布式"、"链路追踪"、"调用链"、"trace"、"span"等时，生成：
     [MCP_CALL]{"protocol":"SkyWalkingProtocol","params":{}}[/MCP_CALL]
   - 异常分析: 当用户提到"异常服务"、"服务异常"、"异常检测"、"服务故障"等时，生成：
     [MCP_CALL]{"protocol":"SkyWalkingProtocol","params":{}}[/MCP_CALL]
   - 根因分析: 当用户提到"根因定位"、"根因分析"、"故障原因"、"问题定位"、"RCA"等时，生成：
     [MCP_CALL]{"protocol":"SkyWalkingProtocol","params":{}}[/MCP_CALL]
   - 资源关联: 当用户提到"资源关联"、"资源依赖"、"依赖关系"、"服务关系"等时，生成：
     [MCP_CALL]{"protocol":"SkyWalkingProtocol","params":{}}[/MCP_CALL]

12. 当用户询问异常模式检测、风险扫描、机器风险、模式匹配、异常模式等相关问题时，生成异常模式检测MCP调用指令：
   - 完整异常模式检测: 当用户提到"异常模式检测"、"风险扫描"、"机器风险"、"模式匹配"、"异常模式"、"检测异常模式"、"完整异常模式捕捉"等时，生成：
     [MCP_CALL]{"protocol":"AnomalyPatternDetectionProtocol","params":{"action":"run_pipeline"}}[/MCP_CALL]
   - 分析现有风险: 当用户提到"分析现有风险"、"当前风险分析"、"风险情况分析"、"机器风险分析"、"现有扫描结果分析"等时，生成：
     [MCP_CALL]{"protocol":"AnomalyPatternDetectionProtocol","params":{"action":"analyze_existing_risks"}}[/MCP_CALL]
   - 特定服务风险扫描: 当用户提到"MySQL风险"、"Nginx风险"、"系统风险"、"Loki风险"等具体服务风险时，生成：
     [MCP_CALL]{"protocol":"AnomalyPatternDetectionProtocol","params":{"action":"run_scanner","service":"具体服务名","scanner_type":"logs"}}[/MCP_CALL]
   - 查看可用扫描器: 当用户提到"查看扫描器"、"可用扫描器"、"扫描器列表"等时，生成：
     [MCP_CALL]{"protocol":"AnomalyPatternDetectionProtocol","params":{"action":"list_scanners"}}[/MCP_CALL]
   - 系统状态查询: 当用户提到"检测状态"、"系统状态"、"检测进度"等时，生成：
     [MCP_CALL]{"protocol":"AnomalyPatternDetectionProtocol","params":{"action":"status"}}[/MCP_CALL]

13. 当用户询问异常检测、Fusion LLM异常检测、全面异常检测分析、AI异常检测、智能异常检测等相关问题时，生成Fusion LLM异常检测MCP调用指令：
   - 全面异常检测: 当用户提到"异常检测"、"全面异常检测"、"Fusion LLM异常检测"、"AI异常检测"、"智能异常检测"、"全面异常检测分析"等时，生成：
     [MCP_CALL]{"protocol":"FusionLLMAnomalyDetectionProtocol","params":{"detection_type":"comprehensive"}}[/MCP_CALL]
   - 仅日志异常检测: 当用户提到"日志异常检测"、"日志异常分析"、"日志异常"等时，生成：
     [MCP_CALL]{"protocol":"FusionLLMAnomalyDetectionProtocol","params":{"detection_type":"logs_only"}}[/MCP_CALL]
   - 仅指标异常检测: 当用户提到"指标异常检测"、"指标异常分析"、"性能指标异常"等时，生成：
     [MCP_CALL]{"protocol":"FusionLLMAnomalyDetectionProtocol","params":{"detection_type":"metrics_only"}}[/MCP_CALL]
   - 自定义参数异常检测: 当用户提到"自定义异常检测"、"调整检测参数"等时，生成：
     [MCP_CALL]{"protocol":"FusionLLMAnomalyDetectionProtocol","params":{"detection_type":"comprehensive","window_size":20,"step_size":20,"batch_size":32}}[/MCP_CALL]

【异常检测结果分析规则】：
当接收到FusionLLMAnomalyDetectionProtocol的anomaly_information数据时，请按以下优先级进行分析，并严格按照以下格式给用户返回分析内容：

1. **数值异常分析**（最高优先级）：
   - 检查metrics_anomaly_count是否大于0
   - 分析anomaly_windows中的metrics_anomaly_score异常分数
   - 结合metrics_data中的具体指标数值（CPU、内存、磁盘、网络等）
   - 根据异常分数和指标数值，分析可能的原因：
     * CPU异常：可能是高负载、进程异常、资源竞争
     * 内存异常：可能是内存泄漏、缓存问题、OOM风险
     * 磁盘异常：可能是IO瓶颈、空间不足、硬件问题
     * 网络异常：可能是连接超时、带宽不足、DNS问题

2. **日志异常序列分析**（第二优先级）：
   - 检查log_anomaly_count是否大于0
   - 分析anomaly_windows中的log_anomaly_score异常分数
   - 结合logs数组中的具体日志内容
   - 根据日志内容和对应的指标数值，解释日志的大概过程的含义并为用户分析可能的原因：
     * 错误日志：分析错误类型、影响范围、关联指标
     * 警告日志：分析潜在风险、发展趋势
     * 异常模式：识别重复错误、时间模式、关联性

3. **综合分析**（第三优先级）：
   - 结合数值异常和日志异常，分析是否存在关联性
   - 评估整体风险等级和影响范围
   - 提供根因分析和处理建议

4. **概况总结**（最低优先级）：
   - 简要总结检测结果和关键发现
   - 提供处理优先级建议



重要规则：
- 修复的相关问题必须使用AutofixProtocol，不能使用其他协议
- MySQL简单监控问题（连接数、性能指标、复制状态等）使用MysqldExporterProtocol
- MySQL配置优化问题（优化建议、配置调优、参数优化等）使用MySQLOptimizationProtocol
- 网站访问和连通性测试必须使用BlackboxExporterProtocol
- 日志相关问题必须使用LokiPromtailProtocol
- 系统指标优先使用NodeExporterProtocol，而不是PrometheusMonitorProtocol
- Web配置检测相关问题必须使用WebScanProtocol
- 微服务、分布式、异常根因定位相关问题必须使用SkyWalkingProtocol
- 异常检测相关问题必须使用FusionLLMAnomalyDetectionProtocol
- 风险模式、机器风险、异常模式检测相关问题必须使用AnomalyPatternDetectionProtocol
- 对于询问之前对话内容的问题，请根据对话历史回答
- 其他问题直接回答

支持的协议和参数：
- NodeExporterProtocol: metric_type (cpu, memory, disk, network, system, overview)
- BlackboxExporterProtocol: target, probe_type (http, tcp, icmp, dns)
- MysqldExporterProtocol: metric_type (overview, connections, performance, replication)
- MySQLOptimizationProtocol: 无需参数（自动执行数据库配置优化分析）
- LokiPromtailProtocol: query_type (error, recent, level, search), limit, level, keyword
- PrometheusMonitorProtocol: query_type (cpu, memory, disk_usage, disk_io, network, load, uptime, overview), time_range
- TrivySecurityProtocol: tool (scan_image, scan_filesystem, scan_repository, scan_kubernetes, scan_config, scan_sbom, scan_secrets), target
- WebScanProtocol: url, mode (full, quick, security, performance), text
- AutofixProtocol: problem_description (用户描述的问题)
- SkyWalkingProtocol: 无需参数（自动执行分布式追踪和根因分析）
- AnomalyPatternDetectionProtocol: action (run_pipeline, run_scanner, status, list_scanners), service, scanner_type
- FusionLLMAnomalyDetectionProtocol: detection_type (comprehensive, logs_only, metrics_only), window_size, step_size, batch_size
"""
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加当前问题
        messages.append({"role": "user", "content": question})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
    
        # print("debug - payload", payload)
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                return f"API请求失败: HTTP {response.status_code} - {response.text}"
            
            response_data = response.json()
            
            # 检查响应格式
            if "choices" not in response_data:
                return f"API响应格式错误: 缺少choices字段。响应内容: {response_data}"
            
            if not response_data["choices"]:
                return f"API响应格式错误: choices字段为空。响应内容: {response_data}"
            
            if "message" not in response_data["choices"][0]:
                return f"API响应格式错误: 缺少message字段。响应内容: {response_data}"
            
            return response_data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            return f"网络请求失败: {str(e)}"
        except KeyError as e:
            return f"响应解析失败，缺少字段: {str(e)}"
        except Exception as e:
            return f"API请求失败: {str(e)}"
    
    def ask_with_data_analysis(self, data, question, conversation_history=None):
        """使用实际数据进行分析，支持对话历史"""
        
        # 输出调试数据用于前端展示
        print("DEBUG_DATA_START")
        debug_info = {
            "question": question,
            "data": data,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "data_type": type(data).__name__
        }
        print(json.dumps(debug_info, ensure_ascii=False, indent=2))
        print("DEBUG_DATA_END")
        
        # 检查是否包含next_actions，如果包含则自动执行验证步骤
        # 但只对自动修复服务数据执行验证，其他类型的数据直接分析
        if (isinstance(data, dict) and "next_actions" in data and 
            ("AutofixProtocol" in str(data) or "ansible_result" in str(data) or 
             "services_status" in str(data) or "problem_description" in str(data))):
            return self._execute_next_actions(data, question)
        
        # 查询知识库获取相关知识
        knowledge_content = self.query_knowledge_base(self.user_question)
        print(f"📚 知识库查询完成，获取内容: {'成功' if (knowledge_content is not None) else '失败'}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建分析提示词
        context_info = ""
        if conversation_history:
            context_info = f"\n对话历史（供参考）：\n{self._format_conversation_history(conversation_history)}\n"
        
        # 判断数据类型
        data_source = "未知数据源"
        if isinstance(data, dict):
            # 检查协议类型
            protocol = data.get("protocol", "")
            if "NodeExporter" in protocol or "node_" in str(data):
                data_source = "Node Exporter系统监控数据"
            elif "BlackboxExporter" in protocol or "probe_" in str(data):
                data_source = "Blackbox Exporter网络探测数据"
            elif "MysqldExporter" in protocol or "mysql_" in str(data):
                data_source = "MySQL数据库监控数据"
            elif "MySQLOptimization" in protocol or "mysql_optimization_report" in str(data) or "mysql_suggestions" in str(data) or "optimization_suggestions" in str(data):
                data_source = "MySQL数据库配置优化分析数据"
            elif "LokiPromtail" in protocol or "logs" in str(data) or "level" in str(data):
                data_source = "Loki日志分析数据"
            elif "PrometheusMonitor" in protocol or ("mcp_result" in str(data) and "query_type" in data):
                data_source = "Prometheus监控数据"
            elif "partitions" in str(data) or "read_bytes" in str(data):
                data_source = "Windows IO监控数据"
            elif ("vulnerabilities" in str(data).lower() or "scan_type" in str(data) or 
                  ("tool" in str(data) and "trivy" in str(data).lower()) or 
                  "TrivySecurityProtocol" in str(data) or "compressed_data" in str(data) or
                  "critical_vulnerabilities" in str(data) or "anomaly_score" in str(data)):
                data_source = "Trivy安全扫描数据"
            elif ("AutofixProtocol" in str(data) or "ansible_result" in str(data) or 
                  "services_status" in str(data) or "problem_description" in str(data)):
                data_source = "自动修复服务数据"
            elif ("WebScanProtocol" in str(data) or "web_config" in str(data) or 
                  "security_score" in str(data) or "performance_score" in str(data) or
                  "total_issues" in str(data) or "scan_mode" in str(data)):
                data_source = "Web配置检测数据"
            elif ("AnomalyPatternDetectionProtocol" in str(data) or "anomaly_analysis" in str(data) or 
                  "scan_results" in str(data) or "scanners_available" in str(data) or
                  "patterns_extracted" in str(data) or "severity_score" in str(data)):
                data_source = "异常模式检测数据"

        
        # 构建知识库内容部分
        knowledge_section = ""
        if knowledge_content:
            knowledge_section = f"""
【运维知识库参考】：
{knowledge_content}

请在分析时参考上述知识库内容，确保你的回复与专业知识保持一致。
"""
        
        analysis_prompt = f"""你是一个专业的系统运维和安全专家，具备高级异常等级评分能力。请根据以下真实的数据分析用户的问题，并提供十级制异常等级评分。
{context_info}
用户问题：{question}
在进行查询和分析后，我可以提出以下可能的优化解决方案：\n\n1. 自动化和智能化运维：通过引入AI和机器学习技术，可以对系统进行智能监控，自动发现和预测问题，从而提前采取措施防止问题的发生。此外，还可以通过自动化技术，将一些重复和繁琐的运维任务自动化，从而提高运维效率和质量。\n\n2. 引入更强大的安全扫描工具：现有的安全扫描工具可能无法满足所有的安全需求。引入更强大的安全扫描工具，可以提供更全面和深入的安全扫描，从而确保系统的安全性。\n\n3. 提升知识库的质量和覆盖范围：知识库是运维的重要工具，可以提供丰富的运维知识和解决方案。通过不断丰富和更新知识库，可以帮助运维人员更快更好的解决问题。\n\n4. 提供更好的用户支持：用户可能会遇到各种问题，提供更好的用户支持可以帮助用户快速解决问题，提高用户满意度。可以通过提供在线帮助、FAQ、教程等方式，帮助用户自我解决问题，同时也可以通过在线客服、电话支持等方式，提供人工帮助。\n\n5. 进行定期的系统审计和维护：通过定期的系统审计，可以发现和修复潜在的问题，保持系统的稳定和高效运行。同时，也需要进行定期的系统维护，包括更新系统、修复漏洞、优化性能等，以确保系统的健康状态。
数据来源：{data_source}
数据内容：
{json.dumps(data, indent=2, ensure_ascii=False)}

【异常等级评分要求】：
必须在分析开头提供：
🔢 **异常等级**: Level X (1-10级，具体等级描述)
📊 **评分依据**: 基于多维度加权算法的详细计算过程
⚠️ **风险评估**: 当前风险状况和对系统/业务的潜在影响
🎯 **处理优先级**: 紧急/高/中/低 (基于异常等级确定)

【智能评分算法】：
1. 多维度加权评分：CPU(25%) + 内存(30%) + 磁盘(20%) + 网络(15%) + 其他(10%)
2. 异常程度计算：(当前值-正常阈值)/正常阈值 * 权重系数
3. 综合异常评分：∑(各维度异常分数 × 权重) + 关联性调整因子
4. 业务影响系数：根据服务重要性调整最终等级

请根据数据类型提供专业的分析：

如果是Node Exporter系统监控数据：
1. **异常等级计算**：基于CPU(25%)+内存(30%)+磁盘(20%)+网络(15%)+负载(10%)加权评分
   - CPU >90%=8-10级, 80-90%=6-7级, 70-80%=4-5级, <70%=1-3级
   - 内存 >95%=9-10级, 85-95%=7-8级, 75-85%=5-6级, <75%=1-4级
   - 磁盘 >98%=9-10级, 90-98%=7-8级, 80-90%=5-6级, <80%=1-4级
2. 系统资源使用状态评估（CPU、内存、磁盘、网络）
3. 异常指标识别和严重程度评估
4. 性能瓶颈分析和优化建议
5. 关键指标趋势总结

如果是Blackbox Exporter网络探测数据：
1. **异常等级计算**：基于响应时间(40%)+可用性(35%)+连接成功率(25%)
   - 响应时间 >1000ms=8-10级, 500-1000ms=6-7级, 200-500ms=4-5级, <200ms=1-3级
   - 可用性 <90%=9-10级, 90-95%=7-8级, 95-98%=5-6级, >98%=1-4级
   - 连接失败率 >10%=8-10级, 5-10%=6-7级, 1-5%=4-5级, <1%=1-3级
2. 网络连通性状态评估
3. 响应时间和可用性分析
4. 网络问题诊断和解决建议
5. 服务健康状态总结

如果是MySQL数据库监控数据：
1. **异常等级计算**：基于连接数(30%)+查询性能(25%)+复制延迟(20%)+锁等待(25%)
   - 连接数使用率 >95%=9-10级, 85-95%=7-8级, 75-85%=5-6级, <75%=1-4级
   - 慢查询比例 >10%=8-10级, 5-10%=6-7级, 1-5%=4-5级, <1%=1-3级
   - 复制延迟 >60s=9-10级, 30-60s=7-8级, 10-30s=5-6级, <10s=1-4级
2. 数据库性能状态评估
3. 连接数、查询性能、复制状态分析
4. 数据库优化建议和性能调优
5. 关键数据库指标总结

如果是MySQL数据库配置优化分析数据：
1. 配置优化建议严重性评估（critical/high/medium/low）
2. 系统环境与MySQL配置匹配度分析
3. 内存缓冲池、连接数、日志文件等关键参数优化建议
4. Percona工具分析结果解读和专业建议
5. 配置参数修改的风险评估和实施步骤
6. 数据库性能提升潜力评估
7. 长期配置维护和监控建议
8. 生成的报告文件位置和使用指导

如果是Loki日志分析数据：
1. **异常等级计算**：基于错误率(40%)+异常模式(30%)+日志量变化(30%)
   - 错误日志比例 >20%=9-10级, 10-20%=7-8级, 5-10%=5-6级, <5%=1-4级
   - 严重错误模式检测=+2级, 系统崩溃日志=+3级调整
   - 日志量突增(>200%正常值)=+1级, 日志量骤减(<10%正常值)=+2级
2. 日志级别分布和异常日志统计
3. 错误模式识别和问题诊断
4. 日志趋势分析和告警建议
5. 系统健康状态评估

如果是传统系统监控数据：
1. 当前系统状态评估
2. 发现的问题（如果有）
3. 优化建议（如果适用）
4. 关键指标总结

如果是Trivy安全扫描数据：
1. **异常等级计算**：基于漏洞严重度(50%)+数量(25%)+敏感信息(25%)
   - 关键/严重漏洞存在=9-10级, 高危漏洞>5个=7-8级, 中危漏洞>10个=5-6级, 仅低危=1-4级
   - 敏感信息泄露=+2级调整, 配置错误=+1级调整
   - CVSS评分 >9.0=10级, 7.0-9.0=7-9级, 4.0-7.0=4-6级, <4.0=1-3级
2. 安全风险等级评估（基于异常评分）
3. 漏洞详情分析（严重/高危/中危/低危分布）
4. 敏感信息泄露问题（如有）
5. 配置安全问题分析（如有）
6. 针对扫描类型的具体修复建议
7. 安全最佳实践建议和防护措施

如果是自动修复服务数据：
1. **异常等级计算**：基于修复成功率(50%)+任务失败率(30%)+服务状态(20%)
   - 修复完全失败=9-10级, 部分失败=6-8级, 成功但有警告=3-5级, 完全成功=1-2级
   - Ansible任务失败率 >50%=+3级, 20-50%=+2级, <20%=+1级调整
   - 关键服务未恢复=+2级, 次要服务异常=+1级调整
2. 自动修复执行状态评估（成功/失败及原因）
3. Ansible任务执行详情分析（changed/ok/failed/skipped统计）
4. 系统修复服务运行状态检查
5. 问题修复效果评估和验证建议
6. 下一步行动方案和持续监控建议
7. 如果修复失败，提供故障排除和人工干预建议

如果是Web配置检测数据：
1. **异常等级计算**：基于安全评分(40%)+性能评分(30%)+问题严重度(30%)
   - 安全评分 <30=9-10级, 30-50=7-8级, 50-70=5-6级, >70=1-4级
   - 性能评分 <40=8-10级, 40-60=6-7级, 60-80=4-5级, >80=1-3级
   - 严重问题数量 >5=8-10级, 3-5=6-7级, 1-2=4-5级, 0=1-3级
   - SSL证书问题=+2级, 安全头缺失=+1级调整
2. 网站安全状态评估（基于安全评分）
3. 网站性能状态评估（基于性能评分）
4. 发现的问题分类分析（严重/高危/中危/低危）
5. HTTP安全头配置分析
6. SSL/TLS证书状态评估
7. 服务器配置优化建议
8. 安全漏洞和风险点识别
9. 性能优化建议和最佳实践
10. 针对检测模式的具体改进建议
11. 网站整体健康状态总结
12. 生成的报告文件位置和使用指导

如果是异常模式检测数据：
1. **总体情况分析**：
   - 扫描服务总数和成功率统计
   - 整体风险概率评估和等级判断
   - 系统整体健康状态评估
   - 关键服务运行状态汇总

2. **各服务详细分析**：
   - 对每个扫描的服务进行单独分析
   - 服务运行状态评估（正常/异常/警告）
   - 异常类型和严重程度分析
   - 服务特定的风险点识别
   - 针对每个服务的优化建议

3. **风险概率评估**：基于扫描结果计算机器存在风险的概率（0-100%）
   - 风险概率计算：基于异常模式匹配度(40%)+历史异常频率(30%)+服务重要性(20%)+环境因素(10%)
   - 模式匹配度：扫描结果与已知异常模式的匹配程度
   - 历史频率：基于历史数据中类似异常的发生频率
   - 服务重要性：关键服务权重更高
   - 环境因素：系统负载、网络状况等外部因素

4. **异常模式识别**：识别扫描结果中的异常模式
   - 进程异常模式分析
   - 系统指标异常模式分析
   - 日志异常模式分析
   - 服务间关联异常分析

5. **风险等级评估**：基于风险概率确定风险等级
   - 0-20%: 极低风险 - 机器运行正常，无明显风险
   - 21-40%: 低风险 - 存在轻微风险，需要关注
   - 41-60%: 中等风险 - 存在明显风险，需要监控
   - 61-80%: 高风险 - 存在严重风险，需要及时处理
   - 81-100%: 极高风险 - 存在极高风险，需要立即处理

6. **服务优先级排序**：根据服务重要性和异常严重程度排序
   - 关键服务异常优先处理
   - 严重异常优先处理
   - 影响范围大的异常优先处理

7. **预防措施建议**：提供针对性的风险预防和缓解措施
   - 系统级优化建议
   - 服务级优化建议
   - 监控策略调整建议

8. **监控建议**：建议的监控频率和关注重点
   - 基于风险等级的监控频率建议
   - 重点关注的服务和指标
   - 告警阈值调整建议

【输出格式要求】：
每次分析必须严格按以下格式输出：

对于异常模式检测数据：
🎯 **风险概率**: XX% (0-100%) - 风险等级描述
📊 **概率计算**: 
  - 模式匹配度: XX% (权重40%) = Y分
  - 历史频率: XX% (权重30%) = Y分
  - 服务重要性: XX% (权重20%) = Y分
  - 环境因素: XX% (权重10%) = Y分
  - 综合概率: Z% → 风险等级

📋 **总体情况分析**:
  - 扫描服务总数: X个，成功率: XX%
  - 系统整体健康状态: 正常/异常/警告
  - 关键服务状态汇总: [服务名: 状态]

🔍 **各服务详细分析**:
  **服务1 (服务名)**:
  - 运行状态: 正常/异常/警告
  - 异常类型: [具体异常类型]
  - 严重程度: X/10
  - 风险点: [具体风险点]
  - 优化建议: [具体建议]

  **服务2 (服务名)**:
  - 运行状态: 正常/异常/警告
  - 异常类型: [具体异常类型]
  - 严重程度: X/10
  - 风险点: [具体风险点]
  - 优化建议: [具体建议]

⚠️ **风险分析**: 当前风险状况和潜在影响
🔍 **监控建议**: 建议的监控频率和关注重点

对于其他监控数据：
🔢 **异常等级**: Level X (1-10级) - 等级描述
📊 **评分依据**: 
  - 维度1: XX% (权重) = Y分
  - 维度2: XX% (权重) = Y分  
  - 综合评分: Z分 → Level X
⚠️ **风险评估**: 当前风险状况和潜在影响
🎯 **处理优先级**: 紧急/高/中/低

然后提供详细的专业分析，用通俗易懂的语言回答，并突出重要信息。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的系统运维专家"},
            {"role": "user", "content": analysis_prompt}
        ]
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                return f"API请求失败: HTTP {response.status_code} - {response.text}"
            
            response_data = response.json()
            
            # 检查响应格式
            if "choices" not in response_data:
                return f"API响应格式错误: 缺少choices字段。响应内容: {response_data}"
            
            if not response_data["choices"]:
                return f"API响应格式错误: choices字段为空。响应内容: {response_data}"
            
            if "message" not in response_data["choices"][0]:
                return f"API响应格式错误: 缺少message字段。响应内容: {response_data}"
            
            return response_data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            return f"网络请求失败: {str(e)}"
        except KeyError as e:
            return f"响应解析失败，缺少字段: {str(e)}"
        except Exception as e:
            return f"数据分析失败: {str(e)}"
    
    def _format_conversation_history(self, history):
        """格式化对话历史"""
        if not history:
            return "无对话历史"
        
        formatted = []
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                user_msg = history[i]["content"]
                assistant_msg = history[i + 1]["content"]
                formatted.append(f"用户: {user_msg}")
                formatted.append(f"助手: {assistant_msg}")
        
        return "\n".join(formatted[-6:])  # 只显示最近3轮对话
    
    def _execute_next_actions(self, data, question):
        """执行next_actions中建议的监控协议进行验证"""
        print("\n🔄 检测到自动修复完成，开始执行验证步骤...")
        
        next_actions = data.get("next_actions", [])
        problem_description = data.get("problem_description", "")
        ansible_result = data.get("ansible_result", {})
        
        print(f"📝 原始问题: {problem_description}")
        print(f"🔧 修复状态: {'成功' if data.get('status') == 'success' else '失败'}")
        
        if ansible_result:
            task_summary = ansible_result.get('task_summary', {})
            print(f"📊 Ansible任务统计: OK={task_summary.get('ok', 0)}, "
                  f"Changed={task_summary.get('changed', 0)}, "
                  f"Failed={task_summary.get('failed', 0)}")
        
        # 解析next_actions中的监控建议
        verification_results = []
        
        print(f"📋 待执行的验证步骤: {len(next_actions)} 项")
        for i, action in enumerate(next_actions, 1):
            print(f"  {i}. {action}")
        
        for action in next_actions:
            if "NodeExporterProtocol" in action:
                # 执行系统监控验证
                if "内存" in action or "memory" in action.lower():
                    verification_results.append(self._verify_system_metric("memory", "内存使用率"))
                elif "CPU" in action or "cpu" in action.lower():
                    verification_results.append(self._verify_system_metric("cpu", "CPU使用率"))
                elif "磁盘" in action or "disk" in action.lower():
                    verification_results.append(self._verify_system_metric("disk", "磁盘使用率"))
                elif "整体状态" in action or "overview" in action.lower():
                    verification_results.append(self._verify_system_metric("overview", "系统整体状态"))
                    
            elif "BlackboxExporterProtocol" in action:
                # 执行网络连通性验证
                verification_results.append(self._verify_network_connectivity())
        
        # 如果没有找到具体的验证项目，默认执行系统概览验证
        if not verification_results:
            print("⚠️ 未找到具体验证指标，执行系统概览验证...")
            verification_results.append(self._verify_system_metric("overview", "系统整体状态"))
        
        # 生成验证报告
        return self._generate_verification_report(data, verification_results)
    
    def _verify_system_metric(self, metric_type, metric_name):
        """验证系统指标"""
        print(f"🔍 正在验证{metric_name}...")
        
        try:
            # 导入并执行NodeExporterProtocol
            from .mcp_protocols import NodeExporterProtocol
            result = NodeExporterProtocol.execute({"metric_type": metric_type})
            
            if result.get("status") == "success":
                print(f"✅ {metric_name}验证完成")
                return {
                    "metric": metric_name,
                    "status": "success",
                    "data": result,
                    "summary": self._extract_metric_summary(result, metric_type)
                }
            else:
                print(f"❌ {metric_name}验证失败")
                return {
                    "metric": metric_name,
                    "status": "failed",
                    "error": result.get("error", "未知错误")
                }
                
        except Exception as e:
            print(f"❌ {metric_name}验证异常: {str(e)}")
            return {
                "metric": metric_name,
                "status": "error",
                "error": str(e)
            }
    
    def _verify_network_connectivity(self):
        """验证网络连通性"""
        print("🔍 正在验证网络连通性...")
        
        try:
            from .mcp_protocols import BlackboxExporterProtocol
            # 测试百度连通性
            result = BlackboxExporterProtocol.execute({
                "target": "https://www.baidu.com",
                "probe_type": "http"
            })
            
            if result.get("status") == "success":
                print("✅ 网络连通性验证完成")
                return {
                    "metric": "网络连通性",
                    "status": "success", 
                    "data": result,
                    "summary": "网络连接正常"
                }
            else:
                print("❌ 网络连通性验证失败")
                return {
                    "metric": "网络连通性",
                    "status": "failed",
                    "error": result.get("error", "连接失败")
                }
                
        except Exception as e:
            print(f"❌ 网络连通性验证异常: {str(e)}")
            return {
                "metric": "网络连通性",
                "status": "error",
                "error": str(e)
            }
    
    def _extract_metric_summary(self, result, metric_type):
        """提取指标摘要"""
        try:
            # NodeExporter返回的数据结构包含summary字段
            if "summary" in result and "key_findings" in result.get("summary", {}):
                key_findings = result["summary"]["key_findings"]
                if key_findings and len(key_findings) > 0:
                    return key_findings[0]  # 取第一个关键发现
            
            # 备用解析方式
            data = result.get("data", {})
            
            if metric_type == "memory":
                # 尝试从raw_data中解析内存数据
                raw_data = data.get("raw_data", {})
                if "node_memory_MemTotal_bytes" in raw_data and "node_memory_MemAvailable_bytes" in raw_data:
                    total_bytes = raw_data["node_memory_MemTotal_bytes"][0]["value"]
                    available_bytes = raw_data["node_memory_MemAvailable_bytes"][0]["value"]
                    used_bytes = total_bytes - available_bytes
                    mem_usage = (used_bytes / total_bytes) * 100
                    available_gb = available_bytes / (1024**3)
                    return f"内存使用率: {mem_usage:.1f}%, 可用内存: {available_gb:.1f}GB"
                
            elif metric_type == "cpu": 
                cpu_usage = data.get("cpu_usage_percent", 0)
                return f"CPU使用率: {cpu_usage:.1f}%"
                
            elif metric_type == "disk":
                disk_usage = data.get("disk_usage_percent", 0)
                return f"磁盘使用率: {disk_usage:.1f}%"
                
            elif metric_type == "overview":
                return "系统整体状态已检查"
                
            return "监控数据已获取"
            
        except Exception as e:
            print(f"⚠️ 数据解析异常: {str(e)}")
            return "数据解析中"
    
    def _generate_verification_report(self, original_data, verification_results):
        """生成验证报告"""
        print("\n📋 生成修复验证报告...")
        
        problem_desc = original_data.get("problem_description", "")
        fix_success = original_data.get("status") == "success"
        
        report = f"""
🔧 **自动修复验证报告**

📝 **原始问题**: {problem_desc}

🚀 **修复执行状态**: {'✅ 成功' if fix_success else '❌ 失败'}

📊 **验证结果**:
"""
        
        success_count = 0
        total_count = len(verification_results)
        
        # 处理不同的数据格式
        if not isinstance(verification_results, list):
            # 如果不是列表，转换为列表
            verification_results = [verification_results]
        
        for result in verification_results:
            # print("debug - result: ", result)
            
            # 如果result本身就是一个包含验证结果的对象
            if isinstance(result, dict):
                metric_name = result.get("metric", "未知指标")
                status = result.get("status", "unknown")
                summary = result.get("summary", "")
            else:
                # 处理其他格式的数据
                metric_name = "验证项目"
                status = "success" if result else "failed"
                summary = str(result)
            
            if status == "success":
                success_count += 1
                report += f"  ✅ {metric_name}: {summary}\n"
            elif status == "failed":
                error = result.get("error", "未知错误")
                report += f"  ❌ {metric_name}: 验证失败 - {error}\n"
            else:
                error = result.get("error", "未知错误")
                report += f"  ⚠️ {metric_name}: 验证异常 - {error}\n"
        
        report += f"\n📈 **验证成功率**: {success_count}/{total_count} ({100*success_count/total_count if total_count > 0 else 0:.0f}%)"
        
        # 添加建议
        if success_count == total_count:
            report += "\n\n🎉 **结论**: 修复验证全部通过，系统状态已恢复正常！"
        elif success_count > 0:
            report += "\n\n⚠️ **结论**: 修复部分成功，建议继续关注未恢复的指标。"
        else:
            report += "\n\n❌ **结论**: 修复效果未达预期，建议人工干预或重新执行修复。"
        
        report += "\n\n💡 **建议**: 继续定期监控系统状态，确保问题不再复现。"
        
        # print(report)
        return report 