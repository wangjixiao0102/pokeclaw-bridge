#!/usr/bin/env python3
"""
PokeClaw Bridge Client — 从沙箱控制手机

前提：PokeClaw 已打 patch、手机连 WiFi
用法：
  python3 pokeclaw_client.py --discover          # 扫描局域网找 PokeClaw
  python3 pokeclaw_client.py "给张三发微信：下午开会"
  python3 pokeclaw_client.py --mode chat "帮我查下今天天气"
  python3 pokeclaw_client.py --host 192.168.1.100 "打开淘宝"
"""

import sys
import json
import socket
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_PORT = 9527
SCAN_TIMEOUT = 0.5
API_PATH = "/api/task"

# ── 局域网扫描 ──────────────────────────────────────

def get_local_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def scan_host(ip, port, timeout=SCAN_TIMEOUT):
    """检测单个 IP 是否是 PokeClaw"""
    url = f"http://{ip}:{port}{API_PATH}"
    req = urllib.request.Request(url, data=b"{}", method="POST",
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return ip, resp.status
    except Exception:
        return None


def discover(subnet=None, port=DEFAULT_PORT):
    """扫描局域网找到 PokeClaw 设备"""
    if subnet is None:
        local_ip = get_local_ip()
        subnet = ".".join(local_ip.split(".")[:3])
    
    print(f"🔍 扫描 {subnet}.0/24 ...")
    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    
    found = []
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(scan_host, ip, port): ip for ip in ips}
        for f in as_completed(futures):
            result = f.result()
            if result:
                ip, status = result
                print(f"  ✅ 找到 PokeClaw: {ip}:{port}")
                found.append(ip)
    
    if not found:
        print("  ❌ 未发现 PokeClaw 设备")
        print("     确保手机已连 WiFi 且 PokeClaw ConfigServer 已启动")
    return found


# ── 发送任务 ────────────────────────────────────────

def send_task(host, port, task, mode="task", timeout=10):
    """向 PokeClaw 发送任务"""
    url = f"http://{host}:{port}{API_PATH}"
    payload = json.dumps({"task": task, "mode": mode}).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST",
        headers={"Content-Type": "application/json"})
    
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"code": -1, "message": f"HTTP {e.code}: {body[:200]}"}
    except urllib.error.URLError as e:
        return {"code": -1, "message": f"连接失败: {e.reason}"}
    except socket.timeout:
        return {"code": -1, "message": "请求超时"}


def check_status(host, port, timeout=10):
    """检查 PokeClaw 是否在线"""
    try:
        resp = send_task(host, port, "", mode="task")
        # 空 task 应返回错误，但证明服务器在运行
        return resp.get("code") is not None
    except Exception:
        return False


# ── CLI ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PokeClaw Bridge — 从沙箱控制手机",
        epilog="示例:\n"
               "  python3 pokeclaw_client.py --discover\n"
               "  python3 pokeclaw_client.py '发微信给张三：下午开会'\n"
               "  python3 pokeclaw_client.py --host 192.168.1.100 '打开淘宝'"
    )
    parser.add_argument("task", nargs="?", help="要执行的任务（自然语言）")
    parser.add_argument("--host", help="PokeClaw 设备 IP（不指定则自动发现）")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口（默认 {DEFAULT_PORT}）")
    parser.add_argument("--mode", choices=["task", "chat"], default="task",
                        help="task=自动化执行, chat=对话模式")
    parser.add_argument("--discover", action="store_true", help="扫描局域网")
    parser.add_argument("--subnet", help="指定扫描网段（如 192.168.1）")
    
    args = parser.parse_args()
    
    if args.discover:
        discover(args.subnet, args.port)
        return
    
    if not args.task:
        parser.print_help()
        return
    
    # 确定目标主机
    host = args.host
    if not host:
        found = discover(args.subnet, args.port)
        if not found:
            print("❌ 请用 --host 指定 IP")
            sys.exit(1)
        host = found[0]
        print()
    
    print(f"📤 发送到 {host}:{args.port}")
    print(f"   模式: {args.mode}")
    print(f"   任务: {args.task[:80]}{'...' if len(args.task) > 80 else ''}")
    print()
    
    result = send_task(host, args.port, args.task, mode=args.mode)
    
    if result.get("code") == 0:
        print(f"✅ 任务已接受 ({result.get('mode', 'task')} 模式)")
        print("   查看手机屏幕确认执行结果")
    else:
        print(f"❌ 错误: {result.get('message', '未知错误')} (code={result.get('code')})")


if __name__ == "__main__":
    main()
