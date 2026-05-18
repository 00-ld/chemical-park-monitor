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
//1. 获取请求的url
        String url = request.getRequestURI();

        //2. 判断请求url中是否包含login，如果包含，说明是登录操作，放行。
        if (url.contains("login")) {
            log.info("登录操作，放行...");
            return true;
        }

        //3. 获取请求头中的令牌（token）。
        String jwt = request.getHeader("token");

        //4. 判断令牌是否存在，如果不存在，返回错误结果（未登录）。
        if(jwt == null || jwt.isEmpty()) {
            log.info("请求头token为空，返回未登录错误信息...");
            response.setStatus(401);
            return  false;
        }

        //5. 解析token，如果解析失败，返回错误结果（未登录）。
        try {
            JwtUtils.parseJWT(jwt);
        } catch (Exception e) {
            e.printStackTrace();
            log.info("解析令牌失败，返回未登录错误信息...");
            response.setStatus(HttpStatus.SC_UNAUTHORIZED);//401
            return  false;
        }

        //6. 放行。
        log.info("令牌合法，放行...");
        return true;
    }
}
