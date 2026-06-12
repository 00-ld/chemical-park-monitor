package com.at.service;

import com.at.pojo.WarningHistory;
import java.util.List;

public interface WarningHistoryService {
    // 新增预警记录
    boolean addWarningRecord(Integer carId, String areaName, Integer x, Integer y, String gasType, Double gasValue);
    // 查询所有历史记录
    List<WarningHistory> getAllHistory();
    // 删除单条记录
    boolean deleteHistoryById(Integer id);
}