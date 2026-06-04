# 化工园区智能监测系统 - 部署指南

## 架构

```
浏览器 → Nginx(80) → 前端(Vue 3)
                    → /api/* → Java后端(8081)
                    → /algorithm-api/* → Python算法(8000)
         MySQL(3306) ← Java后端
```

## 一、购买阿里云服务器

1. 登录 [阿里云](https://www.aliyun.com/)
2. 进入 **轻量应用服务器**（新人 99 元/年起）
3. 选择：
   - 地域：就近选择（如华东 1 杭州）
   - 镜像：**Ubuntu 22.04** 或 **Debian 12**
   - 规格：建议 **2核4G** 起步（Python + PyTorch 比较吃内存）
4. 安全组开放端口：**80**、**22**（SSH）
5. 记下公网 IP 和 root 密码

## 二、连接服务器

Windows 用户可以用 PowerShell 或 CMD：

```bash
ssh root@你的公网IP
```

## 三、安装 Docker

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker
systemctl enable docker && systemctl start docker

# 验证
docker --version
docker compose version
```

## 四、上传项目文件

在你的 Windows 电脑上，把 `deploy/` 目录和需要的文件上传到服务器：

```bash
# 方式1: 用 scp 上传（在 Windows 终端执行）
scp -r C:/Users/colorful/Desktop/localhost/deploy root@你的公网IP:/opt/chemical-park
scp -r C:/Users/colorful/Desktop/localhost/Manage/dist root@/opt/chemical-park/manage-dist
scp C:/Users/colorful/Desktop/localhost/Back/target/chemical-backend-1.0.0.jar root@:/opt/chemical-park/deploy/backend/
scp -r C:/Users/colorful/Desktop/localhost/chemical-park-monitor/python root@:/opt/chemical-park/algorithm
```

或者用 **WinSCP** 图形化工具拖拽上传。

## 五、在服务器上调整目录结构

```bash
cd /opt/chemical-park

# 确认文件结构
ls -la
# 应该看到: deploy/  manage-dist/  algorithm/

# 创建 backend jar 的位置
cp deploy/backend/chemical-backend-1.0.0.jar deploy/backend/

# 修改 docker-compose.yml 中的路径（如果需要）
```

## 六、启动服务

```bash
cd /opt/chemical-park/deploy

# 构建并启动所有服务
docker compose up -d --build

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f
```

## 七、验证

```bash
# 检查各服务状态
docker compose ps

# 测试前端
curl http://localhost/

# 测试后端 API
curl http://localhost/api/

# 测试算法服务
curl http://localhost/algorithm-api/
```

浏览器打开 `http://你的公网IP` 即可访问。

## 八、常用维护命令

```bash
# 查看日志
docker compose logs -f backend     # Java 后端日志
docker compose logs -f algorithm   # Python 算法日志
docker compose logs -f nginx       # Nginx 日志

# 重启单个服务
docker compose restart backend

# 停止所有服务
docker compose down

# 重新构建并启动
docker compose up -d --build

# 进入容器调试
docker exec -it chemical-backend bash
docker exec -it chemical-algorithm bash
```

## 九、安全建议

1. **修改数据库密码**: 编辑 `deploy/.env`，修改 `MYSQL_ROOT_PASSWORD`
2. **配置防火墙**: 只开放 80 和 22 端口
3. **后续加域名**: 购买域名后配置 DNS 解析到服务器 IP

## 十、费用估算

| 项目 | 费用 |
|------|------|
| 阿里云轻量服务器 2核4G | ~99-200 元/年（新人价） |
| 域名（可选） | ~30-60 元/年 |
| 流量 | 轻量服务器一般包含流量包 |

总计约 **100-260 元/年**，非常经济。
