package com.at.controller;

import com.at.pojo.Result;
import com.at.pojo.login_register.User;
import com.at.service.LoginService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/user")
@CrossOrigin
public class LoginAndRegisterController {

    @Autowired
    private LoginService loginService;

    @PostMapping("/login")
    public ResponseEntity<Result> login(@Valid @RequestBody User user) {
        String token = loginService.login(user);
        if (token != null) {
            log.info("用户登录成功: {}", user.getUsername());
            return ResponseEntity.ok(Result.success(token));
        }
        log.warn("用户登录失败: {}", user.getUsername());
        return ResponseEntity.status(401).body(Result.error("用户名或密码错误"));
    }

    @PostMapping("/register")
    public ResponseEntity<Result> register(@Valid @RequestBody User user) {
        boolean b = loginService.register(user);
        if (b) {
            log.info("用户注册成功: {}", user.getUsername());
            return ResponseEntity.ok(Result.success());
        }
        log.warn("用户注册失败, 用户名已存在: {}", user.getUsername());
        return ResponseEntity.badRequest().body(Result.error("用户名已存在"));
    }
}
