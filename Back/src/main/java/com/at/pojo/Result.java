package com.at.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result {

    private Integer code;
    private String message;
    private Object data;
    private boolean ok;
    private long timestamp;
    private String requestId;

    public static Result success() {
        return build(200, "成功", null, true);
    }

    public static Result success(Object data) {
        return build(200, "成功", data, true);
    }

    public static Result error(String message) {
        return error(500, message);
    }

    public static Result error(Integer code, String message) {
        return build(code, message, null, false);
    }

    public static Result of(Integer code, String message, Object data) {
        return build(code, message, data, code == 200);
    }

    private static Result build(Integer code, String message, Object data, boolean ok) {
        return new Result(code, message, data, ok, Instant.now().toEpochMilli(), UUID.randomUUID().toString());
    }
}
