<template>
  <view class="proposal_main">
    <view class="proposal_content">
      <view class="proposal_title">提议内容</view>
      <view class="textarea_box">
        <textarea class="textarea"
                  v-model="text"
                  placeholder="请简要描述您的问题或建议"
                  :maxlength="200"
                  :show-confirm-bar="false"
                  :adjust-position="false"></textarea>
        <view class="image_files">
          <view class="image_item upload_box" @click="selectUploadType" v-if="fileList.length < 8">
            <view>
              <image class="image_up" src="../../static/img/upload.png"></image>
              <text class="up_image_text">上传图片</text>
            </view>
          </view>
          <view class="image_item" style="border: none" v-for="(item, index) in fileList">
            <image class="upload_image_item" :src="item.path"></image>
            <view class="del_btn" @click="delImage(item, index)">X</view>
          </view>
        </view>
      </view>
    </view>

    <view class="proposal_menu_main">
      <view class="proposal_menu" @click="submitProposal">提交</view>
    </view>

  </view>
</template>

<script>
import { addProposalImprove } from '@/api'

export default {
  data() {
    return {
      fileList: [],
      text: ''
    }
  },
  methods: {
    delImage(row, index) {
      this.fileList.splice(index, 1)
    },

    selectUploadType() {
      let _this = this;
      uni.showActionSheet({
        itemList: ['拍照', '从相册中选择'],
        success: function(res) {
          if (res.tapIndex === 0) {
            _this.uploadImage(['camera']);
          } else {
            _this.uploadImage(['album']);
          }
        }
      });
    },

    uploadImage(types) {
      let _this = this;
      uni.chooseImage({
        count: 1,
        sizeType: ['original', 'compressed'],
        sourceType: types,
        success: function(res) {
          // 选择图片成功后立即上传
          uni.showLoading({
            title: '上传中...',
            mask: true
          });
			  	const token = uni.getStorageSync('token')
          
          // 这里使用uni.uploadFile上传图片
          uni.uploadFile({
            url: `${_this.$baseUrl}/productOrder/uploadfiles.ajax`, // 上传地址留空
            filePath: res.tempFilePaths[0],
            name: 'photo',
            header: {
                token,
                uniapp: 'true'
            },
            success: function(uploadRes) {
              uni.hideLoading();
              // 假设上传成功后返回的id和路径
              // 实际项目中需要根据后端返回的数据结构进行调整
              let response = JSON.parse(uploadRes.data);
              console.log(response)
              if(response.res){
                uni.showToast({
                  title: '上传成功',
                  icon: 'none'
                });
              let imgId = response.obj.id || '';
                _this.fileList.push({
                  path: res.tempFilePaths[0],
                  id: imgId // 上传完成后返回的id
                });
              } else {
                uni.showToast({
                  title: response.resMsg || '上传失败',
                  icon: 'none'
                });
              }
          
            },
            fail: function() {
              uni.hideLoading();
              uni.showToast({
                title: '上传失败',
                icon: 'none'
              });
            }
          });
        }
      });
    },

    submitProposal() {
      if (this.text.trim().length) {
        let data = {
          content: this.text,
          ids: '',
          platform: 4
        };
        
        // 将文件id组合成字符串
        let imgIds = [];
        this.fileList.forEach(item => {
          if (item.id) {
            imgIds.push(item.id);
          }
        });
        data.ids = imgIds.join(',');
        
        uni.showLoading({
          title: '提交中...',
          mask: true
        });
        
        // 调用提交接口
        addProposalImprove(data).then(res => {
          if (res.res) {
            uni.showToast({
              title: '提交成功',
              icon: 'none'
            });
            
            // 清空表单
            this.fileList = [];
            this.text = '';
          } else {
            uni.showToast({
              title: res.message || '提交失败',
              icon: 'none'
            });
          }
        })
      } else {
        uni.showToast({
          title: '请输入提议内容',
          icon: 'none'
        });
      }
    }
  }
};
</script>

<style lang="scss" scoped>
.proposal_main {
  min-height: 100vh;
  background-color: #f5f5f5;
  overflow: hidden;
  
  .proposal_title {
    margin-top: 38rpx;
    margin-bottom: 20rpx;
    padding-left: 30rpx;
    font-size: 32rpx;
    font-weight: 500;
    color: #333;
  }
  
  .proposal_content {
    padding: 0 30rpx;
    
    .textarea_box {
      border: 1rpx solid #e5e5e5;
      font-size: 30rpx;
      border-radius: 8rpx;
      padding: 15rpx;
      background-color: #fff;
      
      .textarea {
        width: 100%;
        height: 200rpx;
        resize: none;
        color: #333;
      }
      
      .num_tips {
        font-size: 24rpx;
        color: #999;
        line-height: 42rpx;
        text-align: right;
      }
      
      .image_files {
        display: flex;
        flex-wrap: wrap;
        margin-top: 16rpx;
        
        .image_item {
          width: 154rpx;
          height: 154rpx;
          margin: 10rpx 5rpx;
          background: #fafafa;
          border-radius: 8rpx;
          border: 1rpx dashed #e5e5e5;
          display: flex;
          justify-content: center;
          align-items: center;
          position: relative;
          
          .image_up {
            width: 50rpx;
            height: 48rpx;
            margin: 0 auto;
            display: block;
          }
          
          .up_image_text {
            font-size: 24rpx;
            color: #999;
            line-height: 46rpx;
            text-align: center;
          }
        }
      }
    }
  }
}

.proposal_menu_main {
  position: fixed;
  bottom: 48rpx;
  width: 100%;
  margin: 0 auto;
  
  .proposal_menu {
    width: 80%;
    max-width: 1600rpx;
    padding: 24rpx 32rpx;
    margin: 0 auto;
    background-color: #3C8BDB; /* 修改为指定的颜色 */
    color: #fff;
    font-size: 32rpx;
    text-align: center;
    border-radius: 40rpx;
  }
}

.upload_image_item {
  width: 154rpx;
  height: 154rpx;
  border-radius: 8rpx;
}

.del_btn {
  position: absolute;
  width: 30rpx;
  height: 30rpx;
  top: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 0 8rpx 0 8rpx;
  color: #fff;
  font-size: 24rpx;
  text-align: center;
  line-height: 30rpx;
  font-weight: bold;
}

.upload_box {
  width: 150rpx !important;
  height: 150rpx !important;
}
</style>