package com.at.interceptor;

import com.at.pojo.Result;
import com.at.utils.ApiResponseWriter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

public class AdminAuthInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(AdminAuthInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        Object role = request.getAttribute("role");
        if (role == null || !"admin".equals(role.toString())) {
            log.warn("非管理员尝试执行写操作 {} {}, role={}", request.getMethod(), request.getRequestURI(), role);
            ApiResponseWriter.write(response, HttpServletResponse.SC_FORBIDDEN, Result.error(403, "无权限"));
            return false;
        }
        return true;
    }
}
