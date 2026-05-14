# PokeClaw Bridge

让 AI 通过局域网控制手机上的 PokeClaw，执行任何手机操作。

## 使用方法

### 1. 创建 GitHub 仓库
1. 打开 https://github.com/new
2. 仓库名填 `pokeclaw-bridge`（必须和这里一致，Actions 才能对上）
3. 选 Public
4. 点 Create repository

### 2. 上传所有文件
```bash
# 把这个目录里所有文件推上去
cd pokeclaw-bridge-build
git init
git add .
git commit -m "add build workflow"
git remote add origin https://github.com/你的用户名/pokeclaw-bridge.git
git push -u origin main
```

### 3. 等 APK
1. 推完后 GitHub 会自动开始编译
2. 打开你仓库的 Actions 页面，等绿色对勾 ✅
3. 点进最新一次 workflow → 下载 APK artifact
4. 解压得到 app-debug.apk

### 4. 装手机
1. 手机安装 app-debug.apk
2. 打开 PokeClaw → 设置 → 开启 ConfigServer
3. 记下屏幕上显示的 IP 地址（如 192.168.1.100:9527）

### 5. 从沙箱发指令
```bash
python3 pokeclaw_client.py --discover
python3 pokeclaw_client.py --host 192.168.1.100 "给张三发微信：下午开会"
```
