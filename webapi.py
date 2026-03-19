import requests
import time
import qrcode
import uuid
import json
import queue
import os
import uvicorn
import base64
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 请求模型
class MessageRequest(BaseModel):
    content: str

class ReplyRequest(BaseModel):
    contact: dict
    content: str

from threading import Thread, Lock, enumerate

# 配置类，使用单例模式管理全局变量
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance
    
    def _init_config(self):
        # 初始化配置
        self.uid = uuid.uuid4().hex
        self.uid22 = str(uuid.uuid4())
        self.uid33 = str(uuid.uuid4())
        self.session = requests.Session()
        self.finderUsername = ''
        self.txvideo_nickname = ''
        self.txvideo_headImgUrl = ''
        self.wx_nickname = ''
        self.wx_username = ''
        self.wx_encryptedHeadImage = ''
        self.adminNickname = ''
        self.fansCount = 0
        self.uniqId = ''
        self.authKey = ""
        self.X_Wechat_Uin = ""
        self.liveObjectId = ""
        self.liveId = ""
        self.live_description = ""
        self.liveCookies = ""
        self.cookies_data = ""
        self.email_smtp_server = "smtp.gmail.com"
        self.email_smtp_port = 465
        self.email_sender = "easonwang105@gmail.com"
        self.email_password = "uiervgrvltihbbdo"
        self.email_receiver = "228331207@qq.com"
    
    def save(self):
        """保存配置到文件"""
        config_data = {
            'finderUsername': self.finderUsername,
            'txvideo_nickname': self.txvideo_nickname,
            'txvideo_headImgUrl': self.txvideo_headImgUrl,
            'wx_nickname': self.wx_nickname,
            'wx_username': self.wx_username,
            'wx_encryptedHeadImage': self.wx_encryptedHeadImage,
            'adminNickname': self.adminNickname,
            'fansCount': self.fansCount,
            'uniqId': self.uniqId,
            'authKey': self.authKey,
            'X_Wechat_Uin': self.X_Wechat_Uin,
            'liveObjectId': self.liveObjectId,
            'liveId': self.liveId,
            'live_description': self.live_description,
            'liveCookies': self.liveCookies,
            'cookies_data': self.cookies_data,
            'email_smtp_server': self.email_smtp_server,
            'email_smtp_port': self.email_smtp_port,
            'email_sender': self.email_sender,
            'email_password': self.email_password,
            'email_receiver': self.email_receiver
        }
        with open('global_vars.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载配置"""
        try:
            with open('global_vars.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.finderUsername = config_data.get('finderUsername', '')
            self.txvideo_nickname = config_data.get('txvideo_nickname', '')
            self.txvideo_headImgUrl = config_data.get('txvideo_headImgUrl', '')
            self.wx_nickname = config_data.get('wx_nickname', '')
            self.wx_username = config_data.get('wx_username', '')
            self.wx_encryptedHeadImage = config_data.get('wx_encryptedHeadImage', '')
            self.adminNickname = config_data.get('adminNickname', '')
            self.fansCount = config_data.get('fansCount', 0)
            self.uniqId = config_data.get('uniqId', '')
            self.authKey = config_data.get('authKey', '')
            self.X_Wechat_Uin = config_data.get('X_Wechat_Uin', '')
            self.liveObjectId = config_data.get('liveObjectId', '')
            self.liveId = config_data.get('liveId', '')
            self.live_description = config_data.get('live_description', '')
            self.liveCookies = config_data.get('liveCookies', '')
            self.cookies_data = config_data.get('cookies_data', '')
            self.email_smtp_server = config_data.get('email_smtp_server', '')
            self.email_smtp_port = config_data.get('email_smtp_port', 465)
            self.email_sender = config_data.get('email_sender', '')
            self.email_password = config_data.get('email_password', '')
            self.email_receiver = config_data.get('email_receiver', '')
            return True
        except Exception as e:
            print(f"load config exception: {str(e)}")
            return False

# 全局配置实例
config = Config()

def send_error_email(subject, error_message):
    if not config.email_smtp_server or not config.email_sender or not config.email_password or not config.email_receiver:
        logger.warning("Email configuration is incomplete, skipping email notification")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config.email_sender
        msg['To'] = config.email_receiver
        msg['Subject'] = subject
        
        body = f"""
错误时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误信息: {error_message}
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP_SSL(config.email_smtp_server, config.email_smtp_port) as server:
            server.login(config.email_sender, config.email_password)
            server.sendmail(config.email_sender, config.email_receiver, msg.as_string())
        
        logger.info(f"Error email sent successfully to {config.email_receiver}")
        return True
    except Exception as e:
        logger.error(f"Failed to send error email: {str(e)}")
        return False

# 线程锁
app = FastAPI()
msglist = queue.Queue()
mutex = Lock()
terminate_flag = False

# 生成公共HTTP请求头
def get_common_headers():
    """生成公共的HTTP请求头"""
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": config.X_Wechat_Uin,
        "finger-print-device-id": config.uid,
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

# 生成带cookie的HTTP请求头
def get_headers_with_cookie():
    """生成带cookie的HTTP请求头"""
    headers = get_common_headers()
    headers["cookie"] = "; ".join([f"{k}={v}" for k, v in config.cookies_data.items()]) if isinstance(config.cookies_data, dict) else ""
    return headers


def filtertime():
    # 获取今天0点的时间戳
    today = time.time()
    filterEndTime = int(today) - (int(today) % 86400)

    # 减去 8664 天
    diff_days = 8664
    filterStartTime = filterEndTime - (diff_days * 86400)

    print("今天0点的时间戳：", filterEndTime)
    print("相减后的时间戳：", filterStartTime)    
    return filterEndTime,filterStartTime

def setcoockis(response):
    # 获取返回的cookie值
    cookies = response.cookies
    # 打印cookie值
    # print("返回的cookie值：")
    # for cookie in cookies:
    #     print(cookie.name, cookie.value)
    config.cookies_data = dict(cookies)

def generate_timestamp(length=10):
    current_time = time.time()
    if length == 10:
        timestamp = int(current_time)
    elif length == 13:
        timestamp = int(current_time * 1000)
    else:
        raise ValueError("Invalid timestamp length. Must be 10 or 13.")
    return  str(timestamp)

#初始化信息
def hepler_merlin_mmdata():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/hepler_merlin_mmdata"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1"
    # 移除X-WECHAT-UIN，因为这个接口不需要
    if "X-WECHAT-UIN" in headers:
        del headers["X-WECHAT-UIN"]
    time10=generate_timestamp(10)
    time13=generate_timestamp(13)
    data = {
        "id": 23865,
        "data": {
            "12": "",
            "13": "",
            "14": "",
            "15": "",
            "16": "",
            "17": time10,
            "18": time10,
            "19": 1,
            "20": "",
            "21": 2,
            "22": config.uid22,#"398e6d66-8c4d-45db-93f8-b13e240b0892",
            "23": "",
            "24": time13,
            "25": "",
            "26": 0,
            "27": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "28": "",
            "29": "",
            "30": "",
            "31": "LoginForIframe",
            "32": "",
            "33": config.uid33,#"556ff363-7c8b-4f2f-853e-79c35d51e4e7",
            "34": "",
            "35": "",
            "36": 1,
            "37": "{}",
            "38": "",
            "39": "{}",
            "40": "pageEnter",
            "41": "{}",
            "42": "{\"screenHeight\":1032;\"screenWidth\":1920;\"clientHeight\":0;\"clientWidth\":0}",
            "43": ""
        },
        "_log_finder_id": ""
    }

    response = config.session.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return None

#初始化信息2
def helper_mmdata():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_mmdata"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1"
    # 移除X-WECHAT-UIN，因为这个接口不需要
    if "X-WECHAT-UIN" in headers:
        del headers["X-WECHAT-UIN"]
    data = {
        "id": 21307,
        "data": {
            "13": "",
            "14": "",
            "15": "",
            "17": "null",
            "19": None,
            "20": None,
            "21": int(generate_timestamp(13)),
            "22": generate_timestamp(13)
        },
        "addFinderUinBy": 16
    }

    response = config.session.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return None

#获取登录二维码
def getrcode():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_code"

    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1"
    headers["X-WECHAT-UIN"] = "0000000000"

    data = {
        "timestamp": str(int(time.time() * 1000)),  # 使用13位时间戳
        "_log_finder_uin": "",
        "_log_finder_id": "",
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = config.session.post(url, headers=headers, json=data)
    #setcoockis(response)
    rejson=response.json()

    print(f'getrcode_errMesg:{rejson["errMsg"]}')

    if 'token' in rejson['data']:
        return rejson['data']['token']

    return ''

def request_qrcode(retoken):
    url = f"https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_status?token={retoken}&timestamp={generate_timestamp(13)}&_log_finder_uin=&_log_finder_id=&scene=7&reqScene=7"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1"
    headers["X-WECHAT-UIN"] = "0000000000"
    count = 0
    status= 0
    acctStatus = 0
    while count < 200:
        response = config.session.post(url, headers=headers)
        setcoockis(response)
        rejson=response.json()
        if rejson['errCode'] == 0:
            # 处理返回的数据
            # ...
            status=rejson['data']['status']
            acctStatus=rejson['data']['acctStatus']
            if status==0 and acctStatus==0:
                print('请使用微信扫码登录！')
            elif status==5 and acctStatus==1:
                print('已扫码请在手机上点击确认登录！')
            elif status==1 and acctStatus==1:
                print('已成功登录！')
                break
            elif status==3 and acctStatus==0:
                print('已成功登录！')
                break
            else:
                print(rejson)
                print('超时或网络异常已退出')
                break

            count += 1
            time.sleep(1)
        else:
            print("请求失败")
            break

    if count >= 200:
        print("二维码已超时")
    if status==1 & acctStatus==1:
        return True
    return False

def auth_data():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_data"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login"
    headers["X-WECHAT-UIN"] = "0000000000"
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": "",
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = config.session.post(url, headers=headers, json=data)
    # setcoockis(response)
    rejson=response.json()
    #print(response.json())
    if rejson['errCode'] == 0:
        config.wx_encryptedHeadImage = rejson['data']['userAttr']['encryptedHeadImage']
        config.wx_nickname = rejson['data']['userAttr']['nickname']
        config.wx_username = rejson['data']['userAttr']['username']
        config.txvideo_headImgUrl = rejson['data']['finderUser']['headImgUrl']
        config.txvideo_nickname = rejson['data']['finderUser']['nickname']
        config.finderUsername = rejson['data']['finderUser']['finderUsername']
        # 保存全局变量
        config.save()
        return True
    else:
        print("登录异常："+rejson['errMsg'])
        return False

def helper_upload_params():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_upload_params"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/login"
    headers["X-WECHAT-UIN"] = "0000000000"
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = config.session.post(url, headers=headers, json=data)
    rejson=response.json()
    if rejson['errCode'] == 0:
        config.authKey = rejson['data']['authKey']
        config.X_Wechat_Uin = str(rejson['data']['uin'])
        # 保存全局变量
        config.save()
        return True
    else:
        return False

def check_live_status():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/check_live_status"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/live/home"
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("check_live_status")
    try:
        response = config.session.post(url, headers=headers, json=data,timeout=30)

        rejson=response.json()
        if rejson['errCode'] == 0:
            config.liveId = rejson['data']['liveId']
            config.live_description = rejson['data'].get('description', '')
            config.liveObjectId = rejson['data']['liveObjectId']
            # print(f"post_live_msg liveId: {config.liveId}")
            # print(f"post_live_msg liveObjectId: {config.liveObjectId}")
            # 保存全局变量
            config.save()
            #print("check_live_status end")
            if rejson['data']['status']==1:
                logger.info(f'直播间【{config.live_description}】状态正常')
            else:
                logger.warning(f'直播间【{config.live_description}】状态={str(rejson["data"]["status"])}')
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        logger.warning("check_live_status请求超时了")
        return True

#获取历史直播场次的记录。这里可以不用调用
def get_live_history():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/get_live_history"
    headers = get_common_headers()
    headers["Referer"] = "https://channels.weixin.qq.com/platform/live/home"
    request=filtertime()
    filterEndTime,filterStartTime=request
    #查询的开始和结束时间
    data = {
        "pageSize": 1,
        "currentPage": 1,
        "reqType": 2,
        "filterStartTime": filterStartTime,
        "filterEndTime": filterEndTime,
        "timestamp":generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = config.session.post(url, headers=headers, json=data)

    rejson=response.json()
    if rejson['errCode'] == 0:
        return True
    else:
        return False

#
def get_live_info():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/get_live_info"
    headers = get_common_headers()
    data = {
        "liveObjectId": config.liveObjectId,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print('get_live_info')
    try:
        response = config.session.post(url, headers=headers, json=data,timeout=30)

        rejson=response.json()
        if rejson['errCode'] == 0:
            return True
        else:
            logger.error(f"get_live_info异常：{rejson}")
            return False
    except requests.exceptions.Timeout:
        logger.warning("get_live_info请求超时了")
        return True

#获取msg消息刷新cookie
def join_live():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/join_live"
    headers = get_common_headers()
    data = {
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "liveId": config.liveId,
        "timestamp": str(int(time.time() * 1000)), # 使用当前的时间戳
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = config.session.post(url, headers=headers, json=data)

    rejson=response.json()
    if rejson['errCode'] == 0:
        config.liveCookies = rejson['data']['liveCookies']
        # 保存全局变量
        config.save()
        return True
    else:
        logger.error(f"join_live异常：{rejson}")
        return False

#获取最新在线人员信息
def a_online_member():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/online_member"
    headers = get_common_headers()
    data = {
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "clearRecentRewardHistory": True,
        "liveId": config.liveId,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    #print(f'online_member',data)
    #print('online_member')
    try:
        response = config.session.post(url, headers=headers, json=data,timeout=30)
        rejson=response.json()
        #print(rejson)
        if rejson['errCode'] == 0:
            json_str = json.dumps(rejson)
            # 将 JSON 字符串写入本地文件
            with open("online_member.json", "w") as file:
                file.write(json_str)
            return True
        else:
            logger.error(f"online_member异常：{rejson}")
            return False
    except requests.exceptions.Timeout:
        logger.warning("online_member请求超时")
        return True

def msg():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/msg"

    headers = get_common_headers()

    data = {
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "liveCookies": config.liveCookies,
        "liveId": config.liveId,
        "longpollingScene": 0,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("msg")
    try:
        response = config.session.post(url, json=data, headers=headers,timeout=30)
        #print('msg1')
        rejson=response.json()
        #print('msg2')
        if rejson['errCode'] == 0:
            #对本次的消息进行解析

            config.liveCookies = rejson['data']['liveCookies']
            #print("liveCookies",config.liveCookies)
            downmsg(rejson['data'])
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        logger.warning("msg请求超时了")
        return True

import random

def generate_uuid_v4(random_array=None, buffer=None, offset=0):
    """
    生成一个符合 UUID v4 标准的标识符。
    
    :param random_array: 可选，传入一个包含 16 个整数的列表作为随机源。
    :param buffer: 可选，一个列表，用于存储生成的字节。
    :param offset: 配合 buffer 使用，指定写入的起始位置。
    :return: 如果没有提供 buffer，返回格式化后的 UUID 字符串；否则返回填充后的 buffer。
    """
    
    # 1. 获取随机数数组
    # 如果传入了 random_array 则使用它，否则生成 16 个 0-255 的随机字节
    if random_array is None:
        # 使用 os.urandom 获取加密安全的随机字节，或使用 random.randint 作为替代
        bytes_array = [random.randint(0, 255) for _ in range(16)]
    else:
        bytes_array = random_array[:]
    
    # 2. 设置 UUID 版本 (Version) 和 变体 (Variant)
    # 索引 6: 高 4 位固定为 0100 (即十六进制的 4)，所以值范围在 0x40-0x4F 之间
    # 使用按位与 0x0F 保留低 4 位的随机值，使用按位或 0x40 设置高 4 位
    bytes_array[6] = 0x40 | (0x0F & bytes_array[6])
    
    # 索引 8: 高 2 位固定为 10 (即十六进制的高位为 8, 9, A, 或 B)，所以值范围在 0x80-0xBF 之间
    # 使用按位与 0x3F 保留低 6 位的随机值，使用按位或 0x80 设置高 2 位
    bytes_array[8] = 0x80 | (0x3F & bytes_array[8])
    
    # 3. 如果传入了 buffer，则将结果写入 buffer
    if buffer is not None:
        for i in range(16):
            buffer[offset + i] = bytes_array[i]
        return buffer
    
    # 4. 否则，格式化为标准的 UUID 字符串并返回
    return format_uuid_string(bytes_array)

def format_uuid_string(bytes_array):
    """
    将 16 字节的数组格式化为标准的 UUID 字符串 (8-4-4-4-12 格式)。
    """
    # 将每个字节转换为两位的十六进制字符串
    hex_parts = [f"{b:02x}" for b in bytes_array]
    
    # 按照 UUID 标准格式拼接
    # 索引: 0-3, 4-5, 6-7, 8-9, 10-15
    uuid_str = (
        "".join(hex_parts[0:4]) + "-" +
        "".join(hex_parts[4:6]) + "-" +
        "".join(hex_parts[6:8]) + "-" +
        "".join(hex_parts[8:10]) + "-" +
        "".join(hex_parts[10:16])
    )
    return uuid_str

def post_live_msg(content):
    # 加载全局变量
    config.load()
    # print(f"post_live_msg global variables: liveCookies={config.liveCookies}, liveObjectId={config.liveObjectId}, liveId={config.liveId}, finderUsername={config.finderUsername}, X_Wechat_Uin={config.X_Wechat_Uin}")
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/post_live_msg"
    
    headers = get_headers_with_cookie()
    
    client_msg_id = f"pc_{config.finderUsername}_{generate_uuid_v4()}"
    
    data = {
        "liveCookies": config.liveCookies,
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "liveId": config.liveId,
        "clientMsgId": client_msg_id,
        "msgJson": json.dumps({"content": content, "type": 1}),
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    
    try:
        # print(f"post_live_msg cookies_data: {config.cookies_data}")
        # print(f"post_live_msg headers: {headers}")
        # print(f"post_live_msg data: {data}")
        # print(f"post_live_msg headers: {headers}")
        response = config.session.post(url, json=data, headers=headers, timeout=30)
        # print(f"post_live_msg response status: {response.status_code}")
        # print(f"post_live_msg response text: {response.text}")
        rejson = response.json()
        # print(f"post_live_msg response json: {rejson}")
        if rejson['errCode'] == 0:
            # Update liveCookies if returned
            if 'data' in rejson and 'liveCookies' in rejson['data']:
                config.liveCookies = rejson['data']['liveCookies']
                # 保存全局变量
                config.save()
            return True
        else:
            logger.error(f"post_live_msg error: {rejson['errMsg']}")
            send_error_email("post_live_msg 错误提醒", f"post_live_msg error: {rejson['errMsg']}")
            return False
    except Exception as e:
        logger.error(f"post_live_msg exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def post_live_app_msg(to_user_contact, content):
    # 加载全局变量
    config.load()
    
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/post_live_app_msg"
    
    headers = get_headers_with_cookie()
    headers["Accept"] = "*/*"
    headers["Accept-Language"] = "zh-CN,zh;q=0.9,zh-TW;q=0.8"
    headers["Referer"] = "https://channels.weixin.qq.com/micro/live/liveBuild"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    headers["sec-ch-ua"] = "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\""
    
    client_msg_id = f"pc_{config.finderUsername}_{generate_uuid_v4()}"
    
    # 构建 msgJson
    msg_json = {
        "client_msg_id": client_msg_id,
        "to_user_contact": to_user_contact,
        "msg_type": 20002,
        "payload": base64.b64encode(json.dumps({"content": content}).encode('utf-8')).decode('utf-8')
    }
    
    data = {
        "liveCookies": config.liveCookies,
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "liveId": config.liveId,
        "msgJson": json.dumps(msg_json),
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    
    try:
        # print(f"post_live_app_msg cookies_data: {config.cookies_data}")
        # print(f"post_live_app_msg headers: {headers}")
        # print(f"post_live_app_msg data: {data}")
        response = config.session.post(url, json=data, headers=headers, timeout=30)
        # print(f"post_live_app_msg response status: {response.status_code}")
        # print(f"post_live_app_msg response text: {response.text}")
        # 尝试解析响应
        try:
            rejson = response.json()
            logger.debug(f"post_live_app_msg response json: {rejson}")
            if rejson.get('errCode') == 0:
                # Update liveCookies if returned
                if 'data' in rejson and 'liveCookies' in rejson['data']:
                    config.liveCookies = rejson['data']['liveCookies']
                    # 保存全局变量
                    config.save()
                return True
            else:
                logger.error(f"post_live_app_msg error: {rejson.get('errMsg', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            logger.error(f"post_live_app_msg response is not JSON: {response.text}")
            return False
    except Exception as e:
        logger.error(f"post_live_app_msg exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def reward_gains():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/reward_gains"
    headers = get_common_headers()
    data = {
        "objectId": config.liveObjectId,
        "finderUsername": config.finderUsername,
        "clearRecentRewardHistory": True,
        "liveId": config.liveId,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("reward_gains")
    try:
        response = config.session.post(url, headers=headers, json=data,timeout=30)
        rejson=response.json()

        if rejson['errCode'] == 0:
            return True
        else:
            logger.error('reward_gains_err:')
            logger.error(rejson)
            return False
    except requests.exceptions.Timeout:
        logger.warning("reward_gains请求超时了")
        return True

def gift_enum_list():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/gift_enum_list"
    headers = get_common_headers()
    data = {
        "objectId": config.liveObjectId,
        "username": config.finderUsername,
        "liveId": config.liveId,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": config.finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    
    response = config.session.post(url, headers=headers, json=data)
    rejson=response.json()
    logger.debug("gift_enum_list:")
    logger.debug(data)
    logger.debug(rejson)
    if rejson['errCode'] == 0:
        return True
    else:
        return False


def downmsg(rejson):
    """解析和处理直播消息"""
    def extract_contact_info(member, contact_key):
        """提取联系人信息"""
        contact_data = member.get(contact_key, {})
        badge_infos = contact_data.get('badgeInfos', [])
        contact = contact_data.get('contact', {})
        nickname = contact.get('nickname', '')
        username = contact.get('username', '')
        signature = contact.get('signature', '')
        ext_info = contact.get('extInfo', {})
        return nickname, username, signature, ext_info, badge_infos, contact
    
    newmsg = []
    
    # 处理普通消息
    for member in rejson.get('msgList', []):
        msg_type = member.get('type')
        if msg_type in (1, 10005):  # 文本消息和系统消息
            nickname = member.get('nickname', '')
            username = member.get('username', '')
            content = member.get('content', '')
            _, _, signature, ext_info, badge_infos, contact = extract_contact_info(member, 'finderLiveContact')
            
            newmsg.append({
                'nickname': nickname,
                'msgType': msg_type,
                'username': username,
                'content': content,
                'signature': signature,
                'ext_info': ext_info,
                'badge_infos': badge_infos,
                'contact': contact
            })
    
    # 处理应用消息（如礼物）
    for member in rejson.get('appMsgList', []):
        msg_type = member.get('msgType')
        if msg_type in (20009, 20078, 20006):  # 礼物消息 || 关注消息 || 点赞消息
            nickname, username, signature, ext_info, badge_infos, contact = extract_contact_info(member, 'fromUserContact')
            
            # 解析礼物信息
            base64_string = member.get('payload', '')
            gift_info = {}
            try:
                decoded_string = base64.b64decode(base64_string).decode('utf-8')
                gift_info = json.loads(decoded_string)
            except Exception as e:
                logger.error(f"解析礼物信息失败: {e}")
            
            newmsg.append({
                'nickname': nickname,
                'msgType': msg_type,
                'username': username,
                'gift_info': gift_info,
                'signature': signature,
                'ext_info': ext_info,
                'badge_infos': badge_infos,
                'contact': contact
            })
        else:
            logger.warning(f"未知消息类型: {msg_type}")
    
    # 保存消息到文件
    if newmsg:
        # 确保tmp目录存在
        os.makedirs("tmp", exist_ok=True)
        
        # 生成文件路径
        file_path = os.path.join("tmp", f"{generate_timestamp(13)}.json")
        
        # 保存数据
        with open(file_path, "w", encoding='utf-8') as file:
            json.dump(newmsg, file, ensure_ascii=False, indent=2)

def getmsg():
    """获取直播消息的主循环"""
    count = 0
    global terminate_flag
    
    try:
        logger.info("消息获取线程已启动")
        while not terminate_flag:
            count += 1
            
            # 每3次循环检查一次直播状态和在线成员
            if count % 3 == 0:
                try:
                    if not (check_live_status() and a_online_member() and reward_gains()):
                        logger.warning("直播状态检查失败，退出消息获取循环")
                        break
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"检查直播状态时出错: {e}")
                    time.sleep(1)  # 出错时暂停更长时间
            
            # 每次循环都获取消息
            try:
                if not (get_live_info() and msg()):
                    logger.warning("获取消息失败，退出消息获取循环")
                    break
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"获取消息时出错: {e}")
                time.sleep(1)  # 出错时暂停更长时间
    except Exception as e:
        logger.error(f"消息获取线程异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("消息获取线程已退出")
        
@app.get("/getmsg")
def getmsgs():
    """获取直播消息"""
    msglist_dir = "tmp"
    
    # 检查目录是否存在
    if not os.path.exists(msglist_dir):
        return {"code": 0, "message": "目录不存在"}
    
    # 获取目录下的所有文件并按修改时间排序
    try:
        files = sorted(
            [f for f in os.listdir(msglist_dir) if os.path.isfile(os.path.join(msglist_dir, f))],
            key=lambda x: os.path.getmtime(os.path.join(msglist_dir, x))
        )
        
        # 检查是否有文件
        if not files:
            return {"code": 0, "message": "目前没有消息"}
        
        # 取最早的文件
        first_file = files[0]
        file_path = os.path.join(msglist_dir, first_file)
        
        # 读取文件内容
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                file_content = file.read()
        except UnicodeDecodeError:
            # 尝试使用其他编码读取
            with open(file_path, "r", encoding='utf-8', errors='replace') as file:
                file_content = file.read()
        
        # 删除已读取的文件
        os.remove(file_path)
        
        # 返回文件内容
        return {"code": 1, "message": "读取成功", "data": json.loads(file_content)}
    except Exception as e:
        logger.error(f"获取消息时出错: {e}")
        return {"code": 0, "message": f"读取失败: {str(e)}"}

@app.get("/clsmsg")
def clear_messages():
    """清空所有消息"""
    msglist_dir = "tmp"
    
    # 检查目录是否存在
    if not os.path.exists(msglist_dir):
        return {"code": 0, "message": "目录不存在"}
    
    try:
        # 获取目录下的所有文件
        files = [f for f in os.listdir(msglist_dir) if os.path.isfile(os.path.join(msglist_dir, f))]
        
        # 删除目录下的所有文件
        for file in files:
            file_path = os.path.join(msglist_dir, file)
            os.remove(file_path)
        
        return {"code": 1, "message": f"成功删除 {len(files)} 个消息文件"}
    except Exception as e:
        logger.error(f"清空消息时出错: {e}")
        return {"code": 0, "message": f"清空失败: {str(e)}"}

@app.get("/get_online_member")
async def get_online_members():
    """获取在线成员信息"""
    try:
        if os.path.exists("online_member.json"):
            return FileResponse("online_member.json")
        else:
            return {"code": 0, "message": "在线成员信息文件不存在"}
    except Exception as e:
        logger.error(f"获取在线成员信息时出错: {e}")
        return {"code": 0, "message": f"获取失败: {str(e)}"}

@app.post("/post_live_msg")
async def post_message(request: MessageRequest):
    """发送直播消息"""
    try:
        # 发送消息
        result = post_live_msg(request.content)
        if result:
            return {"code": 1, "message": "发送成功"}
        else:
            return {"code": 0, "message": "发送失败"}
    except Exception as e:
        logger.error(f"发送消息时出错: {e}")
        return {"code": 0, "message": f"发送失败: {str(e)}"}

@app.post("/post_live_app_msg")
async def post_app_message(request: ReplyRequest):
    """回复评论消息"""
    try:
        # 构建 to_user_contact 结构
        to_user_contact = {
            "contact": request.contact,
            "enableComment": 1,
            "badgeInfo": {},
            "liveIdentity": 2,
            "liveContactExtInfo": "CAE=",
            "badgeInfos": [
                {
                    "badgeType": 2,
                    "badgeLevel": 0
                }
            ]
        }
        
        # 发送回复
        result = post_live_app_msg(to_user_contact, request.content)
        if result:
            return {"code": 1, "message": "回复成功"}
        else:
            return {"code": 0, "message": "回复失败"}
    except Exception as e:
        logger.error(f"回复消息时出错: {e}")
        return {"code": 0, "message": f"回复失败: {str(e)}"}

if __name__ == '__main__':
    t1 = None
    
    try:
        # 调用函数获取数据
        #data = hepler_merlin_mmdata()
        #logger.debug(data)
        # 调用函数发起请求
        #response = helper_mmdata()
        #logger.debug(response)

        retoken = getrcode()
        
        if not retoken:
            logger.error("获取二维码token失败，请检查网络连接")
            exit(1)
        
        rehttp = f'https://channels.weixin.qq.com/mobile/confirm_login.html?token={retoken}'
        logger.info(f'二维码链接: {rehttp}')

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(rehttp)
        qr.make(fit=True)
        
        # 保存为图片文件（推荐使用）
        try:
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save("qrcode.png")
            logger.info('=' * 60)
            logger.info('二维码已保存到 qrcode.png')
            logger.info('强烈建议：请打开 qrcode.png 图片文件进行扫码')
            logger.info('=' * 60)
        except Exception as e:
            logger.warning(f'保存二维码图片失败: {e}')
        
        # 在终端显示二维码（注意：终端显示可能变形，建议扫描图片）
        logger.info('终端显示的二维码（可能变形，建议扫描上方图片）：')
        qr.print_ascii(out=None, tty=False, invert=False)

        logger.info('请使用微信扫码登录！')
        logger.info('二维码有效期200秒，请尽快扫码')

        time.sleep(1)

        # 获取二维码以及前期一系列准备工作。
        if request_qrcode(retoken) and auth_data() and helper_upload_params() and check_live_status() and get_live_info() and join_live() and a_online_member():
            logger.info("加载成功，开启消息获取线程。获取实时弹幕消息。")
            t1 = Thread(target=getmsg)
            t1.daemon = True  # 设置为守护线程，主进程退出时自动退出
            t1.start()
        else:
            logger.error("初始化失败，无法启动消息获取线程")

        #启动本地api服务
        logger.info("如需关闭服务，请输入ctrl+C来终止api服务进程，再输入exit退出监听。")
        uvicorn.run("webapi:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务...")
    finally:
        # 确保线程退出
        if t1 and t1.is_alive():
            logger.info("正在停止消息获取线程...")
            terminate_flag = True
            try:
                t1.join(timeout=5)  # 等待线程退出，最多等待5秒
                if t1.is_alive():
                    logger.warning("消息获取线程未能在超时时间内退出")
                else:
                    logger.info("消息获取线程已成功退出")
            except Exception as e:
                logger.error(f"停止线程时出错: {e}")
        logger.info("服务已完全关闭")