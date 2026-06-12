package com.at.interceptor;

import com.at.pojo.Result;
import com.at.utils.ApiResponseWriter;
import com.at.utils.JwtUtils;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

public class TokenInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(TokenInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        String jwt = request.getHeader("token");
        if (jwt == null || jwt.isEmpty()) {
            ApiResponseWriter.write(response, HttpServletResponse.SC_UNAUTHORIZED, Result.error(401, "未登录"));
            return false;
        }

        try {
            Claims claims = JwtUtils.parseJWT(jwt);
            request.setAttribute("role", claims.get("role"));
            request.setAttribute("userId", claims.get("id"));
            request.setAttribute("username", claims.get("username"));
        } catch (Exception exception) {
            log.warn("令牌无效: {}", exception.getMessage());
            ApiResponseWriter.write(response, HttpServletResponse.SC_UNAUTHORIZED, Result.error(401, "令牌无效"));
            return false;
        }

        return true;
    }
}
