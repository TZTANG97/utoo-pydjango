<script>
import { UploadPermitApi } from "@/api/index";
import { mapMutations } from "vuex";
import { loadMammoth, loadXlsx } from "@/utils/loadScript";

export default {
  name: "offlinePay",
  data() {
    return {
      path: "",
      fileId: [],
      fileList: [],
      topUpMoney: 0,
      innerVisible: false,
    };
  },
  props: {
    title: {
      default: "",
      type: String,
    },
    modelValue: {
      default: false,
      type: Boolean,
    },
    value: {
      default: false,
      type: Boolean,
    },
    cltAccount: {
      default: "",
      type: String,
    },
    cltName: {
      default: "",
      type: String,
    },
    payMoney: {
      default: 0,
      type: Number,
    },
  },
  computed: {
    dialogVisible: {
      get() {
        return this.modelValue || this.value;
      },
      set(val) {
        this.$emit("update:modelValue", val);
        this.$emit("input", val);
      },
    },
  },
  methods: {
    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),

    openDialog() {
      this.path = "";
      this.fileId = [];
      this.topUpMoney = 0;
      this.$refs["file"] && this.resetInput();
    },

    handleClose(done) {
      this.dialogVisible = false;
      this.fileList = [];
      if (typeof done === "function") done();
    },

    // 复制
    copyAccount() {},

    resetInput() {
      this.$refs["file"].value = "";
    },

    // 验证金额
    verifyMoney(e) {
      let num = parseFloat(e);

      if (num < 1) {
        num = 1;
      }

      if (num > 999999) {
        num = 999999;
      }

      this.topUpMoney = num;
    },

    uploadFile(e) {
      if(e.target.files.length == 0) return
      this.CHANGE_LOADING(1);
      const fileList = e.target.files;
      for (const file of fileList) {
        this.fileList.push(file);

        // if (file.size / 1024 / 1024 > 3) {
        //   // this.resetInput();
        //   this.CHANGE_LOADING();
        //   return this.$notify.warning({
        //     title: "提示",
        //     message: "回执单大小不能超过 3MB!",
        //   });
        // }
        UploadPermitApi(file)
          .then((res) => {
            if (res.res) {
              const { path, name, id } = res.obj;
              this.path = path + "/" + name;
              this.fileId.push(id);
              // this.resetInput();
            } else {
              this.$notify.warning({
                title: "提示",
                message: res.errMsg,
              });
            }
          })
          .finally((_) => {
            this.CHANGE_LOADING();
          });
      }
      // this.CHANGE_LOADING();

      // if (type !== 'image/jpeg' && type !== 'image/jpg' && type !== 'image/png') {
      //   this.resetInput()
      //   this.CHANGE_LOADING()
      //   return this.$notify.warning({
      //     title: '提示',
      //     message: '上传的回执单只能是 JPG/PNG 格式!'
      //   })
      // }

      // if (file.size / 1024 / 1024 > 3) {
      //   this.resetInput();
      //   this.CHANGE_LOADING();
      //   return this.$notify.warning({
      //     title: "提示",
      //     message: "回执单大小不能超过 3MB!",
      //   });
      // }
    },

    confirm() {
      if (!this.path)
        return this.$notify.warning({
          title: "提示",
          message: "请上传回执单！",
        });
      this.$emit("confirmSubmit", {
        money: this.title === "充值" ? this.topUpMoney : this.money,
        fileId: this.fileId.join(","),
      });
      this.fileList = [];
      this.fileId = [];
    },
    // 点击预览各种类型文件
    fileFn(data) {
      console.log(data, "data");
      this.innerVisible = true;
      setTimeout(() => {
        const previewContainer = document.getElementById("previewContainer");
        previewContainer.innerHTML = "";
        const fileType = data.type;
        const fileReader = new FileReader();
        fileReader.onload = (e) => {
          const fileURL = e.target.result;
          if (fileType.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = fileURL;
            img.style.maxWidth = "100%";
            previewContainer.appendChild(img);
          } else if (fileType === "application/pdf") {
            const iframe = document.createElement("iframe");
            iframe.src = fileURL;
            iframe.style.width = "100%";
            iframe.style.height = "500px";
            previewContainer.appendChild(iframe);
          } else if (fileType.startsWith("text/")) {
            const pre = document.createElement("pre");
            pre.textContent = e.target.result;
            previewContainer.appendChild(pre);
            pre.style.overflowWrap = "break-word";
            pre.style.whiteSpace = "pre-wrap";
          } else if (
            fileType ==
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          ) {
            loadMammoth()
              .then((mammoth) => mammoth.convertToHtml({ arrayBuffer: fileURL }))
              .then((result) => {
                const index = result.value.indexOf("src");
                if (index != -1) {
                  result.value =
                    result.value.slice(0, index) +
                    ' width="100% "' +
                    result.value.slice(index);
                }
                previewContainer.innerHTML = result.value;
              })
              .catch((err) => {
                console.log(err, "err");
                previewContainer.innerHTML =
                  "<p>Error: " + err.message + "</p>";
              });
          } else if (
            fileType == "application/vnd.ms-excel" ||
            fileType ==
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ) {
            loadXlsx()
              .then((XLSX) => {
                const data = new Uint8Array(fileURL);
                const workbook = XLSX.read(data, { type: "array" });
                const sheetName = workbook.SheetNames[0];
                const sheet = workbook.Sheets[sheetName];
                previewContainer.innerHTML = XLSX.utils.sheet_to_html(sheet);
              })
              .catch((err) => {
                console.log(err, "err");
                previewContainer.innerHTML =
                  "<p>Error: " + err.message + "</p>";
              });
          } else {
            return this.$message.error("该文件暂不支持预览！");
          }
        };
        if (fileType.startsWith("text/")) {
          fileReader.readAsText(data);
        } else if (
          fileType ==
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
          fileType == "application/vnd.ms-excel" ||
          fileType ==
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ) {
          fileReader.readAsArrayBuffer(data);
        } else {
          fileReader.readAsDataURL(data);
        }
      }, 200);
    },
    deleteFn(index) {
      this.fileList.splice(index, 1);
      this.fileId.splice(index, 1);
    },
  },
};
</script>

<template>
  <div class="offline-pay">
    <el-dialog
      @open="openDialog"
      :title="`线下${title}`"
      v-model="dialogVisible"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleClose"
    >
      <el-dialog title="文件预览" v-model="innerVisible" append-to-body align-center>
        <div id="previewContainer"></div>
      </el-dialog>
      <div class="collection-info">
        <div class="collection-item">
          <div class="label">收款账号：</div>
          <div class="value">
            <span>{{ cltAccount ? cltAccount : "暂无" }}</span>
            <el-button
              type="text"
              size="mini"
              v-if="cltAccount"
              style="margin-left: 10px"
              @click="copyAccount"
              >复制
            </el-button>
          </div>
        </div>
        <div class="collection-item">
          <div class="label">收款公司名称：</div>
          <div class="value">{{ cltName ? cltName : "暂无" }}</div>
        </div>
        <div class="collection-item">
          <div class="label">{{ title }}金额：</div>
          <div class="value">
            <el-input
              v-if="title === '充值'"
              :maxlength="6"
              :placeholder="`请输入充值金额`"
              v-model="topUpMoney"
              type="number"
              @change="verifyMoney"
            ></el-input>
            <span v-else>{{ payMoney.toFixed(2) }}元</span>
          </div>
        </div>
        <div class="collection-item">
          <div class="label">回执单：</div>
          <div class="value">
            <!-- v-if="!path" -->
            <div class="receipt" @click="$refs['file'].click()">
              <i class="el-icon-plus" />
            </div>
            <!-- <img v-else :src="path" alt="" @click="$refs['file'].click()"> -->
          </div>
        </div>
        <!-- multiple -->
        <input
          type="file"
          @change="uploadFile"
          ref="file"
          multiple
          v-show="false"
        />
        <ul class="fileList">
          <li v-for="(item, index) in fileList" :key="index">
            <span @click="fileFn(item)">{{ item.name }}</span>
            <b @click="deleteFn(index)">删除</b>
          </li>
        </ul>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="handleClose">取&nbsp;消</el-button>
        <el-button type="primary" @click="confirm">确&nbsp;定</el-button>
      </span>
    </el-dialog>
  </div>
</template>


<style scoped>
/deep/.el-dialog {
  width: 600px;
}

.el-dialog__body {
  padding: 0 20px 10px !important;
}

.collection-item .el-input {
  width: 100%;
}
</style>
<style scoped lang="scss">
#previewContainer img {
    width: 460px;
  }
.fileList {
  li {
    display: flex;
    justify-content: space-between;
    cursor: pointer;
    margin: 5px 0;
    span:hover {
      color: #0078d4;
    }
    b:hover {
      color: red;
    }
  }
}
.offline-pay {
  .collection-info {
    font-size: 16px;

    .collection-item {
      margin-top: 20px;
    }

    .label {
      font-weight: bold;
    }

    .value {
      margin-top: 5px;
      font-size: 15px;

      .el-input {
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
          -webkit-appearance: none;
          height: 100px;
        }
      }

      img {
        width: 100px;
        height: 100px;
        border-radius: 5px;
        cursor: pointer;
        border: 2px dotted #999;
      }
    }
  }

  .receipt {
    display: flex;
    box-sizing: border-box;
    justify-content: center;
    align-items: center;
    width: 100px;
    height: 100px;
    border-radius: 5px;
    border: 2px dotted #999;
    cursor: pointer;
    margin-top: 10px;

    i {
      font-size: 25px;
    }
  }
}
</style>
