<script>
import { h } from 'vue'
import SvgIcon from '@client/components/SvgIcon/index.vue'

export default {
  name: 'MenuItem',
  props: {
    icon: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
  },
  setup(props) {
    return () => {
      const vnodes = []
      if (props.icon) {
        if (props.icon.includes('el-icon')) {
          vnodes.push(h('i', { class: [props.icon, 'sub-el-icon'] }))
        } else {
          vnodes.push(h(SvgIcon, { iconClass: props.icon, className: 'menu-icon' }))
        }
      }
      if (props.title) {
        // class 供收起态 CSS 精确隐藏；title 供无 tooltip 时悬停提示
        vnodes.push(h('span', { class: 'menu-title', title: props.title }, props.title))
      }
      return vnodes
    }
  },
}
</script>

<style scoped>
.sub-el-icon {
  color: currentColor;
  width: 1em;
  height: 1em;
}
</style>
