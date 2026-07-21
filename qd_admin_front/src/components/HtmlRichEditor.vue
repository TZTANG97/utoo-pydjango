<template>
  <div class="rich-editor">
    <div ref="toolbarHost" class="toolbar-host" />
    <div ref="editorHost" class="editor-host" />
    <div class="actions">
      <el-button @click="albumVisible = true">从相册选择图片</el-button>
      <slot name="actions" />
    </div>
    <AlbumImagePicker v-model="albumVisible" @select="insertImage" />
  </div>
</template>

<script setup lang="ts">
import '@wangeditor/editor/dist/css/style.css'
import { createEditor, createToolbar, type IDomEditor, type IEditorConfig } from '@wangeditor/editor'
import { nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import AlbumImagePicker from '@/components/AlbumImagePicker.vue'

const html = defineModel<string>({ default: '' })

const toolbarHost = ref<HTMLDivElement | null>(null)
const editorHost = ref<HTMLDivElement | null>(null)
const editorRef = shallowRef<IDomEditor | null>(null)
const albumVisible = ref(false)
/** avoid feedback loop when syncing html from editor */
let syncingFromEditor = false

const editorConfig: Partial<IEditorConfig> = {
  placeholder: '请输入页面内容…',
  MENU_CONF: {},
}

function destroyEditor() {
  const editor = editorRef.value
  if (!editor) return
  try {
    editor.destroy()
  } catch {
    // ignore double-destroy
  }
  editorRef.value = null
}

function initEditor() {
  if (!toolbarHost.value || !editorHost.value) return
  destroyEditor()
  toolbarHost.value.innerHTML = ''
  editorHost.value.innerHTML = ''

  const editor = createEditor({
    selector: editorHost.value,
    html: html.value || '',
    mode: 'default',
    config: {
      ...editorConfig,
      onChange(ed) {
        syncingFromEditor = true
        html.value = ed.getHtml()
        void nextTick(() => {
          syncingFromEditor = false
        })
      },
    },
  })

  createToolbar({
    editor,
    selector: toolbarHost.value,
    mode: 'default',
    config: {
      excludeKeys: ['group-video', 'uploadVideo', 'insertVideo', 'uploadImage'],
    },
  })

  editorRef.value = editor
}

function insertImage(url: string) {
  const editor = editorRef.value
  if (!editor) return
  editor.focus()
  editor.dangerouslyInsertHtml(
    `<p><img src="${url}" alt="" style="max-width:100%;" /></p>`
  )
}

watch(html, (val) => {
  if (syncingFromEditor) return
  const editor = editorRef.value
  if (!editor) return
  const next = val || ''
  if (editor.getHtml() === next) return
  editor.setHtml(next)
})

onMounted(() => {
  void nextTick(() => initEditor())
})

onBeforeUnmount(() => {
  destroyEditor()
})

defineExpose({ insertImage, getEditor: () => editorRef.value })
</script>

<style scoped lang="scss">
.rich-editor {
  position: relative;
  z-index: 1;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: #fff;
  /* do not use overflow:hidden — it blocks toolbar dropdowns / clicks */
}

.toolbar-host {
  position: relative;
  z-index: 20;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: #fff;

  :deep(.w-e-toolbar) {
    flex-wrap: wrap;
  }

  :deep(.w-e-bar-item button) {
    pointer-events: auto;
    cursor: pointer;
  }

  :deep(.w-e-select-list),
  :deep(.w-e-drop-panel),
  :deep(.w-e-bar-item-menus-container),
  :deep(.w-e-modal) {
    z-index: 1000;
  }
}

.editor-host {
  height: 420px;
  position: relative;
  z-index: 1;
  overflow-y: hidden;

  :deep(.w-e-text-container) {
    height: 100% !important;
  }
}

.actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: #fafbfc;
}
</style>
