package com.at.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.Map;
import java.util.UUID;

public class JwtUtils {

    private static final Logger LOGGER = LoggerFactory.getLogger(JwtUtils.class);
    private static final String SECRET = System.getenv("JWT_SECRET");
    private static final Key SIGNING_KEY;
    private static final long EXPIRE = 1000L * 60 * 60 * 24;

    static {
        if (SECRET != null && SECRET.length() >= 32) {
            SIGNING_KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
        } else {
            String randomKey = UUID.randomUUID().toString().replace("-", "")
                    + UUID.randomUUID().toString().replace("-", "");
            SIGNING_KEY = Keys.hmacShaKeyFor(randomKey.getBytes(StandardCharsets.UTF_8));
            LOGGER.warn("JWT_SECRET is not configured or is shorter than 32 characters. "
                    + "A random runtime secret was generated, so existing tokens become invalid after restart.");
        }
    }

    private JwtUtils() {
    }

    public static String generateJwt(Map<String, Object> claims) {
        return Jwts.builder()
                .addClaims(claims)
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRE))
                .signWith(SIGNING_KEY)
                .compact();
    }

    public static Claims parseJWT(String jwt) {
        return Jwts.parserBuilder()
                .setSigningKey(SIGNING_KEY)
                .build()
                .parseClaimsJws(jwt)
                .getBody();
    }
}
