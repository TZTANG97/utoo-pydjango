import { createStore } from 'vuex'
import getters from './getters'
import app from './modules/app'
import settings from './modules/settings'
import user from './modules/user'
import tagsView from './modules/tagsView'
import permission from './modules/permission'
import cate from './modules/cate'

export default createStore({
  modules: {
    app,
    settings,
    tagsView,
    permission,
    user,
    cate,
  },
  getters,
})
