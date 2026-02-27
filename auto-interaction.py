import time
import random
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# 发言内容库
msg_contents = [
    '当季新货山楂干，无熏无硫，没有任何添加。',
    '煮水，煲汤，炖肉，煮花茶，做山楂饼，山楂糕，山楂汁等吃法多种多样。',
    '七天无理由，运费险给您保驾护航，放心拍，放心带。',
    '今天福利价格10块9半斤，16块9一斤，先到先得。',
    '去籽无核，品质保证。'
]

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
    global msg_index
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
    while True:
        print('[系统] 开始新一轮发言')
        
        # 按顺序发表所有留言
        for i in range(len(msg_contents)):
            send_msg()
            
            # 除了最后一条，每条留言后等待3秒
            if i < len(msg_contents) - 1:
                time.sleep(5)
        
        print('[系统] 本轮发言结束，等待20秒后开始下一轮')
        time.sleep(20)

# 定时检查并回复评论
def periodic_check():
    while True:
        check_and_reply_comments()
        time.sleep(3)

# 主函数
if __name__ == '__main__':
    print('[系统] 自动交互脚本已启动，每3秒执行一次发言和评论回复')
    
    # 初始执行一次回复检查
    check_and_reply_comments()
    
    # 创建线程执行循环任务
    import threading
    msg_thread = threading.Thread(target=start_msg_cycle)
    check_thread = threading.Thread(target=periodic_check)
    
    msg_thread.daemon = True
    check_thread.daemon = True
    
    msg_thread.start()
    check_thread.start()
    
    # 主线程保持运行
    while True:
        time.sleep(1)
