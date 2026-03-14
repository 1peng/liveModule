#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
import os

def start_webapi():
    """启动 webapi 服务"""
    print('[启动] 正在启动 webapi 服务...')
    return subprocess.Popen(
        [sys.executable, 'webapi.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

def start_live_tts(session_id):
    """启动 live-tts 服务"""
    print('[启动] 正在启动 live-tts 服务...')
    return subprocess.Popen(
        [sys.executable, 'live-tts.py', '--sessionid', str(session_id)],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

def start_auto_interaction():
    """启动 auto-interaction 服务"""
    print('[启动] 正在启动 auto-interaction 服务...')
    return subprocess.Popen(
        [sys.executable, 'auto-interaction.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

def main():
    print('=' * 60)
    print('启动所有服务')
    print('=' * 60)
    
    # 解析命令行参数
    session_id = None
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == '--sessionid' and i + 1 < len(args):
            session_id = int(args[i + 1])
            break
    
    if session_id:
        print(f'[参数] 使用 Session ID: {session_id}')
    else:
        # 交互式输入 sessionid
        while True:
            try:
                user_input = input('[输入] 请输入 Session ID: ').strip()
                if user_input:
                    session_id = int(user_input)
                    print(f'[参数] 使用 Session ID: {session_id}')
                    break
                else:
                    print('[提示] 未输入 Session ID，退出启动')
                    sys.exit(0)
            except ValueError:
                print('[错误] 请输入有效的数字')
            except KeyboardInterrupt:
                print()
                print('[提示] 已取消启动')
                sys.exit(0)
    
    processes = []
    
    try:
        # 启动 webapi
        webapi_process = start_webapi()
        processes.append(('webapi', webapi_process))
        
        # 等待 webapi 登录和初始化
        print('[等待] 等待 webapi 登录和初始化...')
        print('[提示] 请在终端中查看二维码并扫码登录')
        print('[提示] 登录成功后，其他服务将自动启动')
        
        # 等待 30 秒，让 webapi 服务有足够的时间启动、显示二维码并完成登录
        for i in range(30):
            if webapi_process.poll() is not None:
                print(f'[错误] webapi 服务已停止，退出码: {webapi_process.returncode}')
                return
            time.sleep(1)
            print(f'[等待] 已等待 {i+1} 秒...')
        
        # 检查 webapi 服务是否还在运行
        if webapi_process.poll() is not None:
            print(f'[错误] webapi 服务已停止，退出码: {webapi_process.returncode}')
            return
        
        print('[成功] webapi 服务已启动，继续启动其他服务...')
        time.sleep(2)
        
        # 启动 live-tts
        live_tts_process = start_live_tts(session_id)
        processes.append(('live-tts', live_tts_process))
        time.sleep(2)
        
        # 启动 auto-interaction
        auto_interaction_process = start_auto_interaction()
        processes.append(('auto-interaction', auto_interaction_process))
        
        print('=' * 60)
        print('所有服务已启动')
        print('=' * 60)
        print('[提示] 按 Ctrl+C 停止所有服务')
        print()
        
        # 监控所有进程
        print('[监控] 开始监控所有服务...')
        print('[提示] 按 Ctrl+C 停止所有服务')
        print()
        
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f'[错误] {name} 服务已停止，退出码: {process.returncode}')
                    # 停止其他服务
                    for n, p in processes:
                        if p.poll() is None:
                            print(f'[停止] 停止 {n} 服务...')
                            try:
                                p.terminate()
                                p.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                print(f'[停止] {n} 服务未响应，强制终止...')
                                p.kill()
                                p.wait()
                    return
            
            # 简单的延迟，避免 CPU 占用过高
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print('[停止] 正在停止所有服务...')
        
        for name, process in processes:
            print(f'[停止] 停止 {name} 服务...')
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f'[停止] {name} 服务未响应，强制终止...')
                process.kill()
                process.wait()
        
        print('[停止] 所有服务已停止')
        print()

if __name__ == '__main__':
    main()