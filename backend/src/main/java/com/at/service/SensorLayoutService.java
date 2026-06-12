package com.at.service;

import com.at.mapper.SensorLayoutMapper;
import com.at.pojo.SensorLayout;
import com.at.pojo.SensorLayoutDetail;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
public class SensorLayoutService {

    @Resource
    private SensorLayoutMapper sensorLayoutMapper;

    @Transactional
    public Integer saveLayout(SensorLayout layout, List<SensorLayoutDetail> details) {
        layout.setSensorCount(details.size());
        layout.setStatus("draft");
        sensorLayoutMapper.insertLayout(layout);
        Integer layoutId = layout.getId();

        if (details != null && !details.isEmpty()) {
            for (SensorLayoutDetail detail : details) {
                detail.setLayoutId(layoutId);
                sensorLayoutMapper.insertDetail(detail);
            }
        }

        log.info("保存布局方案: id={}, name={}, 传感器数量: {}", layoutId, layout.getLayoutName(), details.size());
        return layoutId;
    }

    @Transactional
    public boolean updateLayout(SensorLayout layout, List<SensorLayoutDetail> details) {
        sensorLayoutMapper.updateLayout(layout);
        sensorLayoutMapper.deleteDetailsByLayoutId(layout.getId());

        if (details != null && !details.isEmpty()) {
            for (SensorLayoutDetail detail : details) {
                detail.setLayoutId(layout.getId());
                sensorLayoutMapper.insertDetail(detail);
            }
        }

        log.info("更新布局方案: id={}, 传感器数量: {}", layout.getId(), details.size());
        return true;
    }

    public boolean deleteLayout(Integer id) {
        sensorLayoutMapper.deleteLayout(id);
        log.info("删除布局方案: id={}", id);
        return true;
    }

    public List<SensorLayout> getAllLayouts() {
        return sensorLayoutMapper.selectLayoutList();
    }

    public SensorLayout getLayoutById(Integer id) {
        return sensorLayoutMapper.selectLayoutById(id);
    }

    public List<SensorLayoutDetail> getLayoutDetails(Integer layoutId) {
        return sensorLayoutMapper.selectDetailsByLayoutId(layoutId);
    }
}
