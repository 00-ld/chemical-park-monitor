package com.at.interceptor;

import com.at.utils.JwtUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.servlet.HandlerInterceptor;
import org.apache.http.HttpStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;



public class TokenInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(TokenInterceptor.class);


    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String url = request.getRequestURI();

        // 登录/注册接口放行
        if (url.contains("login") || url.contains("register")) {
            return true;
        }

        // 获取 token：优先从 Header，其次从 WebSocket 查询参数
        String jwt = request.getHeader("token");
        if (jwt == null || jwt.isEmpty()) {
            jwt = request.getParameter("token");
        }

        if (jwt == null || jwt.isEmpty()) {
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"未登录\"}");
            return false;
        }

        try {
            JwtUtils.parseJWT(jwt);
        } catch (Exception e) {
            log.warn("令牌无效: {}", e.getMessage());
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"令牌无效\"}");
            return false;
        }

        return true;
    }
}
