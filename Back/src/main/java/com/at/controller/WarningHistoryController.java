package com.at.controller;

import com.at.pojo.Result;
import com.at.pojo.WarningHistory;
import com.at.service.WarningHistoryService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

@Slf4j
@RestController
@RequestMapping("/api/history")
@CrossOrigin
public class WarningHistoryController {

    @Resource
    private WarningHistoryService warningHistoryService;

    private static final Map<Integer, String> CAR_AREA_MAP = new HashMap<>();

    static {
        CAR_AREA_MAP.put(1, "东区");
        CAR_AREA_MAP.put(2, "南区");
        CAR_AREA_MAP.put(3, "西区");
        CAR_AREA_MAP.put(4, "北区");
    }

    @PostMapping("/add")
    public ResponseEntity<Result> addWarning(@RequestBody Map<String, Object> param) {
        try {
            Integer carId = (Integer) param.get("carId");
            String gasType = (String) param.get("gasType");
            Double gasValue = Double.valueOf(param.get("gasValue").toString());

            if (carId == null || !CAR_AREA_MAP.containsKey(carId)) {
                return ResponseEntity.badRequest().body(Result.error("小车编号无效"));
            }

            Random random = new Random();
            Integer x = random.nextInt(501);
            Integer y = random.nextInt(501);
            String areaName = CAR_AREA_MAP.get(carId);

            boolean success = warningHistoryService.addWarningRecord(carId, areaName, x, y, gasType, gasValue);
            if (success) {
                log.info("预警记录已保存, carId: {}, gasType: {}, gasValue: {}", carId, gasType, gasValue);
                return ResponseEntity.ok(Result.success("预警记录已保存"));
            } else {
                log.warn("预警记录保存失败, carId: {}", carId);
                return ResponseEntity.internalServerError().body(Result.error("保存失败"));
            }
        } catch (Exception e) {
            log.error("保存预警记录异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常：" + e.getMessage()));
        }
    }

    @GetMapping("/list")
    public ResponseEntity<Result> getHistoryList() {
        try {
            List<WarningHistory> list = warningHistoryService.getAllHistory();
            log.info("查询历史记录, 数量: {}", list.size());
            return ResponseEntity.ok(Result.success(list));
        } catch (Exception e) {
            log.error("查询历史记录失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败：" + e.getMessage()));
        }
    }

    @PostMapping("/delete")
    public ResponseEntity<Result> deleteHistory(@RequestBody Map<String, Integer> param) {
        try {
            Integer id = param.get("id");
            if (id == null) {
                return ResponseEntity.badRequest().body(Result.error("记录ID不能为空"));
            }
            boolean success = warningHistoryService.deleteHistoryById(id);
            if (success) {
                log.info("删除历史记录成功, id: {}", id);
                return ResponseEntity.ok(Result.success("删除成功"));
            } else {
                log.warn("删除历史记录失败, id: {}", id);
                return ResponseEntity.internalServerError().body(Result.error("删除失败"));
            }
        } catch (Exception e) {
            log.error("删除历史记录异常", e);
            return ResponseEntity.internalServerError().body(Result.error("删除异常：" + e.getMessage()));
        }
    }
}
