# Backend Service

本目录存放 Java Spring Boot 后端服务，负责用户认证、业务数据管理、传感器与小车数据接口、告警记录、图片识别服务转发，以及对 Python 算法服务的受控调用。

## 技术栈

- Spring Boot 3.4
- JDK 21
- MyBatis
- MySQL
- JWT
- BCrypt 密码哈希

## 标准入口

- 应用入口：`src/main/java/com/at/ChemicalApplication.java`
- 配置文件：`src/main/resources/application.yml`
- MyBatis 映射：`src/main/resources/mapper/`
- 局部 SQL 资源：`src/main/resources/schema-*.sql`、`src/main/resources/init-sensor-db.sql`

## 运行方式

```bash
mvn spring-boot:run
```

打包：

```bash
mvn clean package -DskipTests
```

生成的 `target/` 目录和 `.jar` 构建产物不得提交到 GitHub。部署时将构建出的 `chemical-backend-1.0.0.jar` 放入 `deploy/backend/`。

## 配置要求

敏感配置必须来自环境变量或部署平台密钥，不得写死在代码中：

- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `JWT_SECRET`
- `ALGORITHM_API_KEY`
- `ANALYSIS_SERVICE_URL`
- `CORS_ALLOWED_ORIGINS`

本地临时配置文件不得提交。需要新增配置时，应优先在 `application.yml` 中使用 `${ENV_NAME:default}` 形式。

## 接口规范

后端接口统一返回 `Result` 外壳，字段应与项目统一 JSON 协议保持一致。新增接口不得直接返回数据库实体给前端，应通过 DTO、VO 或明确的响应结构输出。

## 目录维护规则

- `controller/` 只处理 HTTP 入参、鉴权结果和响应封装。
- `service/` 和 `service/impl/` 承载业务流程编排。
- `mapper/` 只负责数据库访问，不写页面逻辑和算法逻辑。
- `pojo/` 保持字段命名清晰，避免同义重复字段。
- `utils/` 只放低耦合工具类，不放具体业务流程。

## 验证命令

```bash
mvn -q -DskipTests compile
```

涉及数据库脚本、统一响应协议、登录鉴权或算法转发时，应同步更新 `docs/api-reference.md`、`docs/development-guide.md` 或部署文档。
