import os
import re
import random
import asyncio
import sys
import signal
import requests
from datetime import datetime
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

# 文本处理工具函数
def remove_punctuation(text):
    """移除标点符号"""
    return re.sub(r'[\p{P}\p{S}]', '', text)

def randomize_sentence(template):
    """处理嵌套的 {} 和 | 语法，从多个选项中随机选择一个"""
    def process_template(s):
        result = ''
        stack = []
        current_part = ''

        for char in s:
            if char == '{':
                if len(stack) == 0:
                    result += current_part
                    current_part = ''
                stack.append('{')
            elif char == '}':
                if len(stack) == 1:
                    options = [option.strip() for option in current_part.split('|')]
                    result += random.choice(options)
                    current_part = ''
                stack.pop()
            else:
                current_part += char

        result += current_part
        return result

    return process_template(template)

def split_text_by_period(text, min_len=40, max_len=60):
    """按句号、感叹号、问号、逗号分割文本，并根据长度进行智能分段"""
    if not text.strip():
        return []

    # 按句号、感叹号、问号、逗号分割，保留分隔符
    import re
    raw_sentences = re.split(r'(?<=[。！？，])', text)
    raw_sentences = [s for s in raw_sentences if s.strip()]

    if not raw_sentences:
        return [text]

    result = []
    current = ''

    for sentence in raw_sentences:
        candidate = current + sentence

        # 如果加上当前句后仍小于最小长度，先累积
        if len(candidate) < min_len:
            current = candidate
            continue

        # 如果当前累积 + 当前句 超过最大长度，但 current 非空，则先输出 current
        if current and len(candidate) > max_len:
            # 尽量不让 current 太短
            if len(current) >= min_len:
                result.append(current)
                current = sentence
            else:
                # current 太短，只能硬切（或合并到下一段）
                result.append(candidate)
                current = ''
        else:
            # 候选长度在合理范围内，直接提交
            result.append(candidate)
            current = ''

    # 处理最后剩余的部分
    if current:
        result.append(current)

    return result

def split_by_period(text):
    """按句号分割文本并去除首尾空白"""
    parts = text.split('。')
    result = []
    for part in parts:
        stripped_part = part.strip()
        if stripped_part:  # 只处理非空部分
            result.append(stripped_part + '。')
    return result


# 获取当前时间文本
def get_current_time_text():
    """获取格式化的当前时间文本"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    
    # 如果秒数大于 40，则分钟进位
    if second > 40:
        minute += 1
        
        # 处理分钟进位到小时的情况
        if minute >= 60:
            minute = 0
            hour += 1
            
            # 处理小时进位（24点制）
            if hour >= 24:
                hour = 0
    
    # 格式化时间文本：如果是整点（分钟为0），则显示“xx点整”
    if minute == 0:
        return f"{hour}点整"
    else:
        return f"{hour}点{minute}分"

# 主函数：执行一次完整的流程
async def execute_cycle(session_id):
    global running
    try:
        current_index, current_product = product_state.get_current_product()
        if not current_product:
            print('[错误] 未找到商品文件夹')
            return
        
        print(f'[商品] 当前商品: {current_product} (索引: {current_index})')
        
        file_path = product_state.get_product_folder_path(current_product)
        index_path = product_state.get_index_path(current_product)
        
        if not os.path.exists(index_path):
            print(f'[错误] 索引文件不存在: {index_path}')
            return
        
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for item in os.listdir(file_path):
            if not running:
                break
            if item == 'index.lsp' or not item.endswith('.lsp'):
                continue
            
            model_path = os.path.join(file_path, item)
            if not os.path.isfile(model_path):
                continue

            model_name = item.replace('.lsp', '')
            with open(model_path, 'r', encoding='utf-8') as f:
                model_content = f.read()
            
            placeholder = re.compile(f'\\{{{model_name}\\}}', re.IGNORECASE)
            content = placeholder.sub(randomize_sentence(model_content), content)

        sentences = split_by_period(randomize_sentence(content))
 
        for item in sentences:
            if not running:
                break
            processed_item = item

            if 'CURRENT_TIME' in item:
                time_text = get_current_time_text()
                processed_item = processed_item.replace('CURRENT_TIME', time_text)
            print(processed_item)
            try:
                response = requests.post('http://localhost:8010/human', json={
                    'text': processed_item,
                    'type': 'echo',
                    'interrupt': False,
                    'sessionid': session_id
                })
                response.raise_for_status()
            except Exception as e:
                print(f'发送文本失败: {e}')

            await asyncio.sleep(1)

            try:
                res = requests.post('http://localhost:8010/get_remaining_duration', json={
                    'sessionid': session_id
                })
                res.raise_for_status()
                
                response_data = res.json()
                remaining_time = 0
                
                if isinstance(response_data, dict):
                    data = response_data.get('data')
                    if isinstance(data, dict):
                        remaining_time = data.get('data', 0)
                    elif isinstance(data, (int, float)):
                        remaining_time = data
                
                if remaining_time > 0:
                    wait_time = remaining_time - 20
                    if wait_time > 0:
                        for _ in range(int(wait_time * 10)):
                            if not running:
                                break
                            await asyncio.sleep(0.1)
            except Exception as e:
                print(f'获取剩余播放时间失败: {e}')
        
        if running:
            new_index, new_product = product_state.switch_to_next_product()
            print(f'[商品] 完成朗读，切换到下一个商品: {new_product}')
            
    except Exception as err:
        print(f'执行循环时出错: {err}')

# 无限循环执行
async def start_loop(session_id):
    global running
    # await execute_cycle(session_id)
    while running:
        await execute_cycle(session_id)
        if not running:
            break
        print('[INFO] 一轮执行完成，即将开始下一轮...')
        # 分段等待，以便快速响应停止信号
        for _ in range(10):
            if not running:
                break
            await asyncio.sleep(0.1)

# 主函数
async def main():
    global running
    # 解析命令行参数
    session_id = 0  # 默认值
    
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == '--sessionid' and i + 1 < len(args):
            session_id = int(args[i + 1])
            break
    
    print(f'[启动] 使用的 Session ID: {session_id}')
    try:
        await start_loop(session_id)
    except KeyboardInterrupt:
        print()
        print('[系统] 收到停止信号，正在退出...')
        running = False
    
    print('[系统] live-tts 脚本已停止')

if __name__ == '__main__':
    asyncio.run(main())
