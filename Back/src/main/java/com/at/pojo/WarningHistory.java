package com.at.pojo;

import lombok.Data;
import java.time.LocalDateTime;

// 移除所有 MyBatis-Plus 注解，仅保留 Lombok 和字段
@Data
public class WarningHistory {
    private Integer id;
    private Integer carId;
    private String areaName;
    private Integer x;
    private Integer y;
    private String gasType;
    private Double gasValue;
    private LocalDateTime warningTime;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getCarId() {
        return carId;
    }

    public void setCarId(Integer carId) {
        this.carId = carId;
    }

    public String getAreaName() {
        return areaName;
    }

    public void setAreaName(String areaName) {
        this.areaName = areaName;
    }

    public Integer getX() {
        return x;
    }

    public void setX(Integer x) {
        this.x = x;
    }

    public Integer getY() {
        return y;
    }

    public void setY(Integer y) {
        this.y = y;
    }

    public String getGasType() {
        return gasType;
    }

    public void setGasType(String gasType) {
        this.gasType = gasType;
    }

    public Double getGasValue() {
        return gasValue;
    }

    public void setGasValue(Double gasValue) {
        this.gasValue = gasValue;
    }

    public LocalDateTime getWarningTime() {
        return warningTime;
    }

    public void setWarningTime(LocalDateTime warningTime) {
        this.warningTime = warningTime;
    }
}