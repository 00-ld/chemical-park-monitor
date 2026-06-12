package com.at.pojo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class InspectRecord {
    private Long id;
    private LocalDateTime createTime;
    private Integer personCount;
    private String location;
    private String status;
    private String imageBase64;
    private Integer analysisTime;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    public Integer getPersonCount() {
        return personCount;
    }

    public void setPersonCount(Integer personCount) {
        this.personCount = personCount;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getImageBase64() {
        return imageBase64;
    }

    public void setImageBase64(String imageBase64) {
        this.imageBase64 = imageBase64;
    }

    public Integer getAnalysisTime() {
        return analysisTime;
    }

    public void setAnalysisTime(Integer analysisTime) {
        this.analysisTime = analysisTime;
    }
}