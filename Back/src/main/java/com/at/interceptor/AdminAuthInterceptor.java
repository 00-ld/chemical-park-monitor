package com.at.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 管理员鉴权拦截器（H-1 授权层）。
 *
 * <p>在 {@link TokenInterceptor} 完成认证（order=1）之后执行（order=2），
 * 仅挂载到写操作接口（增删改）。从 request attribute 读取由认证拦截器写入的
 * "role"，只有 admin 角色才放行，否则返回 403。只读 GET 接口不挂此拦截器，
 * 登录即可访问。
 */
public class AdminAuthInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(AdminAuthInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 预检请求直接放行（CORS）
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        Object role = request.getAttribute("role");
        if (role == null || !"admin".equals(role.toString())) {
            log.warn("非管理员尝试执行写操作: {} {}, role={}",
                    request.getMethod(), request.getRequestURI(), role);
            response.setStatus(403);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":403,\"message\":\"无权限\"}");
            return false;
        }
        return true;
    }
}
