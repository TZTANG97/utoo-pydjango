import mitt from 'mitt'

const emitter = mitt()

/** 兼容 Vue2 的 $on / $off / $emit 写法 */
export default {
  $on(event, handler) {
    emitter.on(event, handler)
  },
  $off(event, handler) {
    if (handler) emitter.off(event, handler)
    else emitter.all.clear()
  },
  $emit(event, ...args) {
    emitter.emit(event, ...args)
  },
}
