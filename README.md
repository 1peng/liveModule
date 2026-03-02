# LiveModules

LiveModules 是一个用于微信视频号直播的辅助工具，提供实时消息获取、发送消息、回复评论等功能，帮助主播更好地管理直播间互动。

## 功能特性

- **微信视频号登录**：通过二维码扫码登录微信视频号
- **实时消息获取**：获取直播间的弹幕、礼物、点赞等消息
- **消息发送**：发送文本消息到直播间
- **评论回复**：回复观众的评论
- **在线成员信息**：获取直播间在线成员信息
- **消息管理**：清空历史消息

## 技术栈

- Python 3.7+
- FastAPI
- requests
- qrcode
- uvicorn

## 安装说明

### 1. 克隆项目

```bash
git clone <项目地址>
cd LiveModules
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 启动服务

```bash
python webapi.py
```

服务启动后，会生成一个微信登录二维码，使用微信扫码登录。

### 2. API 接口

服务启动后，可通过以下接口访问功能：

#### 获取直播消息
- **URL**: `/getmsg`
- **Method**: GET
- **返回**: 最新的直播消息列表

#### 清空消息
- **URL**: `/clsmsg`
- **Method**: GET
- **返回**: 清空结果

#### 获取在线成员
- **URL**: `/get_online_member`
- **Method**: GET
- **返回**: 在线成员信息

#### 发送直播消息
- **URL**: `/post_live_msg`
- **Method**: POST
- **参数**: `{"content": "消息内容"}`
- **返回**: 发送结果

#### 回复评论消息
- **URL**: `/post_live_app_msg`
- **Method**: POST
- **参数**: `{"contact": {...}, "content": "回复内容"}`
- **返回**: 回复结果

## 项目结构

```
LiveModules/
├── data/             # 数据目录，包含产品介绍等文本
│   └── 刀削面/        # 示例产品数据
├── msglist/          # 消息存储目录
├── utils/            # 工具函数
│   ├── request.py    # 请求相关工具
│   └── text.py       # 文本处理工具
├── auto-interaction.py # 自动交互功能
├── live-tts.py       # 文本转语音功能
├── webapi.py         # 主要API服务
├── requirements.txt  # 依赖文件
└── README.md         # 项目说明
```

## 注意事项

1. 请确保使用有效的微信账号登录
2. 登录后，服务会自动获取当前直播状态
3. 消息会存储在 `msglist` 目录中，定期清理以避免占用过多空间
4. 服务默认运行在 `http://0.0.0.0:8000`

## 常见问题

### 登录失败
- 请检查网络连接
- 确保微信账号已绑定视频号
- 尝试重新扫码登录

### 消息获取失败
- 请检查直播是否正在进行
- 确保网络连接稳定
- 尝试重启服务

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
