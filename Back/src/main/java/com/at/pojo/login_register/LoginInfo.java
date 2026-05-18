package com.at.pojo.login_register;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;


@Data
@AllArgsConstructor
@NoArgsConstructor
public class LoginInfo {



    private List<String> routes;
    private List<String> buttons;
    private List<String> roles;
    private String name;
    private String avatar;
}
