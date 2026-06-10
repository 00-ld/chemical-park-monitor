

package com.at.mapper;

import com.at.pojo.login_register.User;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface LoginMapper {

    // 根据用户名查询用户（登录用，密码在 Java 层验证）
    @Select("SELECT * FROM user WHERE username = #{username}")
    User getByUsername(String username);

    // 插入用户（注册用，密码已哈希，role 由服务端强制赋值）
    @Insert("INSERT INTO user(username, password, role, create_time) VALUES(#{username}, #{password}, #{role}, NOW())")
    int insert(User user);
}
