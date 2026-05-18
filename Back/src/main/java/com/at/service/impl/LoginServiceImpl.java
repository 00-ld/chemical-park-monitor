package com.at.service.impl;

import com.at.mapper.LoginMapper;
import com.at.pojo.login_register.User;
import com.at.service.LoginService;
import com.at.utils.JwtUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class LoginServiceImpl implements LoginService {

    @Autowired
    private LoginMapper loginMapper;

    @Override
    public String login(User user) {
        User loginUser = loginMapper.getByUsernameAndPassword(user);
        if (loginUser == null) {
            log.warn("用户登录失败: {}", user.getUsername());
            return null;
        }
        Map<String, Object> map = new HashMap<>();
        map.put("username", loginUser.getUsername());
        map.put("id", loginUser.getId());
        String token = JwtUtils.generateJwt(map);
        log.info("用户登录成功: {}", user.getUsername());
        return token;
    }

    @Override
    public boolean register(User user) {
        User u = loginMapper.getByUsername(user.getUsername());
        if (u != null) {
            log.warn("用户注册失败, 用户名已存在: {}", user.getUsername());
            return false;
        }
        loginMapper.insert(user);
        log.info("用户注册成功: {}", user.getUsername());
        return true;
    }
}
