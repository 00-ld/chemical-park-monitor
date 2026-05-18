package com.at.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result {

    private Integer code;
    private String message;
    private Object data;
    private boolean ok;

    public static Result success() {
        return new Result(200, "成功", null, true);
    }

    public static Result success(Object data) {
        return new Result(200, "成功", data, true);
    }

    public static Result error(String msg) {
        return new Result(500, msg, null, false);
    }

    public static Result of(Integer code, String msg, Object data) {
        return new Result(code, msg, data, code == 200);
    }
}
