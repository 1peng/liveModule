import os
import json
import threading
import time
from typing import List, Optional, Tuple

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), 'knowledge')
STATE_FILE = os.path.join(os.path.dirname(__file__), '.product_state.json')
LOCK_FILE = os.path.join(os.path.dirname(__file__), '.product_state.lock')

_state_lock = threading.Lock()
_current_state = None

def get_product_folders() -> List[str]:
    """获取 knowledge 文件夹下所有商品文件夹名称"""
    folders = []
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        for name in os.listdir(KNOWLEDGE_BASE_PATH):
            folder_path = os.path.join(KNOWLEDGE_BASE_PATH, name)
            if os.path.isdir(folder_path):
                folders.append(name)
    return sorted(folders)

def get_product_folder_path(product_name: str) -> str:
    """获取商品文件夹的完整路径"""
    return os.path.join(KNOWLEDGE_BASE_PATH, product_name)

def _acquire_file_lock(timeout: float = 5.0) -> bool:
    """获取文件锁"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.05)
    return False

def _release_file_lock():
    """释放文件锁"""
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass

def _read_state_file() -> dict:
    """读取状态文件"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {'current_index': 0, 'last_update': 0}

def _write_state_file(state: dict):
    """写入状态文件"""
    try:
        state['last_update'] = time.time()
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f)
    except Exception:
        pass

def get_current_product() -> Tuple[int, str]:
    """
    获取当前商品信息
    返回: (索引, 商品名称)
    """
    global _current_state
    
    with _state_lock:
        folders = get_product_folders()
        if not folders:
            return 0, ''
        
        if _acquire_file_lock():
            try:
                state = _read_state_file()
                current_index = state.get('current_index', 0)
                
                if current_index >= len(folders):
                    current_index = 0
                
                _current_state = {
                    'index': current_index,
                    'product': folders[current_index]
                }
            finally:
                _release_file_lock()
        else:
            if _current_state is None:
                _current_state = {'index': 0, 'product': folders[0] if folders else ''}
        
        return _current_state['index'], _current_state['product']

def switch_to_next_product() -> Tuple[int, str]:
    """
    切换到下一个商品
    返回: (新索引, 新商品名称)
    """
    global _current_state
    
    with _state_lock:
        folders = get_product_folders()
        if not folders:
            return 0, ''
        
        if _acquire_file_lock():
            try:
                state = _read_state_file()
                current_index = state.get('current_index', 0)
                
                current_index = (current_index + 1) % len(folders)
                
                state['current_index'] = current_index
                _write_state_file(state)
                
                _current_state = {
                    'index': current_index,
                    'product': folders[current_index]
                }
                
                print(f'[商品切换] 切换到商品: {folders[current_index]} (索引: {current_index})')
            finally:
                _release_file_lock()
        else:
            current_index = _current_state['index'] if _current_state else 0
            current_index = (current_index + 1) % len(folders)
            _current_state = {
                'index': current_index,
                'product': folders[current_index]
            }
        
        return _current_state['index'], _current_state['product']

def set_current_product(index: int) -> Tuple[int, str]:
    """
    设置当前商品索引
    返回: (索引, 商品名称)
    """
    global _current_state
    
    with _state_lock:
        folders = get_product_folders()
        if not folders:
            return 0, ''
        
        if index >= len(folders):
            index = 0
        
        if _acquire_file_lock():
            try:
                state = _read_state_file()
                state['current_index'] = index
                _write_state_file(state)
            finally:
                _release_file_lock()
        
        _current_state = {
            'index': index,
            'product': folders[index]
        }
        
        return index, folders[index]

def get_product_files(product_name: str) -> dict:
    """
    获取商品文件夹下的所有文件内容
    返回: {'knowledge.txt': 内容, 'msg.txt': 内容, ...}
    """
    folder_path = get_product_folder_path(product_name)
    files = {}
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[filename] = f.read()
                except Exception as e:
                    print(f'[警告] 读取文件失败 {filename}: {e}')
    
    return files

def get_knowledge_path(product_name: str) -> str:
    """获取商品的知识库文件路径"""
    return os.path.join(KNOWLEDGE_BASE_PATH, product_name, 'knowledge.txt')

def get_msg_path(product_name: str) -> str:
    """获取商品的发言内容文件路径"""
    return os.path.join(KNOWLEDGE_BASE_PATH, product_name, 'msg.txt')

def get_index_path(product_name: str) -> str:
    """获取商品的索引文件路径"""
    return os.path.join(KNOWLEDGE_BASE_PATH, product_name, 'index.txt')
