package com.at.interceptor;

import com.at.utils.JwtUtils;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.servlet.HandlerInterceptor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;



public class TokenInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(TokenInterceptor.class);


    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 预检请求直接放行（CORS）
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        // 登录/注册等白名单路径由 WebConfig.excludePathPatterns 精确放行，
        // 这里不再用 url.contains 做子串匹配，避免 /api/sensor/login-xxx 之类绕过。

        // 获取 token：仅从 Header 读取，不再支持查询参数回退（避免 token 出现在
        // URL/日志/Referer 中泄露；项目无 WebSocket 端点在用）。
        String jwt = request.getHeader("token");

        if (jwt == null || jwt.isEmpty()) {
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"未登录\"}");
            return false;
        }

        try {
            Claims claims = JwtUtils.parseJWT(jwt);
            // 解析成功后，将身份信息存入 request attribute，供后续鉴权拦截器使用
            request.setAttribute("role", claims.get("role"));
            request.setAttribute("userId", claims.get("id"));
            request.setAttribute("username", claims.get("username"));
        } catch (Exception e) {
            log.warn("令牌无效: {}", e.getMessage());
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"令牌无效\"}");
            return false;
        }

        return true;
    }
}
