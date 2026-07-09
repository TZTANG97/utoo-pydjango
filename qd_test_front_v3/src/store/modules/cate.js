import {getTestCateListApi} from "@/api/test";

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
    // 获取分类列表
    getCateList({commit}) {
        return new Promise((resolve, reject) => {
            getTestCateListApi()
              .then((res) => {
                if (res && res.res) {
                  commit('SET_CATE_LIST', res.obj || [])
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

