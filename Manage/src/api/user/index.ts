//统一管理咱们项目用户相关的接口
import request from '@/utils/request'
import type {
  loginFormData,
  loginResponseData,
  userInfoReponseData,
  registerFormData,
  registerResponseData,
} from './type'

//项目用户相关的请求地址
enum API {
  LOGIN_URL = '/user/login',
  USERINFO_URL = '/admin/acl/index/info',
  LOGOUT_URL = '/admin/acl/index/logout',
  REGISTER_URL = '/user/register'
}

//登录接口
export const reqLogin = (data: loginFormData) =>
    request.post<loginFormData, loginResponseData>(API.LOGIN_URL, data)

//注册接口
export const reqRegister = (data: registerFormData) =>
    request.post<registerFormData, registerResponseData>(API.REGISTER_URL, data)

//获取用户信息
export const reqUserInfo = () =>
    request.get<null, userInfoReponseData>(API.USERINFO_URL)

//退出登录
export const reqLogout = () => request.post<null, null>(API.LOGOUT_URL)