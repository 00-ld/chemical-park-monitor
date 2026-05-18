package com.at.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.util.Date;
import java.util.Map;

public class JwtUtils {

    // 安全密钥（长度满足HS256要求）
    private static final String SECRET_KEY = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFG";
    private static final long EXPIRE = 1000 * 60 * 60 * 24;

    // 生成密钥（直接返回，不声明类型）
    private static Object getSigningKey() {
        return Keys.hmacShaKeyFor(SECRET_KEY.getBytes());
    }

    // 生成JWT令牌
    public static String generateJwt(Map<String, Object> claims) {
        return Jwts.builder()
                .addClaims(claims)
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRE))
                .signWith((java.security.Key) getSigningKey())
                .compact();
    }

    // 解析JWT令牌
    public static Claims parseJWT(String jwt) {
        return Jwts.parserBuilder()
                .setSigningKey((java.security.Key) getSigningKey())
                .build()
                .parseClaimsJws(jwt)
                .getBody();
    }
}