<script>
import {getToken} from "@/utils/auth";
import {insertentry} from "@/api/discussion";

let token = getToken();

export default {
  data() {
    return {
      form: {
        title: '',
        photos: [],
        photoIds: [],
        content: ''
      },
      uploadUrl: process.env.VUE_APP_BASE_API + '/pc/updatePhone.ajax', // 上传的图片服务器地址
      headers: {
        token: token,
      },
      showForm: true,
    }
  },
  methods: {
    getContent(data) {
      let str = data.replaceAll(/%/g, '%25')
      let str1 = encodeURIComponent(str)
      this.form.content = str1;
    },
    handleAvatarSuccess(res) {
      console.log(res)
      this.form.photos.push(res.obj.url)
      this.form.photoIds.push(res.obj.imageId)
    },
    delImage(index) {
      this.$confirm('是否确认删除？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.form.photos.splice(index, 1)
        this.form.photoIds.splice(index, 1)
      })
    },
    submit() {
      if(!this.form.title) {
        this.$message.warning("请输入标题")
        return
      }
      let loading = this.$loading({
        lock: true,
        text: '上传中...',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.4)',
      });
      let data = {
        ...this.form
      }
      delete data.photos;
      data.photoIds = data.photoIds.join(',')
      insertentry(data).then(res => {
        if(res.res == true) {
          this.$message.success("发布成功")
          this.showForm = false;
          this.form = {
            title: '',
            photos: [],
            photoIds: [],
            content: ''
          }
          setTimeout(() => {
            loading.close()
            this.showForm = true;
          }, 300)
        } else {
          loading.close()
          this.$message.error(res.resMsg)
        }
      })
    },
  }
}
</script>

<template>
  <div class="container">
    <el-form ref="issueForm" :model="form" label-width="100px" v-if="showForm">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" maxlength="120" placeholder="请输入标题"></el-input>
      </el-form-item>
      <el-form-item label="轮播图" prop="photoIds">
        <div class="uploadImageBox">
          <div v-for="(item, index) in form.photos" style="display:flex; flex-direction: column; align-items: center">
            <el-image
              :src="item"
              class="avatar-uploader"
              :preview-src-list="[item]">
            </el-image>
            <el-button type="danger" class="el-icon-close" size="mini" @click="delImage(index)"></el-button>
          </div>
          <el-upload
            class="avatar-uploader"
            :action="uploadUrl"
            list-type="picture-card"
            :headers="headers"
            name="photo"
            :show-file-list="false"
            :on-success="handleAvatarSuccess">
            <i slot="default" class="el-icon-plus"></i>
          </el-upload>
        </div>
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <div style="width: 950px;">
          <editor ref="editor" height="400" :disabled="false" :toolbarShow="true" @input="getContent"></editor>
        </div>
      </el-form-item>
    </el-form>
    <div style="display:flex; justify-content: end">
      <el-button type="primary" @click="submit">
        发布
      </el-button>
    </div>

  </div>
</template>
<style lang="scss" scoped>
.container {
  background: #ffffff;
  min-height: 100vh;
  overflow: auto;
  padding: 24px;
  .content {
    margin: 10px auto;
    width: 1000px;
    background: #ffffff;
    padding: 16px;
  }
}
.uploadImageBox {
  display: flex;
  flex-wrap: wrap;
  .avatar-uploader {
    width: 150px;
    height: 150px;
    margin: 10px;
    display: block;
  }
}
</style>
