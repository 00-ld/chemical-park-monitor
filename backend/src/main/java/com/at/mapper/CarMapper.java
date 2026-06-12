package com.at.mapper;

import com.at.pojo.Car;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CarMapper {

    // 手动预警：设置warning=1
    @Update("UPDATE leida SET warning = 1 WHERE car_id = #{carId}")
    int setWarning(Integer carId);

    // 重置状态：设置warning=0
    @Update("UPDATE leida SET warning = 0 WHERE car_id = #{carId}")
    int resetStatus(Integer carId);

    // 新增：查询所有小车的最新状态
    @Select("SELECT car_id as carId, warning, x, y, gas_type as gasType FROM leida")
    List<Car> getAllCars();
}