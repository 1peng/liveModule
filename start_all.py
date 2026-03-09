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
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def start_live_tts():
    """启动 live-tts 服务"""
    print('[启动] 正在启动 live-tts 服务...')
    return subprocess.Popen(
        [sys.executable, 'live-tts.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def start_auto_interaction():
    """启动 auto-interaction 服务"""
    print('[启动] 正在启动 auto-interaction 服务...')
    return subprocess.Popen(
        [sys.executable, 'auto-interaction.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def main():
    print('=' * 60)
    print('启动所有服务')
    print('=' * 60)
    
    processes = []
    
    try:
        # 启动 webapi
        webapi_process = start_webapi()
        processes.append(('webapi', webapi_process))
        
        # 等待 webapi 登录和初始化
        print('[等待] 等待 webapi 登录和初始化...')
        login_success = False
        init_failed = False
        wait_timeout = 300  # 5分钟超时
        start_time = time.time()
        
        while time.time() - start_time < wait_timeout:
            # 检查进程是否还在运行
            if webapi_process.poll() is not None:
                print(f'[错误] webapi 服务已停止，退出码: {webapi_process.returncode}')
                return
            
            # 读取输出
            try:
                output = webapi_process.stdout.readline()
                if output:
                    output_str = output.decode().strip()
                    print(f'[webapi] {output_str}')
                    
                    # 检查初始化失败
                    if '初始化失败，无法启动消息获取线程' in output_str:
                        init_failed = True
                        break
                    
                    # 检查登录成功的标志
                    if '加载成功，开启消息获取线程' in output_str:
                        login_success = True
                        break
            except:
                pass
            
            time.sleep(0.1)
        
        if init_failed:
            print('[错误] webapi 初始化失败，请检查直播间状态或权限')
            print('[提示] 可能的原因：')
            print('  1. 直播间不存在或已结束')
            print('  2. 没有权限加入该直播间')
            print('  3. 直播间状态异常')
            return
        
        if not login_success:
            print('[错误] webapi 登录或初始化超时，请检查网络或手动登录')
            return
        
        print('[成功] webapi 登录和初始化成功，继续启动其他服务...')
        time.sleep(2)
        
        # 启动 live-tts
        live_tts_process = start_live_tts()
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
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f'[错误] {name} 服务已停止，退出码: {process.returncode}')
                    return
            
            # 打印各服务的输出（跳过 webapi，因为已经在登录阶段打印过了）
            for name, process in processes:
                if name == 'webapi':
                    continue
                try:
                    output = process.stdout.readline()
                    if output:
                        print(f'[{name}] {output.decode().strip()}')
                except:
                    pass
            
            time.sleep(0.1)
            
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