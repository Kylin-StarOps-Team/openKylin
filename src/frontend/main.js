const { app, BrowserWindow, ipcMain, screen, Tray, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

class StarOpsApp {
    constructor() {
        this.mainWindow = null;
        this.floatingWindow = null;
        this.tray = null;
        this.isDev = process.argv.includes('--development');
        this.reportsDir = path.join(__dirname, '../reports');
        this.mysqlReportsDir = path.join(__dirname, '../mysql_report');
        
        this.initApp();
    }

    initApp() {
        app.whenReady().then(() => {
            // 隐藏系统菜单栏（去掉file、edit等菜单）
            Menu.setApplicationMenu(null);
            
            this.createFloatingBall();
            this.setupTray();
            this.setupIPCHandlers();
        });

        app.on('window-all-closed', () => {
            // 在Linux上，除非用户明确退出，否则应用保持运行
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createFloatingBall();
            }
        });

        app.on('before-quit', () => {
            if (this.mainWindow) {
                this.mainWindow.destroy();
                this.mainWindow = null;
            }
            if (this.floatingWindow) {
                this.floatingWindow.destroy();
                this.floatingWindow = null;
            }
        });
    }

    createFloatingBall() {
        // 获取屏幕尺寸
        const primaryDisplay = screen.getPrimaryDisplay();
        const { width, height } = primaryDisplay.workAreaSize;

        this.floatingWindow = new BrowserWindow({
            width: 80,
            height: 80,
            x: width - 100,
            y: 100,
            frame: false,
            transparent: true,
            alwaysOnTop: true,
            skipTaskbar: true,
            resizable: false,
            minimizable: false,
            maximizable: false,
            closable: false,
            focusable: false,
            show: false,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                webSecurity: false,
                allowRunningInsecureContent: true
            }
        });

        this.floatingWindow.loadFile('floating-ball.html');
        
        // 窗口准备好后显示
        this.floatingWindow.once('ready-to-show', () => {
            this.floatingWindow.show();
            this.floatingWindow.setVisibleOnAllWorkspaces(true);
            this.floatingWindow.setAlwaysOnTop(true, 'floating');
        });
        
        // 双击事件处理
        this.floatingWindow.on('closed', () => {
            this.floatingWindow = null;
        });

        // 使悬浮球可拖拽
        this.floatingWindow.setIgnoreMouseEvents(false);
        
        if (this.isDev) {
            this.floatingWindow.webContents.openDevTools();
        }
    }

    createMainWindow() {
        if (this.mainWindow) {
            this.mainWindow.focus();
            return;
        }

        const primaryDisplay = screen.getPrimaryDisplay();
        const { width, height } = primaryDisplay.workAreaSize;

        this.mainWindow = new BrowserWindow({
            width: Math.min(1200, width * 0.8),
            height: Math.min(800, height * 0.8),
            minWidth: 800,
            minHeight: 600,
            frame: false,
            icon: path.join(__dirname, 'assets/icon.png'), // 需要添加图标
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                enableRemoteModule: true
            },
            show: false
        });

        this.mainWindow.loadFile('index.html');

        // 窗口准备好后显示
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            this.mainWindow.center();
            // 主界面打开时隐藏悬浮球
            if (this.floatingWindow) {
                this.floatingWindow.hide();
            }
        });

        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
            // 主界面关闭时显示悬浮球
            if (this.floatingWindow) {
                this.floatingWindow.show();
            }
        });

        if (this.isDev) {
            this.mainWindow.webContents.openDevTools();
        }
    }

    setupTray() {
        // 创建系统托盘图标（可选）
        if (fs.existsSync(path.join(__dirname, 'assets/tray-icon.png'))) {
            this.tray = new Tray(path.join(__dirname, 'assets/tray-icon.png'));
            
            const contextMenu = Menu.buildFromTemplate([
                { 
                    label: '显示主窗口', 
                    click: () => this.createMainWindow() 
                },
                { 
                    label: '显示悬浮球', 
                    click: () => {
                        if (!this.floatingWindow) {
                            this.createFloatingBall();
                        }
                    } 
                },
                { type: 'separator' },
                { 
                    label: '退出', 
                    click: () => app.quit() 
                }
            ]);
            
            this.tray.setToolTip('StarOps AI系统监控助手');
            this.tray.setContextMenu(contextMenu);
            
            this.tray.on('click', () => {
                this.createMainWindow();
            });
        }
    }

    setupIPCHandlers() {
        // 处理悬浮球双击事件
        ipcMain.handle('open-main-window', () => {
            this.createMainWindow();
        });

        // 处理关闭主窗口事件
        ipcMain.handle('close-main-window', () => {
            if (this.mainWindow) {
                this.mainWindow.close();
            }
        });

        // 处理最小化主窗口事件
        ipcMain.handle('minimize-main-window', () => {
            if (this.mainWindow) {
                this.mainWindow.minimize();
            }
        });

        // 处理最大化主窗口事件
        ipcMain.handle('maximize-main-window', () => {
            if (this.mainWindow) {
                if (this.mainWindow.isMaximized()) {
                    this.mainWindow.unmaximize();
                } else {
                    this.mainWindow.maximize();
                }
            }
        });

        // 处理Python智能监控调用
        ipcMain.handle('call-smart-monitor', async (event, question, conversationId, options = {}) => {
            return await this.callSmartMonitor(question, conversationId, options);
        });

        // 历史管理相关处理器
        ipcMain.handle('get-conversation-history', async () => {
            return await this.getConversationHistory();
        });

        ipcMain.handle('clear-conversation-history', async () => {
            return await this.clearConversationHistory();
        });

        ipcMain.handle('export-conversation-history', async () => {
            return await this.exportConversationHistory();
        });

        // 处理获取报告列表
        ipcMain.handle('get-web-reports', () => {
            return this.getWebReports();
        });

        ipcMain.handle('get-mysql-reports', () => {
            return this.getMysqlReports();
        });

        // 处理打开报告文件
        ipcMain.handle('open-report', (event, filePath) => {
            shell.openPath(filePath);
        });

        // 处理获取应用信息
        ipcMain.handle('get-app-info', () => {
            return {
                version: app.getVersion(),
                platform: process.platform,
                arch: process.arch
            };
        });
    }

    async callSmartMonitor(question, conversationId, options = {}) {
        return new Promise((resolve, reject) => {
            try {
                console.log('开始调用智能监控，问题：', question);
                console.log('对话ID：', conversationId);
                console.log('选项参数：', options);
                
                // 创建Python脚本来调用smart_monitor
                const pythonCode = `
import sys
import os
import json
import io
from contextlib import redirect_stdout, redirect_stderr

# 添加项目根目录到路径
sys.path.insert(0, '${path.join(__dirname, '..').replace(/\\/g, '/')}')

# 创建缓冲区来捕获所有输出
console_buffer = io.StringIO()

try:
    from core.smart_monitor import SmartMonitor
    from utils.config import Config
    from utils.history_manager import HistoryManager
    
    # 初始化配置、监控器和历史管理器
    config = Config()
    monitor = SmartMonitor(config.api_key)
    history_manager = HistoryManager()
    
    # 将历史加载到监控器中
    monitor.conversation_history = history_manager.conversation_history
    
    # 处理用户问题
    question = """${question.replace(/"/g, '\\"').replace(/\n/g, '\\n')}"""
    conversation_id = "${conversationId}"
    options = ${JSON.stringify(options).replace(/true/g, 'True').replace(/false/g, 'False').replace(/null/g, 'None')}
    
    print(f"[会话 {conversation_id}] 处理问题: {question}")
    if options:
        print(f"[会话 {conversation_id}] 选项参数: {options}")
    console_buffer.write(f"[会话 {conversation_id}] 处理问题: {question}\\n")
    
    # 使用自定义的print函数来同时输出到控制台和缓冲区
    import builtins
    original_print = builtins.print
    
    def dual_print(*args, **kwargs):
        # 输出到控制台
        original_print(*args, **kwargs)
        # 输出到缓冲区
        console_buffer.write(' '.join(str(arg) for arg in args) + '\\n')
    
    # 安全地替换print函数
    builtins.print = dual_print
    
    # 根据选项处理
    if options.get('force_protocol') and options.get('confirm_permissions'):
        # 如果是强制使用协议且已确认权限，直接调用对应协议
        force_protocol = options.get('force_protocol')
        problem_description = options.get('problem_description', question)
        
        print(f"[强制协议] 使用 {force_protocol}，问题描述: {problem_description}")
        
        # 从monitor获取协议并直接调用
        if hasattr(monitor, 'mcp_protocols') and force_protocol in monitor.mcp_protocols:
            protocol_class = monitor.mcp_protocols[force_protocol]
            params = {
                'problem_description': problem_description,
                'confirm_permissions': True
            }
            protocol_result = protocol_class.execute(params)
            
            # 构造标准返回格式
            result = {
                "type": "mcp_analysis",
                "analysis": f"✅ 已执行 {force_protocol} 自动修复",
                "mcp_result": protocol_result,
                "protocol": force_protocol,
                "forced_execution": True
            }
        else:
            result = {
                "type": "error",
                "error": f"未找到协议: {force_protocol}"
            }
    else:
        # 正常处理
        result = monitor.smart_query(question)
    
    # 恢复原始print函数
    builtins.print = original_print
    
    # 保存对话历史
    assistant_response = ""
    if result and result.get("type") == "mcp_analysis":
        assistant_response = result.get("analysis", "")
    elif result and result.get("type") == "direct_answer":
        assistant_response = result.get("answer", "")
    elif result and result.get("type") == "skywalking_direct_output":
        assistant_response = "SkyWalking分布式追踪分析已完成"
    else:
        assistant_response = "处理完成"
    
    # 添加对话到历史
    if assistant_response:
        history_manager.add_conversation(question, assistant_response)
        # 同步监控器的历史回历史管理器
        if hasattr(monitor, 'conversation_history') and monitor.conversation_history:
            history_manager.conversation_history = monitor.conversation_history
        # 保存历史
        history_manager.save_history()
        print(f"[历史] 已保存对话，当前历史包含 {history_manager.conversation_count} 轮对话")
    
    # 获取所有控制台输出
    all_console_output = console_buffer.getvalue()
    
    print("STAROPS_RESULT_START")
    print(json.dumps({
        "result": result,
        "conversation_id": conversation_id,
        "history_count": history_manager.conversation_count
    }, ensure_ascii=False, indent=2))
    print("STAROPS_RESULT_END")
    
    print("CONSOLE_OUTPUT_START")
    print(all_console_output.strip())
    print("CONSOLE_OUTPUT_END")
    
except Exception as e:
    import traceback
    all_console_output = console_buffer.getvalue()
    print("STAROPS_ERROR_START")
    print(f"错误: {str(e)}")
    print(f"详细信息: {traceback.format_exc()}")
    print("STAROPS_ERROR_END")
    
    print("CONSOLE_OUTPUT_START")
    print(all_console_output.strip())
    print("CONSOLE_OUTPUT_END")
`;

                console.log('Python代码：', pythonCode);

                const pythonProcess = spawn('python3', ['-c', pythonCode], {
                    cwd: path.join(__dirname, '..'),
                    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
                });

                let output = '';
                let error = '';

                pythonProcess.stdout.on('data', (data) => {
                    const text = data.toString();
                    output += text;
                    console.log('Python stdout:', text);
                });

                pythonProcess.stderr.on('data', (data) => {
                    const text = data.toString();
                    error += text;
                    console.log('Python stderr:', text);
                });

                pythonProcess.on('close', (code) => {
                    console.log('Python进程结束，退出码：', code);
                    console.log('完整输出：', output);
                    console.log('错误输出：', error);
                    
                    try {
                        if (output.includes('STAROPS_RESULT_START')) {
                            // 解析成功结果
                            const resultMatch = output.match(/STAROPS_RESULT_START\n(.*?)\nSTAROPS_RESULT_END/s);
                            if (resultMatch) {
                                try {
                                    const parsedData = JSON.parse(resultMatch[1]);
                                    console.log('解析成功的结果：', parsedData);
                                    
                                    // 提取控制台输出
                                    const consoleMatch = output.match(/CONSOLE_OUTPUT_START\n(.*?)\nCONSOLE_OUTPUT_END/s);
                                    const consoleOutput = consoleMatch ? consoleMatch[1] : '';
                                    
                                    // 提取调试数据
                                    const debugMatches = [];
                                    const debugRegex = /DEBUG_DATA_START\n(.*?)\nDEBUG_DATA_END/gs;
                                    let match;
                                    while ((match = debugRegex.exec(output)) !== null) {
                                        try {
                                            // 解析调试数据中的JSON
                                            const debugContent = match[1].trim();
                                            debugMatches.push(debugContent);
                                        } catch (e) {
                                            console.log('调试数据解析失败:', e);
                                        }
                                    }
                                    
                                    resolve({
                                        success: true,
                                        data: parsedData.result,
                                        console_output: consoleOutput,
                                        debug_data: debugMatches.length > 0 ? debugMatches : [parsedData.result],
                                        conversation_id: parsedData.conversation_id,
                                        raw_output: output
                                    });
                                    return;
                                } catch (jsonError) {
                                    console.error('JSON解析失败：', jsonError);
                                    console.error('原始JSON：', resultMatch[1]);
                                }
                            }
                        }
                        
                        if (output.includes('STAROPS_ERROR_START')) {
                            // 解析错误结果
                            const errorMatch = output.match(/STAROPS_ERROR_START\n(.*?)\nSTAROPS_ERROR_END/s);
                            if (errorMatch) {
                                resolve({
                                    success: false,
                                    error: errorMatch[1],
                                    raw_output: output
                                });
                                return;
                            }
                        }
                        
                        // 如果没有找到标记，返回通用错误
                        resolve({
                            success: false,
                            error: error || '执行失败，未找到结果标记',
                            code: code,
                            raw_output: output
                        });
                        
                    } catch (parseError) {
                        console.error('解析结果时出错：', parseError);
                        resolve({
                            success: false,
                            error: `解析结果失败: ${parseError.message}`,
                            raw_output: output
                        });
                    }
                });

                pythonProcess.on('error', (err) => {
                    console.error('Python进程启动失败：', err);
                    resolve({
                        success: false,
                        error: `启动Python进程失败: ${err.message}`
                    });
                });

            } catch (err) {
                console.error('调用智能监控失败：', err);
                resolve({
                    success: false,
                    error: `调用智能监控失败: ${err.message}`
                });
            }
        });
    }

    getWebReports() {
        try {
            if (!fs.existsSync(this.reportsDir)) {
                return [];
            }

            const files = fs.readdirSync(this.reportsDir)
                .filter(file => file.endsWith('.html'))
                .map(file => {
                    const filePath = path.join(this.reportsDir, file);
                    const stats = fs.statSync(filePath);
                    
                    // 解析文件名中的时间戳
                    let formattedTime = '时间未知';
                    try {
                        const timestampMatch = file.match(/web_config_report_(\d{8}_\d{6})\.html/);
                        if (timestampMatch) {
                            const timestamp = timestampMatch[1];
                            formattedTime = `${timestamp.substr(0,4)}-${timestamp.substr(4,2)}-${timestamp.substr(6,2)} ${timestamp.substr(9,2)}:${timestamp.substr(11,2)}:${timestamp.substr(13,2)}`;
                        }
                    } catch (e) {
                        // 使用文件修改时间
                        formattedTime = new Date(stats.mtime).toLocaleString('zh-CN');
                    }

                    // 尝试提取目标URL
                    let targetUrl = null;
                    try {
                        const content = fs.readFileSync(filePath, 'utf-8');
                        const urlMatch = content.match(/<p>目标URL:\s*([^<]+)<\/p>/);
                        if (urlMatch) {
                            targetUrl = urlMatch[1].trim();
                        }
                    } catch (e) {
                        // 忽略读取错误
                    }

                    return {
                        name: file,
                        path: filePath,
                        size: stats.size,
                        modifiedTime: formattedTime,
                        targetUrl: targetUrl
                    };
                })
                .sort((a, b) => b.size - a.size); // 按文件大小排序

            return files;
        } catch (error) {
            console.error('获取Web报告失败:', error);
            return [];
        }
    }

    getMysqlReports() {
        try {
            if (!fs.existsSync(this.mysqlReportsDir)) {
                return [];
            }

            const files = fs.readdirSync(this.mysqlReportsDir)
                .filter(file => file.startsWith('mysql_optimization_report_') && file.endsWith('.html'))
                .map(file => {
                    const filePath = path.join(this.mysqlReportsDir, file);
                    const stats = fs.statSync(filePath);
                    
                    // 提取检测编号
                    let detectionNum = '未知';
                    try {
                        const numMatch = file.match(/mysql_optimization_report_(\d+)\.html/);
                        if (numMatch) {
                            detectionNum = numMatch[1];
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }

                    // 尝试读取对应的建议文件
                    let suggestionsCount = 0;
                    try {
                        const suggestionsFile = file.replace('mysql_optimization_report_', 'mysql_suggestions_').replace('.html', '.json');
                        const suggestionsPath = path.join(this.mysqlReportsDir, suggestionsFile);
                        if (fs.existsSync(suggestionsPath)) {
                            const suggestionsData = JSON.parse(fs.readFileSync(suggestionsPath, 'utf-8'));
                            suggestionsCount = Array.isArray(suggestionsData) ? suggestionsData.length : 0;
                        }
                    } catch (e) {
                        // 忽略读取错误
                    }

                    return {
                        name: file,
                        path: filePath,
                        size: stats.size,
                        modifiedTime: new Date(stats.mtime).toLocaleString('zh-CN'),
                        detectionNum: detectionNum,
                        suggestionsCount: suggestionsCount
                    };
                })
                .sort((a, b) => parseInt(b.detectionNum) - parseInt(a.detectionNum)); // 按检测编号倒序

            return files;
        } catch (error) {
            console.error('获取MySQL报告失败:', error);
            return [];
        }
    }

    async getConversationHistory() {
        // 获取对话历史
        return new Promise((resolve, reject) => {
            try {
                const pythonCode = `
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, '${path.join(__dirname, '..').replace(/\\/g, '/')}')

try:
    from utils.history_manager import HistoryManager
    
    # 初始化历史管理器
    history_manager = HistoryManager()
    
    print("HISTORY_RESULT_START")
    print(json.dumps({
        "conversation_history": history_manager.conversation_history,
        "conversation_count": history_manager.conversation_count,
        "summary": history_manager.get_history_summary()
    }, ensure_ascii=False, indent=2))
    print("HISTORY_RESULT_END")
    
except Exception as e:
    import traceback
    print("HISTORY_ERROR_START")
    print(f"错误: {str(e)}")
    print(f"详细信息: {traceback.format_exc()}")
    print("HISTORY_ERROR_END")
`;

                const pythonProcess = spawn('python3', ['-c', pythonCode], {
                    cwd: path.join(__dirname, '..'),
                    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
                });

                let output = '';
                let error = '';

                pythonProcess.stdout.on('data', (data) => {
                    output += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    error += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    try {
                        if (output.includes('HISTORY_RESULT_START')) {
                            const resultMatch = output.match(/HISTORY_RESULT_START\n(.*?)\nHISTORY_RESULT_END/s);
                            if (resultMatch) {
                                const historyData = JSON.parse(resultMatch[1]);
                                resolve({
                                    success: true,
                                    data: historyData
                                });
                                return;
                            }
                        }
                        
                        if (output.includes('HISTORY_ERROR_START')) {
                            const errorMatch = output.match(/HISTORY_ERROR_START\n(.*?)\nHISTORY_ERROR_END/s);
                            if (errorMatch) {
                                resolve({
                                    success: false,
                                    error: errorMatch[1]
                                });
                                return;
                            }
                        }
                        
                        resolve({
                            success: false,
                            error: error || '获取历史失败',
                            raw_output: output
                        });
                        
                    } catch (parseError) {
                        resolve({
                            success: false,
                            error: `解析历史数据失败: ${parseError.message}`,
                            raw_output: output
                        });
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    async clearConversationHistory() {
        // 清空对话历史
        return new Promise((resolve, reject) => {
            try {
                const pythonCode = `
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, '${path.join(__dirname, '..').replace(/\\/g, '/')}')

try:
    from utils.history_manager import HistoryManager
    
    # 初始化历史管理器
    history_manager = HistoryManager()
    
    # 清空历史
    history_manager.clear_history()
    
    print("CLEAR_RESULT_START")
    print(json.dumps({
        "message": "历史已清空",
        "conversation_count": history_manager.conversation_count
    }, ensure_ascii=False, indent=2))
    print("CLEAR_RESULT_END")
    
except Exception as e:
    import traceback
    print("CLEAR_ERROR_START")
    print(f"错误: {str(e)}")
    print(f"详细信息: {traceback.format_exc()}")
    print("CLEAR_ERROR_END")
`;

                const pythonProcess = spawn('python3', ['-c', pythonCode], {
                    cwd: path.join(__dirname, '..'),
                    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
                });

                let output = '';
                let error = '';

                pythonProcess.stdout.on('data', (data) => {
                    output += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    error += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    try {
                        if (output.includes('CLEAR_RESULT_START')) {
                            const resultMatch = output.match(/CLEAR_RESULT_START\n(.*?)\nCLEAR_RESULT_END/s);
                            if (resultMatch) {
                                const clearData = JSON.parse(resultMatch[1]);
                                resolve({
                                    success: true,
                                    data: clearData
                                });
                                return;
                            }
                        }
                        
                        if (output.includes('CLEAR_ERROR_START')) {
                            const errorMatch = output.match(/CLEAR_ERROR_START\n(.*?)\nCLEAR_ERROR_END/s);
                            if (errorMatch) {
                                resolve({
                                    success: false,
                                    error: errorMatch[1]
                                });
                                return;
                            }
                        }
                        
                        resolve({
                            success: false,
                            error: error || '清空历史失败',
                            raw_output: output
                        });
                        
                    } catch (parseError) {
                        resolve({
                            success: false,
                            error: `解析清空结果失败: ${parseError.message}`,
                            raw_output: output
                        });
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    async exportConversationHistory() {
        // 导出对话历史
        return new Promise((resolve, reject) => {
            try {
                const pythonCode = `
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, '${path.join(__dirname, '..').replace(/\\/g, '/')}')

try:
    from utils.history_manager import HistoryManager
    
    # 初始化历史管理器
    history_manager = HistoryManager()
    
    # 导出历史
    export_filename = history_manager.export_history()
    
    print("EXPORT_RESULT_START")
    print(json.dumps({
        "message": "历史已导出",
        "filename": export_filename,
        "conversation_count": history_manager.conversation_count
    }, ensure_ascii=False, indent=2))
    print("EXPORT_RESULT_END")
    
except Exception as e:
    import traceback
    print("EXPORT_ERROR_START")
    print(f"错误: {str(e)}")
    print(f"详细信息: {traceback.format_exc()}")
    print("EXPORT_ERROR_END")
`;

                const pythonProcess = spawn('python3', ['-c', pythonCode], {
                    cwd: path.join(__dirname, '..'),
                    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
                });

                let output = '';
                let error = '';

                pythonProcess.stdout.on('data', (data) => {
                    output += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    error += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    try {
                        if (output.includes('EXPORT_RESULT_START')) {
                            const resultMatch = output.match(/EXPORT_RESULT_START\n(.*?)\nEXPORT_RESULT_END/s);
                            if (resultMatch) {
                                const exportData = JSON.parse(resultMatch[1]);
                                resolve({
                                    success: true,
                                    data: exportData
                                });
                                return;
                            }
                        }
                        
                        if (output.includes('EXPORT_ERROR_START')) {
                            const errorMatch = output.match(/EXPORT_ERROR_START\n(.*?)\nEXPORT_ERROR_END/s);
                            if (errorMatch) {
                                resolve({
                                    success: false,
                                    error: errorMatch[1]
                                });
                                return;
                            }
                        }
                        
                        resolve({
                            success: false,
                            error: error || '导出历史失败',
                            raw_output: output
                        });
                        
                    } catch (parseError) {
                        resolve({
                            success: false,
                            error: `解析导出结果失败: ${parseError.message}`,
                            raw_output: output
                        });
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }
}

// 启动应用
new StarOpsApp();
