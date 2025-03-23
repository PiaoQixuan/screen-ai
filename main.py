import sys
import os
import time
from datetime import datetime
from pynput import mouse
from PIL import ImageGrab
import base64
from openai import OpenAI
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
                            QHBoxLayout, QWidget, QLabel, 
                            QGroupBox, QSplitter, QPlainTextEdit,
                            QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MouseListener(QThread):
    clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.listener = None
        
    def run(self):
        def on_click(x, y, button, pressed):
            if button == mouse.Button.middle and pressed:
                print("[DEBUG] 检测到鼠标中键点击")
                self.clicked.emit()
            return self.running
            
        print("[DEBUG] 开始监听鼠标中键")
        with mouse.Listener(on_click=on_click) as listener:
            self.listener = listener
            listener.join()
            
    def stop(self):
        print("[DEBUG] 停止鼠标监听")
        self.running = False
        if self.listener:
            self.listener.stop()

class ScreenshotThread(QThread):
    finished = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
    
    def run(self):
        try:
            self.log_signal.emit("开始截取屏幕...")
            # 截取屏幕
            screenshot = ImageGrab.grab()
            
            # 保存截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot.save(filename)
            self.log_signal.emit(f"截图已保存为: {filename}")
            
            # 调用千问 API
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                self.log_signal.emit("错误：未设置DASHSCOPE_API_KEY环境变量")
                return
                
            self.log_signal.emit("正在调用千问 VL API分析图片...")
            
            # 读取图片并转换为base64
            with open(filename, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 创建OpenAI客户端（使用千问兼容模式）
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # 调用API
            response = client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )
            
            self.finished.emit(response.choices[0].message.content)
            self.log_signal.emit("分析完成！")
        except Exception as e:
            error_msg = f"发生错误：{str(e)}"
            self.log_signal.emit(error_msg)
            self.finished.emit(error_msg)
        finally:
            # 清理临时文件
            if os.path.exists(filename):
                os.remove(filename)
                self.log_signal.emit("临时文件已清理")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("屏幕AI助手")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左右分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：回答区
        answer_group = QGroupBox("AI分析结果")
        answer_layout = QVBoxLayout()
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)
        answer_layout.addWidget(self.answer_text)
        answer_group.setLayout(answer_layout)
        splitter.addWidget(answer_group)
        
        # 右侧：设置和日志
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)  # 设置垂直间距
        
        # 设置区
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)  # 设置垂直间距
        
        # 提示词设置
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(5)  # 减小标签和输入框的间距
        prompt_label = QLabel("提问关键词：")
        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText("请输入分析图片时的提示词...")
        self.prompt_input.setMaximumHeight(80)  # 减小文本框高度
        default_prompt = "请分析这张截图并回答以下问题：\n1. 这是什么类型的界面？\n2. 主要功能是什么？\n3. 有什么可以改进的地方？"
        self.prompt_input.setPlainText(default_prompt)
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_input)
        settings_layout.addLayout(prompt_layout)
        
        # 设置组的大小策略
        settings_group.setLayout(settings_layout)
        settings_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        right_layout.addWidget(settings_group)
        
        # 日志区
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        # 初始化鼠标监听器
        self.mouse_listener = MouseListener()
        self.mouse_listener.clicked.connect(self.take_screenshot)
        self.mouse_listener.start()
        
        # 截图线程
        self.screenshot_thread = None
        
        # 添加初始日志
        self.log("程序已启动")
        self.log("按下鼠标中键进行截图")
            
    def take_screenshot(self):
        print("[DEBUG] 触发截图功能")
        if self.screenshot_thread is None or not self.screenshot_thread.isRunning():
            prompt = self.prompt_input.toPlainText()
            print(f"[DEBUG] 创建截图线程，提示词: {prompt}")
            self.screenshot_thread = ScreenshotThread(prompt)
            self.screenshot_thread.finished.connect(self.update_result)
            self.screenshot_thread.log_signal.connect(self.log)
            self.screenshot_thread.start()
        else:
            print("[DEBUG] 截图线程正在运行中，忽略本次触发")
            
    def update_result(self, result):
        self.answer_text.append(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        self.answer_text.append(result)
        self.answer_text.append("\n" + "="*50 + "\n")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        # 停止鼠标监听
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 