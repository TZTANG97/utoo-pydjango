import {getTestCateListApi} from "@client/api/test";

const getDefaultState = () => {
    return {
        cateList: [],
        showCate: false
    }
}

const state = getDefaultState()

const mutations = {
    RESET_STATE: (state) => {
        Object.assign(state, getDefaultState())
    },
    SET_CATE_LIST: (state, cateList) => {
        state.cateList = cateList
    },
    CHANGE_SHOW_CATE: (state, showCate) => {
        state.showCate = showCate
    }
}

const actions = {
    // 获取分类列表（兼容误返回 secList/tList 的旧数据）
    getCateList({commit}) {
        return new Promise((resolve, reject) => {
            getTestCateListApi()
              .then((res) => {
                if (res && res.res) {
                  const list = (res.obj || []).map((lv1) => {
                    const secs = lv1.childList || lv1.secList || []
                    return {
                      ...lv1,
                      childList: secs.map((lv2) => ({
                        ...lv2,
                        childList: lv2.childList || lv2.tList || [],
                      })),
                    }
                  })
                  commit('SET_CATE_LIST', list)
                }
                resolve()
              })
              .catch((error) => {
                console.warn('[cate] getCateList failed', error)
                resolve()
              })
        })
    },
}

export default {
    namespaced: true,
    state,
    mutations,
    actions
}

