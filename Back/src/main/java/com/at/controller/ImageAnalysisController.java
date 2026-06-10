package com.at.controller;

import com.alibaba.fastjson.JSONObject;
import com.at.mapper.InspectRecordMapper;
import com.at.pojo.InspectRecord;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import jakarta.annotation.Resource;
import java.io.IOException;
import java.time.LocalDateTime;

@Slf4j
@RestController
@RequestMapping("/api/analysis")
public class ImageAnalysisController {

    @Resource
    private InspectRecordMapper inspectRecordMapper;

    // 上传文件限制：仅允许常见图片类型，最大 10MB
    private static final long MAX_FILE_SIZE = 10L * 1024 * 1024;
    private static final java.util.Set<String> ALLOWED_CONTENT_TYPES =
            java.util.Set.of("image/jpeg", "image/png", "image/jpg");
    private static final java.util.Set<String> ALLOWED_EXTENSIONS =
            java.util.Set.of("jpg", "jpeg", "png");

    // 算法服务共享密钥，与 Python 服务的 ALGORITHM_API_KEY 一致
    private static final String ALGORITHM_API_KEY = System.getenv("ALGORITHM_API_KEY");

    @PostMapping("/person")
    public ResponseEntity<String> analyzePerson(@RequestParam("file") MultipartFile file) {
        // ===== 上传文件校验 =====
        if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest().body("{\"status\":\"error\",\"message\":\"未上传文件\"}");
        }
        if (file.getSize() > MAX_FILE_SIZE) {
            return ResponseEntity.status(413).body("{\"status\":\"error\",\"message\":\"文件过大，最大 10MB\"}");
        }
        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType.toLowerCase())) {
            return ResponseEntity.badRequest().body("{\"status\":\"error\",\"message\":\"仅支持 JPG/PNG 图片\"}");
        }
        // 文件名安全化：去除路径分隔符，仅保留基础名，并校验扩展名
        String rawName = file.getOriginalFilename();
        String safeName = (rawName == null) ? "upload"
                : rawName.replaceAll(".*[\\\\/]", "").replaceAll("[^A-Za-z0-9._-]", "_");
        int dot = safeName.lastIndexOf('.');
        String ext = (dot >= 0) ? safeName.substring(dot + 1).toLowerCase() : "";
        if (!ALLOWED_EXTENSIONS.contains(ext)) {
            return ResponseEntity.badRequest().body("{\"status\":\"error\",\"message\":\"文件扩展名不合法\"}");
        }
        final String filename = safeName;

        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(10000);
            factory.setReadTimeout(60000);

            RestTemplate restTemplate = new RestTemplate(factory);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            // 携带算法服务密钥（内网鉴权）
            if (ALGORITHM_API_KEY != null && !ALGORITHM_API_KEY.isEmpty()) {
                headers.set("X-API-Key", ALGORITHM_API_KEY);
            }

            ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return filename;
                }
            };

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", fileResource);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
            String pythonUrl = "http://localhost:8001/api/analysis/person";
            String result = restTemplate.postForObject(pythonUrl, requestEntity, String.class);

            log.info("人员分析请求完成, 文件名: {}", filename);

            try {
                JSONObject json = JSONObject.parseObject(result);
                if ("success".equals(json.getString("status"))) {
                    InspectRecord record = new InspectRecord();
                    record.setCreateTime(LocalDateTime.now());
                    record.setPersonCount(json.getInteger("count"));
                    record.setLocation("核心作业区-A7");
                    record.setStatus(json.getInteger("count") > 5 ? "异常" : "正常");
                    record.setImageBase64(json.getString("image_base64"));
                    record.setAnalysisTime(0);
                    inspectRecordMapper.insert(record);
                    log.info("巡检记录已保存, 人数: {}", json.getInteger("count"));
                }
            } catch (Exception e) {
                log.error("保存巡检记录失败", e);
            }

            return ResponseEntity.ok(result);
        } catch (IOException e) {
            log.error("文件读取失败: {}", filename, e);
            return ResponseEntity.status(500).body("{\"status\":\"error\",\"message\":\"文件读取失败\"}");
        } catch (Exception e) {
            log.error("算法服务异常", e);
            return ResponseEntity.status(500).body("{\"status\":\"error\",\"message\":\"算法服务异常\"}");
        }
    }

    @GetMapping("/list")
    public ResponseEntity<?> getList() {
        log.info("查询巡检记录列表");
        return ResponseEntity.ok(inspectRecordMapper.listAll());
    }

    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> delete(@PathVariable Long id) {
        inspectRecordMapper.deleteById(id);
        log.info("删除巡检记录, id: {}", id);
        return ResponseEntity.ok("success");
    }
}
