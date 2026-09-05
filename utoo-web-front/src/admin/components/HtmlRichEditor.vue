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
import AlbumImagePicker from '@admin/components/AlbumImagePicker.vue'

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

/**
 * 对齐 Java KindEditor 落库内容：常见为「裸 img + 紧跟文字」或零散文节点。
 * wangEditor 要求块级结构，否则会丢掉 img 后面的文字（如 fsafaf）。
 */
function normalizeLegacyHtml(raw: string): string {
  const src = String(raw || '').trim()
  if (!src) return '<p><br></p>'

  if (typeof DOMParser === 'undefined') {
    // SSR / 极端环境兜底：简单包一层
    if (/^<p[\s>]/i.test(src) || /^<div[\s>]/i.test(src)) return src
    return `<p>${src}</p>`
  }

  const doc = new DOMParser().parseFromString(`<div id="__root__">${src}</div>`, 'text/html')
  const root = doc.getElementById('__root__')
  if (!root) return src

  const nodes = Array.from(root.childNodes)
  for (const node of nodes) {
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent || ''
      if (!text.trim()) {
        root.removeChild(node)
        continue
      }
      const p = doc.createElement('p')
      p.textContent = text
      root.replaceChild(p, node)
      continue
    }
    if (node.nodeType !== Node.ELEMENT_NODE) continue
    const el = node as HTMLElement
    const tag = el.tagName.toLowerCase()
    if (tag === 'img') {
      const p = doc.createElement('p')
      root.insertBefore(p, el)
      p.appendChild(el)
      continue
    }
    // 块内若仍有「img 后紧跟裸文本」，再包一层文字到 p
    if (tag === 'p' || tag === 'div') {
      const kids = Array.from(el.childNodes)
      for (const kid of kids) {
        if (kid.nodeType === Node.TEXT_NODE && (kid.textContent || '').trim()) {
          // 已在 p 内的文字可保留
          continue
        }
      }
    }
  }

  const out = root.innerHTML.trim()
  return out || '<p><br></p>'
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

  const initialHtml = normalizeLegacyHtml(html.value || '')

  const editor = createEditor({
    selector: editorHost.value,
    html: initialHtml,
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

  // 若规范化后与外部 v-model 不一致，回写一次（不触发丢字）
  if (initialHtml !== (html.value || '').trim()) {
    syncingFromEditor = true
    html.value = editor.getHtml()
    void nextTick(() => {
      syncingFromEditor = false
    })
  }
}

function insertImage(pick: string | { id?: number; url: string }) {
  const url = typeof pick === 'string' ? pick : pick.url
  if (!url) return
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
  const next = normalizeLegacyHtml(val || '')
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
