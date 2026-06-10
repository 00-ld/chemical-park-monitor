package com.at.config;

import com.at.interceptor.AdminAuthInterceptor;
import com.at.interceptor.TokenInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 注册 JWT 鉴权拦截器。
 *
 * <p>{@link TokenInterceptor}（order=1）负责认证：校验 token 并解析出身份信息（role/userId）。
 * {@link AdminAuthInterceptor}（order=2）负责鉴权：仅对写操作（增删改）接口要求 admin 角色。
 *
 * <p>设计原则：只读 GET 接口登录即可访问；写操作必须是管理员。先认证后鉴权，
 * 顺序由 order 保证。
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 1. 认证拦截器：拦截所有业务接口，精确放行登录/注册
        registry.addInterceptor(new TokenInterceptor())
                .addPathPatterns("/api/**")
                // 精确放行：仅登录与注册（不使用子串匹配，避免绕过）
                .excludePathPatterns(
                        "/api/user/login",
                        "/api/user/register"
                )
                .order(1);

        // 2. 管理员鉴权拦截器：仅挂载到写操作（增删改）接口
        registry.addInterceptor(new AdminAuthInterceptor())
                .addPathPatterns(
                        // 传感器写操作
                        "/api/sensor/add",
                        "/api/sensor/update",
                        "/api/sensor/delete",
                        // 气体类型写操作
                        "/api/gas/add",
                        "/api/gas/update",
                        "/api/gas/delete",
                        // 布局方案写操作
                        "/api/sensor-layout/save",
                        "/api/sensor-layout/delete/**",
                        // 预警历史写操作
                        "/api/history/add",
                        "/api/history/delete",
                        // 巡检记录写操作
                        "/api/analysis/delete/**",
                        // 小车写操作
                        "/api/car/setWarning",
                        "/api/car/resetStatus"
                )
                .order(2);
    }
}
