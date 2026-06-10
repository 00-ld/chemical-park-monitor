package com.at.controller;

import com.at.pojo.Result;
import com.at.pojo.login_register.User;
import com.at.service.LoginService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@RestController
@RequestMapping("/api/user")
public class LoginAndRegisterController {

    @Autowired
    private LoginService loginService;

    // 简易限流：IP → {次数, 窗口起始时间}
    private final ConcurrentHashMap<String, int[]> registerAttempts = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, int[]> loginAttempts = new ConcurrentHashMap<>();
    private static final int MAX_REGISTER_PER_MINUTE = 5;
    private static final int MAX_LOGIN_PER_MINUTE = 10;

    /**
     * 固定窗口限流：同一 key 在 1 分钟窗口内累加次数，超过 limit 返回 true（已超限）。
     */
    private boolean isRateLimited(ConcurrentHashMap<String, int[]> attempts, String key, int limit) {
        long now = System.currentTimeMillis();
        int[] record = attempts.compute(key, (k, v) -> {
            if (v == null || now - v[1] > 60_000) {
                return new int[]{1, (int) now};
            }
            v[0]++;
            return v;
        });
        return record[0] > limit;
    }

    @PostMapping("/login")
    public ResponseEntity<Result> login(@Valid @RequestBody User user, HttpServletRequest request) {
        // 限流：同一 IP 每分钟最多登录尝试 10 次，防止暴力破解
        String ip = request.getRemoteAddr();
        if (isRateLimited(loginAttempts, ip, MAX_LOGIN_PER_MINUTE)) {
            log.warn("登录频率过高，IP: {}", ip);
            return ResponseEntity.status(429).body(Result.error("登录过于频繁，请稍后再试"));
        }

        String token = loginService.login(user);
        if (token != null) {
            log.info("用户登录成功: {}", user.getUsername());
            return ResponseEntity.ok(Result.success(token));
        }
        log.warn("用户登录失败: {}", user.getUsername());
        return ResponseEntity.status(401).body(Result.error("用户名或密码错误"));
    }

    @PostMapping("/register")
    public ResponseEntity<Result> register(@Valid @RequestBody User user, HttpServletRequest request) {
        // 限流：每个 IP 每分钟最多注册 5 次
        String ip = request.getRemoteAddr();
        if (isRateLimited(registerAttempts, ip, MAX_REGISTER_PER_MINUTE)) {
            log.warn("注册频率过高，IP: {}", ip);
            return ResponseEntity.status(429).body(Result.error("注册过于频繁，请稍后再试"));
        }

        boolean b = loginService.register(user);
        if (b) {
            log.info("用户注册成功: {}", user.getUsername());
            return ResponseEntity.ok(Result.success());
        }
        log.warn("用户注册失败, 用户名已存在: {}", user.getUsername());
        return ResponseEntity.badRequest().body(Result.error("用户名已存在"));
    }
}
