# 登录报错排查与启动顺序

## 常见原因

1. Java 后端没有启动。前端开发服务器只负责页面，登录接口需要后端监听 `8081`。
2. 后端连错数据库。Docker 部署使用 `mysql:3306`，本机 Maven 启动通常使用 `127.0.0.1:3306`。
3. 数据库未初始化。`chemical` 库中必须存在 `user` 表和默认管理员账号。
4. MySQL 密码未传给后端。本机运行时需要设置 `SPRING_DATASOURCE_PASSWORD` 或 `DB_PASSWORD`。
5. YOLO 服务未启动或 Java 后端未配置 `ANALYSIS_SERVICE_URL`，会导致人员识别接口返回 503 或 500。

## 启动顺序

### 推荐：一键启动

在项目根目录双击或通过终端运行：

```bat
startup.bat
```

脚本会按顺序检查或启动：

1. MySQL 数据库：优先复用本机 `3306`，未监听时通过 Docker Compose 启动 `chemical-mysql`。
2. Python 算法扩散服务：`127.0.0.1:8000`。
3. YOLO 人员识别服务：`127.0.0.1:8001`。
4. Java 后端：`127.0.0.1:8081`。
5. 前端开发服务：`127.0.0.1:5173`。

如果修改了任一服务的启动命令、端口、环境变量、数据库初始化方式或启动顺序，必须同步更新根目录 `startup.bat`。

以下步骤用于手动排查。

### 1. 启动并初始化 MySQL

确认本机 MySQL 正在监听 `3306`：

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 3306 }
```

初始化数据库：

```powershell
cd C:\Users\colorful\Desktop\localhost
mysql --protocol=TCP --host=127.0.0.1 --port=3306 --user=root --password < deploy\mysql\init.sql
```

初始化脚本会创建 `chemical` 数据库、`user` 表，并写入默认开发账号：

```text
账号：admin
密码：123456
```

### 2. 启动 YOLO 识别服务

```powershell
cd C:\Users\colorful\Desktop\localhost\algorithm
python -m uvicorn polo:app --host 127.0.0.1 --port 8001
```

验证服务：

```powershell
Invoke-WebRequest http://127.0.0.1:8001/docs
```

### 3. 启动 Java 后端

```powershell
cd C:\Users\colorful\Desktop\localhost\backend
$env:SPRING_PROFILES_ACTIVE="local"
$env:SPRING_DATASOURCE_PASSWORD="你的 MySQL root 密码"
$env:ANALYSIS_SERVICE_URL="http://127.0.0.1:8001/api/analysis/person"
$env:INSPECTION_DEFAULT_LOCATION="核心作业区 A7"
mvn.cmd spring-boot:run
```

启动成功后应能看到 `8081` 端口：

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8081 }
```

### 4. 启动前端

```powershell
cd C:\Users\colorful\Desktop\localhost\frontend
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173/index.html
```

## 验证登录接口

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8081/api/user/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"123456"}'
```

如果返回 `code: 200` 且 `data` 中有 token，说明后端、数据库和默认账号都正常。

## 验证 YOLO 代理接口

先登录拿 token，再把图片通过 Java 后端代理到 YOLO 服务：

```powershell
$login = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8081/api/user/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"123456"}'

$token = $login.data
curl.exe -X POST http://127.0.0.1:8081/api/analysis/person `
  -H "token: $token" `
  -F "file=@yolo_test_person_like.jpg;type=image/jpeg"
```

成功时接口返回 `code: 200`，`data.status` 为 `success`，并带有 `image_base64` 识别结果图。
