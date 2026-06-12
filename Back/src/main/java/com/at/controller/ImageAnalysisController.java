package com.at.controller;

import com.alibaba.fastjson.JSONObject;
import com.at.mapper.InspectRecordMapper;
import com.at.pojo.InspectRecord;
import com.at.pojo.Result;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Set;

@Slf4j
@RestController
@RequestMapping("/api/analysis")
public class ImageAnalysisController {

    @Resource
    private InspectRecordMapper inspectRecordMapper;

    private static final long MAX_FILE_SIZE = 10L * 1024 * 1024;
    private static final Set<String> ALLOWED_CONTENT_TYPES = Set.of("image/jpeg", "image/png", "image/jpg");
    private static final Set<String> ALLOWED_EXTENSIONS = Set.of("jpg", "jpeg", "png");
    private static final String ALGORITHM_API_KEY = System.getenv("ALGORITHM_API_KEY");
    private static final String ANALYSIS_SERVICE_URL = System.getenv().getOrDefault(
            "ANALYSIS_SERVICE_URL",
            "http://localhost:8001/api/analysis/person"
    );

    @PostMapping("/person")
    public ResponseEntity<Result> analyzePerson(@RequestParam("file") MultipartFile file) {
        if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest().body(Result.error(400, "未上传文件"));
        }
        if (file.getSize() > MAX_FILE_SIZE) {
            return ResponseEntity.status(413).body(Result.error(413, "文件过大，最大 10MB"));
        }

        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType.toLowerCase())) {
            return ResponseEntity.badRequest().body(Result.error(400, "仅支持 JPG/PNG 图片"));
        }

        String filename = normalizeFilename(file.getOriginalFilename());
        if (!hasAllowedExtension(filename)) {
            return ResponseEntity.badRequest().body(Result.error(400, "文件扩展名不合法"));
        }

        try {
            String algorithmResult = requestAlgorithmService(file, filename);
            JSONObject analysisData = JSONObject.parseObject(algorithmResult);
            saveInspectRecordIfNeeded(analysisData);
            log.info("人员分析请求完成, 文件名: {}", filename);
            return ResponseEntity.ok(Result.success(analysisData));
        } catch (IOException exception) {
            log.error("文件读取失败: {}", filename, exception);
            return ResponseEntity.status(500).body(Result.error(500, "文件读取失败"));
        } catch (Exception exception) {
            log.error("算法服务异常", exception);
            return ResponseEntity.status(500).body(Result.error(500, "算法服务异常"));
        }
    }

    @GetMapping("/list")
    public ResponseEntity<Result> getList() {
        log.info("查询巡检记录列表");
        return ResponseEntity.ok(Result.success(inspectRecordMapper.listAll()));
    }

    @DeleteMapping("/delete/{id}")
    public ResponseEntity<Result> delete(@PathVariable Long id) {
        inspectRecordMapper.deleteById(id);
        log.info("删除巡检记录, id: {}", id);
        return ResponseEntity.ok(Result.success("删除成功"));
    }

    private String requestAlgorithmService(MultipartFile file, String filename) throws IOException {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10000);
        factory.setReadTimeout(60000);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
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

        RestTemplate restTemplate = new RestTemplate(factory);
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        return restTemplate.postForObject(ANALYSIS_SERVICE_URL, requestEntity, String.class);
    }

    private void saveInspectRecordIfNeeded(JSONObject analysisData) {
        if (!"success".equals(analysisData.getString("status"))) {
            return;
        }

        try {
            Integer personCount = analysisData.getInteger("count");
            InspectRecord record = new InspectRecord();
            record.setCreateTime(LocalDateTime.now());
            record.setPersonCount(personCount);
            record.setLocation("核心作业区 A7");
            record.setStatus(personCount != null && personCount > 5 ? "异常" : "正常");
            record.setImageBase64(analysisData.getString("image_base64"));
            record.setAnalysisTime(0);
            inspectRecordMapper.insert(record);
            log.info("巡检记录已保存, 人数: {}", personCount);
        } catch (Exception exception) {
            log.error("保存巡检记录失败", exception);
        }
    }

    private String normalizeFilename(String originalFilename) {
        if (originalFilename == null || originalFilename.isBlank()) {
            return "upload";
        }
        return originalFilename
                .replaceAll(".*[\\\\/]", "")
                .replaceAll("[^A-Za-z0-9._-]", "_");
    }

    private boolean hasAllowedExtension(String filename) {
        int dotIndex = filename.lastIndexOf('.');
        String extension = dotIndex >= 0 ? filename.substring(dotIndex + 1).toLowerCase() : "";
        return ALLOWED_EXTENSIONS.contains(extension);
    }
}
