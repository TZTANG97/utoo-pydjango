<script>
import { h } from 'vue'
import SvgIcon from '@/components/SvgIcon/index.vue'

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
          vnodes.push(h(SvgIcon, { iconClass: props.icon }))
        }
      }
      if (props.title) {
        vnodes.push(h('span', props.title))
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
