package com.at.controller;

import com.at.pojo.Car;
import com.at.pojo.Result;
import com.at.service.CarService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/car")
@CrossOrigin
public class CarController {

    @Resource
    private CarService carService;

    @GetMapping("/getAllCars")
    public ResponseEntity<Result> getAllCars() {
        try {
            List<Car> carList = carService.getAllCars();
            log.info("查询所有小车状态, 数量: {}", carList.size());
            return ResponseEntity.ok(Result.success(carList));
        } catch (Exception e) {
            log.error("查询所有小车失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败：" + e.getMessage()));
        }
    }

    @PostMapping("/setWarning")
    public ResponseEntity<Result> setWarning(@RequestBody java.util.Map<String, Integer> param) {
        Integer carId = param.get("carId");

        if (carId == null || carId < 1 || carId > 4) {
            return ResponseEntity.badRequest().body(Result.error("小车ID无效"));
        }

        int rows = carService.setWarning(carId);
        if (rows > 0) {
            log.info("小车{}预警设置成功", carId);
            return ResponseEntity.ok(Result.success("预警设置成功"));
        } else {
            log.warn("小车{}预警设置失败", carId);
            return ResponseEntity.internalServerError().body(Result.error("预警设置失败"));
        }
    }

    @PostMapping("/resetStatus")
    public ResponseEntity<Result> resetStatus(@RequestBody java.util.Map<String, Integer> param) {
        Integer carId = param.get("carId");

        if (carId == null || carId < 1 || carId > 4) {
            return ResponseEntity.badRequest().body(Result.error("小车ID无效"));
        }

        int rows = carService.resetStatus(carId);
        if (rows > 0) {
            log.info("小车{}状态重置成功", carId);
            return ResponseEntity.ok(Result.success("状态重置成功"));
        } else {
            log.warn("小车{}状态重置失败", carId);
            return ResponseEntity.internalServerError().body(Result.error("状态重置失败"));
        }
    }
}
