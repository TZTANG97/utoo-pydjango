import Cookies from 'js-cookie'

const state = {
  sidebar: {
    opened: Cookies.get('sidebarStatus') ? !!+Cookies.get('sidebarStatus') : true,
    withoutAnimation: false
  },
  device: 'desktop',

  loading: false,
  count: 0,
  startTime: 0,
  minTime: 600
}

const mutations = {

  CHANGE_LOADING: (state, value) => {
    console.log(state,'state')
    console.log(value,'value')
    if (value) {
      if (!state.loading) {
        state.loading = true
        state.startTime = +new Date()
      }
      state.count += 1
    } else {
      if (state.count > 0) {
        state.count -= 1
        if (!state.count) {
          const endTime = +new Date(),
            time = endTime - state.startTime;
          if (time > state.minTime) {
            state.loading = false
            state.startTime = 0
          } else {
            setTimeout(() => {
              state.loading = false
              state.startTime = 0
            }, state.minTime - time)
          }
        }
      }
    }
  },

  TOGGLE_SIDEBAR: state => {
    state.sidebar.opened = !state.sidebar.opened
    state.sidebar.withoutAnimation = false
    if (state.sidebar.opened) {
      Cookies.set('sidebarStatus', 1)
    } else {
      Cookies.set('sidebarStatus', 0)
    }
  },
  CLOSE_SIDEBAR: (state, withoutAnimation) => {
    Cookies.set('sidebarStatus', 0)
    state.sidebar.opened = false
    state.sidebar.withoutAnimation = withoutAnimation
  },
  TOGGLE_DEVICE: (state, device) => {
    state.device = device
  }
}

const actions = {
  toggleSideBar({commit}) {
    commit('TOGGLE_SIDEBAR')
  },
  closeSideBar({commit}, {withoutAnimation}) {
    commit('CLOSE_SIDEBAR', withoutAnimation)
  },
  toggleDevice({commit}, device) {
    commit('TOGGLE_DEVICE', device)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
