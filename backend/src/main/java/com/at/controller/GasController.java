package com.at.controller;

import com.at.pojo.Gas;
import com.at.pojo.Result;
import com.at.service.GasService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/gas")
public class GasController {

    @Resource
    private GasService gasService;

    @GetMapping("/list")
    public ResponseEntity<Result<?>> getAllGases() {
        try {
            List<Gas> list = gasService.getAllGases();
            log.info("查询所有气体类型, 数量: {}", list.size());
            return ResponseEntity.ok(Result.success(list));
        } catch (Exception e) {
            log.error("查询气体类型失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败"));
        }
    }

    @PostMapping("/add")
    public ResponseEntity<Result<?>> addGas(@RequestBody Gas gas) {
        try {
            if (gas.getId() == null || gas.getId().isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("气体编号不能为空"));
            }
            if (gas.getName() == null || gas.getName().isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("气体名称不能为空"));
            }
            boolean success = gasService.addGas(gas);
            if (success) {
                log.info("新增气体类型成功: id={}, name={}", gas.getId(), gas.getName());
                return ResponseEntity.ok(Result.success("气体类型已保存"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("保存失败"));
            }
        } catch (Exception e) {
            log.error("新增气体类型异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常"));
        }
    }

    @PostMapping("/update")
    public ResponseEntity<Result<?>> updateGas(@RequestBody Gas gas) {
        try {
            if (gas.getId() == null || gas.getId().isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("气体编号不能为空"));
            }
            boolean success = gasService.updateGas(gas);
            if (success) {
                log.info("更新气体类型成功: id={}", gas.getId());
                return ResponseEntity.ok(Result.success("气体类型已更新"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("更新失败"));
            }
        } catch (Exception e) {
            log.error("更新气体类型异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常"));
        }
    }

    @PostMapping("/delete")
    public ResponseEntity<Result<?>> deleteGas(@RequestBody Map<String, String> param) {
        try {
            String id = param.get("id");
            if (id == null || id.isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("气体编号不能为空"));
            }
            boolean success = gasService.deleteGas(id);
            if (success) {
                log.info("删除气体类型成功: id={}", id);
                return ResponseEntity.ok(Result.success("气体类型已删除"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("删除失败，未找到该气体类型"));
            }
        } catch (Exception e) {
            log.error("删除气体类型异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常"));
        }
    }
}
