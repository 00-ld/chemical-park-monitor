package com.at.service.impl;

import com.at.mapper.WarningHistoryMapper;
import com.at.pojo.WarningHistory;
import com.at.service.WarningHistoryService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
public class WarningHistoryServiceImpl implements WarningHistoryService {

    @Resource
    private WarningHistoryMapper warningHistoryMapper;

    @Override
    public boolean addWarningRecord(Integer carId, String areaName, Integer x, Integer y, String gasType, Double gasValue) {
        WarningHistory record = new WarningHistory();
        record.setCarId(carId);
        record.setAreaName(areaName);
        record.setX(x);
        record.setY(y);
        record.setGasType(gasType);
        record.setGasValue(gasValue);
        record.setWarningTime(LocalDateTime.now());
        int rows = warningHistoryMapper.insert(record);
        log.info("新增预警记录, carId: {}, gasType: {}, rows: {}", carId, gasType, rows);
        return rows > 0;
    }

    @Override
    public List<WarningHistory> getAllHistory() {
        List<WarningHistory> list = warningHistoryMapper.selectList();
        log.info("查询预警历史, 数量: {}", list.size());
        return list;
    }

    @Override
    public boolean deleteHistoryById(Integer id) {
        int rows = warningHistoryMapper.deleteById(id);
        log.info("删除预警记录, id: {}, rows: {}", id, rows);
        return rows > 0;
    }
}
