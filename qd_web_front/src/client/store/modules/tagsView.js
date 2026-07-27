const STORAGE_KEY = 'qd-tags-view'

function tagKey(view) {
  return view.fullPath || view.path
}

function normalizeView(view) {
  const title = view.meta?.title || view.title || 'no-name'
  return {
    fullPath: view.fullPath || view.path,
    path: view.path,
    name: view.name,
    query: view.query ? { ...view.query } : {},
    meta: {
      title,
      affix: !!(view.meta && view.meta.affix),
      noCache: !!(view.meta && view.meta.noCache),
    },
    title,
  }
}

function loadPersisted() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return { visitedViews: [], cachedViews: [] }
    const data = JSON.parse(raw)
    return {
      visitedViews: Array.isArray(data.visitedViews) ? data.visitedViews : [],
      cachedViews: Array.isArray(data.cachedViews) ? data.cachedViews : [],
    }
  } catch {
    return { visitedViews: [], cachedViews: [] }
  }
}

function persistState(state) {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        visitedViews: state.visitedViews,
        cachedViews: state.cachedViews,
      })
    )
  } catch {
    /* quota / private mode */
  }
}

function clearPersisted() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

const persisted = loadPersisted()

const state = {
  visitedViews: persisted.visitedViews,
  cachedViews: persisted.cachedViews,
}

const mutations = {
  ADD_VISITED_VIEW: (state, view) => {
    const tag = normalizeView(view)
    if (state.visitedViews.some(v => tagKey(v) === tagKey(tag))) return
    state.visitedViews.push(tag)
    persistState(state)
  },
  ADD_CACHED_VIEW: (state, view) => {
    if (!view.name) return
    if (state.cachedViews.includes(view.name)) return
    if (!view.meta?.noCache) {
      state.cachedViews.push(view.name)
      persistState(state)
    }
  },

  DEL_VISITED_VIEW: (state, view) => {
    const key = tagKey(view)
    const i = state.visitedViews.findIndex(v => tagKey(v) === key)
    if (i > -1) state.visitedViews.splice(i, 1)
    persistState(state)
  },
  DEL_CACHED_VIEW: (state, view) => {
    const index = state.cachedViews.indexOf(view.name)
    if (index > -1) state.cachedViews.splice(index, 1)
    persistState(state)
  },

  DEL_OTHERS_VISITED_VIEWS: (state, view) => {
    const key = tagKey(view)
    state.visitedViews = state.visitedViews.filter(
      v => v.meta?.affix || tagKey(v) === key
    )
    persistState(state)
  },
  DEL_OTHERS_CACHED_VIEWS: (state, view) => {
    const index = state.cachedViews.indexOf(view.name)
    if (index > -1) {
      state.cachedViews = state.cachedViews.slice(index, index + 1)
    } else {
      state.cachedViews = []
    }
    persistState(state)
  },

  DEL_ALL_VISITED_VIEWS: state => {
    const affixTags = state.visitedViews.filter(tag => tag.meta?.affix)
    state.visitedViews = affixTags
    persistState(state)
  },
  DEL_ALL_CACHED_VIEWS: state => {
    state.cachedViews = []
    persistState(state)
  },

  UPDATE_VISITED_VIEW: (state, view) => {
    const key = tagKey(view)
    for (let i = 0; i < state.visitedViews.length; i++) {
      if (tagKey(state.visitedViews[i]) === key) {
        state.visitedViews[i] = Object.assign(
          {},
          state.visitedViews[i],
          normalizeView(view)
        )
        break
      }
    }
    persistState(state)
  },

  CLEAR_TAGS: state => {
    state.visitedViews = []
    state.cachedViews = []
    clearPersisted()
  },
}

const actions = {
  addView({ dispatch }, view) {
    dispatch('addVisitedView', view)
    dispatch('addCachedView', view)
  },
  addVisitedView({ commit }, view) {
    commit('ADD_VISITED_VIEW', view)
  },
  addCachedView({ commit }, view) {
    commit('ADD_CACHED_VIEW', view)
  },

  delView({ dispatch, state }, view) {
    return new Promise(resolve => {
      dispatch('delVisitedView', view)
      dispatch('delCachedView', view)
      resolve({
        visitedViews: [...state.visitedViews],
        cachedViews: [...state.cachedViews],
      })
    })
  },
  delVisitedView({ commit, state }, view) {
    return new Promise(resolve => {
      commit('DEL_VISITED_VIEW', view)
      resolve([...state.visitedViews])
    })
  },
  delCachedView({ commit, state }, view) {
    return new Promise(resolve => {
      commit('DEL_CACHED_VIEW', view)
      resolve([...state.cachedViews])
    })
  },

  delOthersViews({ dispatch, state }, view) {
    return new Promise(resolve => {
      dispatch('delOthersVisitedViews', view)
      dispatch('delOthersCachedViews', view)
      resolve({
        visitedViews: [...state.visitedViews],
        cachedViews: [...state.cachedViews],
      })
    })
  },
  delOthersVisitedViews({ commit, state }, view) {
    return new Promise(resolve => {
      commit('DEL_OTHERS_VISITED_VIEWS', view)
      resolve([...state.visitedViews])
    })
  },
  delOthersCachedViews({ commit, state }, view) {
    return new Promise(resolve => {
      commit('DEL_OTHERS_CACHED_VIEWS', view)
      resolve([...state.cachedViews])
    })
  },

  delAllViews({ dispatch, state }, view) {
    return new Promise(resolve => {
      dispatch('delAllVisitedViews', view)
      dispatch('delAllCachedViews', view)
      resolve({
        visitedViews: [...state.visitedViews],
        cachedViews: [...state.cachedViews],
      })
    })
  },
  delAllVisitedViews({ commit, state }) {
    return new Promise(resolve => {
      commit('DEL_ALL_VISITED_VIEWS')
      resolve([...state.visitedViews])
    })
  },
  delAllCachedViews({ commit, state }) {
    return new Promise(resolve => {
      commit('DEL_ALL_CACHED_VIEWS')
      resolve([...state.cachedViews])
    })
  },

  clearTags({ commit }) {
    commit('CLEAR_TAGS')
  },

  updateVisitedView({ commit }, view) {
    commit('UPDATE_VISITED_VIEW', view)
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
}
