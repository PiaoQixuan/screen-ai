# 屏幕AI助手

这是一个Pyhon工具，可以通过鼠标中键快速截取屏幕并发送给千问API进行分析。

## 功能特点

- 使用鼠标中键触发截图
- 自动调用千问API进行分析
- 在窗口中显示分析结果
- 支持自定义提问关键词
- 支持Telegram Bot推送分析结果到手机

## 安装步骤

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 创建 `.env` 文件并添加必要的API密钥：
   ```
   DASHSCOPE_API_KEY=你的千问API密钥
   TELEGRAM_BOT_TOKEN=你的Telegram Bot Token（可选）
   TELEGRAM_CHAT_ID=你的Telegram Chat ID（可选）
   ```

## 使用方法

1. 运行程序：
   ```bash
   python main.py
   ```
2. 点击鼠标中键进行截图
3. 等待分析结果显示在窗口中
4. 如果启用了Telegram Bot，结果也会推送到您的Telegram

## Telegram Bot 设置

要启用Telegram推送功能，需要完成以下步骤：

1. 在Telegram中找到 @BotFather，创建一个新的bot
2. 获取Bot Token
3. 获取您的Chat ID（可以使用 @userinfobot 获取）
4. 在程序界面中：
   - 在右侧设置面板找到"Telegram Bot 设置"
   - 输入Bot Token和Chat ID
   - 勾选"启用 Telegram Bot 推送"选项

您也可以将Token和Chat ID保存在 `.env` 文件中，这样程序启动时会自动加载。

## 注意事项

- 确保已安装Python 3.7或更高版本
- 需要有效的千问API密钥
- 程序需要屏幕录制权限（用于截图）
- Telegram Bot功能需要网络连接

## 自定义配置

你可以在程序界面中修改以下内容：

- 提问关键词（在右侧设置面板中修改）
- Telegram Bot设置（Token、Chat ID和启用状态）