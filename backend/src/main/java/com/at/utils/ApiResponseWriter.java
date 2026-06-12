package com.at.utils;

import com.at.pojo.Result;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class ApiResponseWriter {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private ApiResponseWriter() {
    }

    public static void write(HttpServletResponse response, int status, Result<?> result) throws IOException {
        response.setStatus(status);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(OBJECT_MAPPER.writeValueAsString(result));
    }
}
