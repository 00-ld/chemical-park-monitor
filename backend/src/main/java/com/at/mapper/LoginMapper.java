package com.at.mapper;

import com.at.pojo.login_register.User;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface LoginMapper {

    // 按用户名查询用户，密码在 Java 服务层用 BCrypt 校验。
    @Select("SELECT * FROM user WHERE username = #{username}")
    User getByUsername(String username);

    // 注册用户，密码已在服务层哈希，角色由服务端统一写入。
    @Insert("INSERT INTO user(username, password, role, create_time) VALUES(#{username}, #{password}, #{role}, NOW())")
    int insert(User user);
}
