import time
import random
import json
import signal
import sys
import os
from urllib.request import Request, urlopen
from urllib.error import URLError
import arg_bot
import product_state

# 全局退出标志
running = True

def signal_handler(signum, frame):
    global running
    print()
    print('[系统] 收到停止信号，正在退出...')
    running = False

# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def load_msg_contents():
    """从当前商品文件夹加载发言内容"""
    _, current_product = product_state.get_current_product()
    if not current_product:
        return []
    
    msg_path = product_state.get_msg_path(current_product)
    if not os.path.exists(msg_path):
        print(f'[警告] 发言内容文件不存在: {msg_path}')
        return []
    
    try:
        with open(msg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return lines if lines else []
    except Exception as e:
        print(f'[错误] 读取发言内容失败: {e}')
        return []

msg_contents = load_msg_contents()

# 回复模板
reply_templates = [
    '您好，感谢您的留言，我们会尽快为您解答',
    '感谢您的关注，关于这个问题，我们的产品确实是这样的',
    '您好，您的问题很有价值，我们会认真考虑',
    '感谢您的支持，我们会继续努力提供更好的产品和服务',
    '您好，关于这个问题，我可以为您详细解答'
]

# 欢迎来到直播间相关的回复
welcome_replies = [
    '欢迎 {nickname} 来到直播间！',
    '热烈欢迎 {nickname} 加入我们！',
    '欢迎 {nickname}，很高兴您能来！',
    '{nickname} 来了，欢迎欢迎！',
    '欢迎 {nickname} 来到我们的直播间，希望您喜欢这里！'
]
# 关注主播相关的回复
follow_replies = [
    '谢谢 {nickname} 的关注！',
    '感谢 {nickname} 的关注！'
]

# 直播间点赞的回复
like_replies = [
    '谢谢 {nickname} 的点赞！',
    '感谢 {nickname} 的点赞！'
]

# 顺序获取发言内容
msg_index = 0
def get_send_msg():
    global msg_index, msg_contents
    if not msg_contents:
        msg_contents = load_msg_contents()
        if not msg_contents:
            return ''
    content = msg_contents[msg_index]
    msg_index = (msg_index + 1) % len(msg_contents)
    print(f'[发言] {content}')
    return content

# 随机获取回复模板
def get_random_reply():
    index = random.randint(0, len(reply_templates) - 1)
    return reply_templates[index]

# 发送POST请求
def post_request(url, data, headers):
    try:
        req = Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except URLError as e:
        raise Exception(f'网络请求失败: {e}')
    except KeyboardInterrupt:
        raise
    except Exception as e:
        raise Exception(f'请求处理失败: {e}')

# 发送GET请求
def get_request(url):
    try:
        req = Request(url)
        with urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except URLError as e:
        raise Exception(f'网络请求失败: {e}')
    except KeyboardInterrupt:
        raise
    except Exception as e:
        raise Exception(f'请求处理失败: {e}')

# 调用发言接口
def send_msg():
    try:
        content = get_send_msg()
        
        response = post_request('http://localhost:8000/post_live_msg', {
            'content': content
        }, {
            'Content-Type': 'application/json'
        })
        
        print(f'[发言接口] 调用成功: {response}')
    except KeyboardInterrupt:
        raise
    except Exception as error:
        print(f'[发言接口] 调用失败: {error}')

# 获取用户留言列表并回复
def check_and_reply_comments():
    try:
        # 获取用户留言列表
        response = get_request('http://localhost:8000/getmsg')
        
        # 处理返回的数据结构
        comments = response.get('data', [])
        
        for comment in comments:
            # 检查badgeType是否为5
            has_badge_type_5 = False
            if 'badge_infos' in comment:
                for badge in comment['badge_infos']:
                    if badge.get('badgeType') == 5:
                        has_badge_type_5 = True
                        break
            
            if not has_badge_type_5:
                print(f'[回复] 用户: {comment.get("nickname", "")}, 内容: {comment.get("content", "")}')
                
                # 准备回复内容
                reply_content = ''
                if comment.get('msgType') == 10005:
                    template = welcome_replies[random.randint(0, len(welcome_replies) - 1)]
                    reply_content = template.replace('{nickname}', comment.get('nickname', ''))
                elif comment.get('msgType') == 20078:
                    template = follow_replies[random.randint(0, len(follow_replies) - 1)]
                    reply_content = template.replace('{nickname}', comment.get('nickname', ''))
                elif comment.get('msgType') == 20006:
                    template = like_replies[random.randint(0, len(like_replies) - 1)]
                    reply_content = template.replace('{nickname}', comment.get('nickname', ''))
                else:
                    # 普通回复
                    # 普通回复 - 使用 RAG 智能回复
                    user_question = comment.get('content', '')
                    try:
                        reply_content, _ = arg_bot.rag_chat_logic(user_question)
                        if reply_content.startswith('❌') or reply_content.startswith('⚠️'):
                            reply_content = get_random_reply()
                    except Exception as e:
                        print(f'[RAG回复] 调用失败: {e}')
                        reply_content = get_random_reply()
                
                # 回复评论的接口
                reply_response = post_request('http://localhost:8000/post_live_app_msg', {
                    'content': reply_content,
                    'contact': comment.get('contact')
                }, {
                    'Content-Type': 'application/json'
                })
                
                print(f'[回复接口] 调用成功: {reply_response}')
            else:
                # print(f'[跳过] 用户: {comment.get("nickname", "")}, 内容: {comment.get("content", "")} (badgeType为5)')
                pass
    except KeyboardInterrupt:
        raise
    except Exception as error:
        print(f'[留言列表/回复] 调用失败: {error}')

# 20秒执行一轮发表留言，每3秒发表一次
def start_msg_cycle():
    global running, msg_contents, msg_index
    last_product = None
    while running:
        _, current_product = product_state.get_current_product()
        if current_product != last_product:
            print(f'[商品] 检测到商品切换: {last_product} -> {current_product}')
            msg_contents = load_msg_contents()
            msg_index = 0
            last_product = current_product
        
        if not msg_contents:
            print('[系统] 发言内容为空，等待10秒后重试...')
            for _ in range(100):
                if not running:
                    break
                time.sleep(0.1)
            continue
        
        print('[系统] 开始新一轮发言')
        
        for i in range(len(msg_contents)):
            if not running:
                break
            send_msg()
            
            if i < len(msg_contents) - 1:
                for _ in range(50):
                    if not running:
                        break
                    time.sleep(0.1)
        
        if not running:
            break
        
        print('[系统] 本轮发言结束，等待20秒后开始下一轮')
        for _ in range(200):
            if not running:
                break
            time.sleep(0.1)

# 定时检查并回复评论
def periodic_check():
    global running
    last_product = None
    while running:
        _, current_product = product_state.get_current_product()
        if current_product != last_product:
            print(f'[RAG] 检测到商品切换: {last_product} -> {current_product}')
            if arg_bot.GLOBAL_TEXT2VEC is not None:
                arg_bot.check_and_switch_product_index(arg_bot.GLOBAL_TEXT2VEC, arg_bot.embed_dim)
            last_product = current_product
        
        check_and_reply_comments()
        for _ in range(30):
            if not running:
                break
            time.sleep(0.1)

# 主函数
if __name__ == '__main__':
    print('[系统] 自动交互脚本已启动，每3秒执行一次发言和评论回复')
    
    # 初始化 RAG 系统
    print('[系统] 正在初始化 RAG 智能回复系统...')
    try:
        # 1. 加载本地向量模型
        embed_model, embed_dim = arg_bot.load_local_embedding_model(arg_bot.LOCAL_EMBED_MODEL_PATH, arg_bot.DEVICE)
        arg_bot.embed_dim = embed_dim
        
        # 封装向量化函数
        def text2vec(text: str):
            return embed_model.encode(text, convert_to_numpy=True, normalize_embeddings=True).astype('float32')
        
        arg_bot.GLOBAL_TEXT2VEC = text2vec
        
        # 2. 连接云端 LLM
        arg_bot.GLOBAL_LLM_CLIENT = arg_bot.load_cloud_llm_client(
            arg_bot.DASHSCOPE_API_KEY, 
            arg_bot.DASHSCOPE_BASE_URL, 
            arg_bot.LLM_MODEL_ONLINE
        )
        
        # 3. 构建/加载索引
        arg_bot.build_or_load_index(arg_bot.GLOBAL_TEXT2VEC, embed_dim)
        
        print('[系统] RAG 智能回复系统初始化完成')
    except Exception as e:
        print(f'[系统] RAG 初始化失败: {e}')
        print('[系统] 将使用随机模板回复')
    
    # 初始执行一次回复检查
    check_and_reply_comments()
    
    # 创建线程执行循环任务
    import threading
    msg_thread = threading.Thread(target=start_msg_cycle)
    check_thread = threading.Thread(target=periodic_check)
    
    msg_thread.daemon = False
    check_thread.daemon = False
    
    msg_thread.start()
    check_thread.start()
    
    # 主线程保持运行，直到收到停止信号
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print('[系统] 收到停止信号，正在退出...')
        running = False
    
    # 等待线程结束
    msg_thread.join(timeout=5)
    check_thread.join(timeout=5)
    
    print('[系统] 自动交互脚本已停止')
