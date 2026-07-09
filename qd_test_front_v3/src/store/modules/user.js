import {loginApi, getInfo} from '@/api/user'
import {getToken, setToken, removeToken} from '@/utils/auth'
import { getIntegralConvertRatio,getIntegralApi } from "@/api/integral";

const getDefaultState = () => {
  return {
    token: getToken(),
    name: '',
    avatar: '',
    authInfo: null,
    mobile: '',
    IntegralConvertRatio:2,
    totalIntegral:2
  }
}

const state = getDefaultState()

const mutations = {
  RESET_STATE: (state) => {
    Object.assign(state, getDefaultState())
  },
  SET_TOKEN: (state, token) => {
    state.token = token
  },
  SET_NAME: (state, name) => {
    state.name = name
  },
  SET_AVATAR: (state, avatar) => {
    state.avatar = avatar
  },
  SET_AUTH_INFO: (state, authInfo) => {
    state.authInfo = authInfo
  },
  SET_MOBILE: (state, mobile) => {
    state.mobile = mobile
  },
  SET_IntegralConvertRatio: (state, IntegralConvertRatio) => {
    state.IntegralConvertRatio = IntegralConvertRatio
  },
  SET_TotalIntegral: (state, totalIntegral) => {
    state.totalIntegral = totalIntegral
  },
}

const actions = {
  login({commit}, userInfo) {
    const {mobile, pwd} = userInfo
    return new Promise((resolve, reject) => {
      loginApi({loginName: mobile, password: pwd}).then(response => {
        if (response.res) {
          const obj = response.obj || response.data || {}
          commit('SET_TOKEN', obj.token)
          commit('SET_NAME', obj.nickName || obj.phone || mobile)
          commit('SET_AVATAR', obj.avatar)
          commit('SET_MOBILE', obj.phone)
          setToken(obj.token)
          
          getIntegralApi()
            .then(res => {
              if (res.res) commit('SET_TotalIntegral', res.obj.totalIntegral)
            })
            .catch(() => {})
          getIntegralConvertRatio()
            .then(res => {
              if (res.res) commit('SET_IntegralConvertRatio', res.obj.integral_convert_ratio)
            })
            .catch(() => {})
          
        }
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },

  // 注册
  // reg({commit}, userInfo) {
  //   const {mobile, pwd, code, confirmPwd, userName} = userInfo
  //   return new Promise((resolve, reject) => {
  //     regApi({mobile, userName, password1: pwd, code, companyName: '', password2: confirmPwd}).then(response => {
  //       if(response.res) {
  //         const {obj} = response
  //         commit('SET_TOKEN', obj.token)
  //         commit('SET_NAME', obj.nickName)
  //         commit('SET_AVATAR', obj.avatar)
  //         setToken(obj.token)
  //       }
  //       resolve(response)
  //     }).catch(error => {
  //       reject(error)
  //     })
  //   })
  // },

  // get user info
  getInfo({commit}) {
    return new Promise((resolve, reject) => {
      getInfo().then(response => {
        if (response.res) {
          const obj = response.obj || response.data || {}
          const {avatar, show_name, mobile} = obj
          commit('SET_NAME', show_name)
          commit('SET_AVATAR', avatar)
          commit('SET_AUTH_INFO', obj)
          commit('SET_MOBILE', mobile)
        }
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },

  // 获取积分对换比
  getIntegralConvertRatio({commit}) {
    return new Promise((resolve, reject) => {
      getIntegralConvertRatio().then(res => {
        if (res.res) {
          commit('SET_IntegralConvertRatio', res.obj.integral_convert_ratio)
        }
        resolve(res)
      }).catch(error => {
        reject(error)
      })
    })
  },
  //获取总积分
  getIntegralApi({commit}) {
    return new Promise((resolve, reject) => {
      getIntegralApi().then(res => {
        if (res.res) {
          commit('SET_TotalIntegral', res.obj.totalIntegral)
        }
        resolve(res)
      }).catch(error => {
        reject(error)
      })
    })
  },

  // remove token
  resetToken({ commit, dispatch }) {
    return new Promise(resolve => {
      removeToken()
      commit('RESET_STATE')
      dispatch('tagsView/clearTags', null, { root: true })
      localStorage.setItem('menuIdx', 1);
      resolve()
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

