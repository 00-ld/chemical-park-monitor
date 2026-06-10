package com.at.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.Map;
import java.util.UUID;

public class JwtUtils {

    // 从环境变量读取密钥；未设置时每次启动自动生成随机密钥（重启后旧 token 失效）
    private static final String SECRET = System.getenv("JWT_SECRET");
    private static final Key SIGNING_KEY;
    private static final long EXPIRE = 1000 * 60 * 60 * 24;

    static {
        if (SECRET != null && SECRET.length() >= 32) {
            SIGNING_KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
        } else {
            // 未配置 JWT_SECRET 时自动生成随机密钥
            String randomKey = UUID.randomUUID().toString().replace("-", "")
                    + UUID.randomUUID().toString().replace("-", "");
            SIGNING_KEY = Keys.hmacShaKeyFor(randomKey.getBytes(StandardCharsets.UTF_8));
            System.out.println("[JwtUtils] 警告: 未设置 JWT_SECRET 环境变量，已自动生成随机密钥。重启后旧 token 将失效。");
        }
    }

    // 生成JWT令牌
    public static String generateJwt(Map<String, Object> claims) {
        return Jwts.builder()
                .addClaims(claims)
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRE))
                .signWith(SIGNING_KEY)
                .compact();
    }

    // 解析JWT令牌
    public static Claims parseJWT(String jwt) {
        return Jwts.parserBuilder()
                .setSigningKey(SIGNING_KEY)
                .build()
                .parseClaimsJws(jwt)
                .getBody();
    }
}