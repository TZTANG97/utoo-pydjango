<template>
  <admin-page-card title="App用户管理">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="用户名">
        <el-input v-model="userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="mobile" placeholder="手机号" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="trueName" label="姓名" min-width="100" />
      <el-table-column prop="mobilePhoneNumber" label="手机" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
      <el-table-column prop="companyName" label="公司" min-width="140" />
      <el-table-column prop="registerTime" label="注册时间" min-width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="reload"
      />
    </div>

    <el-dialog v-model="detailVisible" title="用户详情" width="560px">
      <el-descriptions v-if="detail" :column="1" border>
        <el-descriptions-item label="用户名">{{ detail.userName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ detail.trueName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ detail.mobilePhoneNumber || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detail.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="公司">{{ detail.companyName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ detail.registerTime || '-' }}</el-descriptions-item>
        <el-descriptions-item label="微信昵称">{{ detail.wxNickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="微信手机">{{ detail.wxPhonenum || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ detail.userStatus === 1 ? '正常' : detail.userStatus != null ? '禁用' : '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchAppUserList, getAppUserById } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

const userName = ref('')
const mobile = ref('')
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const { loading, rows, total, pagination, load } = useDataTable(fetchAppUserList)

onMounted(() => reload())

function reload() {
  return load({
    userName: userName.value.trim(),
    mobilePhoneNumber: mobile.value.trim(),
  })
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getAppUserById(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error('加载详情失败')
    return
  }
  detail.value = res.obj as Record<string, unknown>
  detailVisible.value = true
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
