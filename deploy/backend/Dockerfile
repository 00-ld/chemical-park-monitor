FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

COPY chemical-backend-1.0.0.jar app.jar

# 以非特权用户运行，避免容器内 root 提权风险
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "app.jar"]
