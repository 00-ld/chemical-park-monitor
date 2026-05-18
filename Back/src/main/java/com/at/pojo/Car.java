package com.at.pojo;

public class Car {
    private Integer id;         // 数据库主键
    private Integer carId;      // 小车ID
    private Integer warning;    // 0=正常 1=预警
    private Integer x;          // X坐标
    private Integer y;          // Y坐标
    private String gasType;     // 检测气体类型

    // Getter & Setter
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

    public Integer getWarning() {
        return warning;
    }

    public void setWarning(Integer warning) {
        this.warning = warning;
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
}