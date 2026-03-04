import os
import re
import random
import asyncio
import sys
import requests
from datetime import datetime

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

# 获取当前时间文本
def get_current_time_text():
    """获取格式化的当前时间文本"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    
    # 如果秒数大于 50，则分钟进位
    if second > 50:
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
    try:
        # 1. 读取主模板文件
        file_path = os.path.join(os.path.dirname(__file__), 'data', '刀削面')
        index_path = os.path.join(file_path, 'index.txt')
        
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 2. 读取目录下的所有 .txt 文件，并替换占位符
        for item in os.listdir(file_path):
            if item == 'index.txt' or not item.endswith('.txt'):
                continue
            
            model_path = os.path.join(file_path, item)
            if not os.path.isfile(model_path):
                continue

            model_name = item.replace('.txt', '')
            with open(model_path, 'r', encoding='utf-8') as f:
                model_content = f.read()
            
            placeholder = re.compile(f'\\{{{model_name}\\}}', re.IGNORECASE)
            content = placeholder.sub(randomize_sentence(model_content), content)

        # 3. 处理文本：打乱并按句号分割
        sentences = split_text_by_period(randomize_sentence(content))
 
 
        # 4. 遍历每句话发送
        for item in sentences:
            processed_item = item

            # 替换时间占位符
            if 'CURRENT_TIME' in item:
                time_text = get_current_time_text()
                processed_item = processed_item.replace('CURRENT_TIME', time_text)
            print(processed_item)
            # 发送文本到本地服务 (使用传入的 sessionId)
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

            # 短暂延迟
            await asyncio.sleep(0.1)

            # 获取服务端剩余播放时间
            try:
                res = requests.post('http://localhost:8010/get_remaining_duration', json={
                    'sessionid': session_id
                })
                res.raise_for_status()
                
                # 等待播放完成
                response_data = res.json()
                remaining_time = 0
                
                # 处理不同的数据结构
                if isinstance(response_data, dict):
                    data = response_data.get('data')
                    if isinstance(data, dict):
                        remaining_time = data.get('data', 0)
                    elif isinstance(data, (int, float)):
                        remaining_time = data
                
                if remaining_time > 0:
                    await asyncio.sleep(remaining_time - 3000 if remaining_time > 3000 else 0)
            except Exception as e:
                print(f'获取剩余播放时间失败: {e}')
    except Exception as err:
        print(f'执行循环时出错: {err}')

# 无限循环执行
async def start_loop(session_id):
    # await execute_cycle(session_id)
    while True:
        await execute_cycle(session_id)
        print('[INFO] 一轮执行完成，即将开始下一轮...')
        await asyncio.sleep(1)

# 主函数
async def main():
    # 解析命令行参数
    session_id = 846307  # 默认值
    
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == '--sessionid' and i + 1 < len(args):
            session_id = int(args[i + 1])
            break
    
    print(f'[启动] 使用的 Session ID: {session_id}')
    await start_loop(session_id)

if __name__ == '__main__':
    asyncio.run(main())
