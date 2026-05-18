

package com.at.mapper;

import com.at.pojo.login_register.User;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface LoginMapper {

    // 根据用户名和密码查询用户（登录用）
    @Select("SELECT * FROM user WHERE username = #{username} AND password = #{password}")
    User getByUsernameAndPassword(User user);

    // 根据用户名查询用户（注册校验用）
    @Select("SELECT * FROM user WHERE username = #{username}")
    User getByUsername(String username);

    // 插入用户（注册用）
    @Insert("INSERT INTO user(username, password, create_time) VALUES(#{username}, #{password}, NOW())")
    int insert(User user);
}
