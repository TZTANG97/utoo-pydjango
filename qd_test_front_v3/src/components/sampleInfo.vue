<script>
import { subTestApi, sampleattributemanageList } from "@/api/test";
import { nanoid } from "nanoid";

export default {
  name: "sampleInfo",
  props: {
    openDialog: {
      // type: Object,
      require: true,
    },
    yyObj: { type: Object },
    special_type: { type: Number },
  },
  data() {
    return {
      sampleInformationList: [
        {
          data: [],
          sample_num: 1,
          sample_name: "",
          main_component: "",
          is_magnetic: 1,
          is_gold_spraying: 1,
          attribute_id: "",
        },
      ],
      uploading: false,
      formRules: {
        sample_num: [{ required: true, message: "请输入样品数量" }],
        sample_name: [{ required: true, message: "请输入名称/类型" }],
        main_component: [{ required: true, message: "请输入主要成分" }],
        is_magnetic: [{ required: true, message: "请选择是否含磁" }],
        is_gold_spraying: [{ required: true, message: "请选择是否喷金" }],
      },
      dialog: false,
      attributeManageList: [],
    };
  },
  watch: {
    // 监听数据，判断是否展示下一步
    openDialog: {
      immediate: true,
      deep: true,
      handler() {
        if (this.openDialog.type == 1) {
          this.dialog = !this.openDialog.show;
          sampleattributemanageList({ special_id: this.special_type }).then(
            (res) => {
              if (res.obj == null) {
                this.attributeManageList = [];
              } else {
                res.obj.attributeManageList.forEach((item, index) => {
                  item.attributeManageList.map((a) => {
                    a.checked = false;
                  });
                  this.sampleInformationList[0].data.push(item);
                });
                this.attributeManageList = res.obj.attributeManageList;
              }
            }
          );
        } else {
          this.dialog = false;
        }
      },
    },
  },
  // created() {
  //   sampleattributemanageList({ special_id: this.special_type }).then((res) => {
  //     if (res.obj == null) {
  //     } else {
  //       res.obj.attributeManageList.forEach((item, index) => {
  //         item.attributeManageList.map((a) => {
  //           a.checked = false;
  //         });
  //         this.sampleInformationList[0].data.push(item);
  //       });
  //       this.attributeManageList = res.obj.attributeManageList;
  //     }
  //   });
  // },
  methods: {
    // 关闭dialog表单
    closeDialog(data) {
      if (data) {
        this.$confirm("确定要取消预约吗?", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        }).then(() => {
          // 清空
          this.dialog = false;
          this.$emit("openDialogClose");
          this.sampleInformationList = [
            {
              sample_num: 1,
              data: [],
              sample_name: "",
              main_component: "",
              is_magnetic: 1,
              is_gold_spraying: 1,
              attribute_id: "",
            },
          ];
        });
      } else {
        // 清空
        this.dialog = false;
        this.$emit("openDialogClose");
        this.sampleInformationList = [
          {
            sample_num: 1,
            data: [],
            sample_name: "",
            main_component: "",
            is_magnetic: 1,
            is_gold_spraying: 1,
            attribute_id: "",
          },
        ];
      }
    },
    // 选择
    btnFn(type, data, list) {
      if (type) {
        list.forEach((item) => {
          if (item.id === data.id) {
            item.checked = true;
          } else {
            item.checked = false;
          }
        });
      } else {
        list.forEach((item) => {
          if (item.id == data.id) {
            item.checked = !item.checked;
          }
        });
      }
    },
    // 添加样品
    addSample() {
      let arr = JSON.parse(JSON.stringify(this.attributeManageList));
      this.sampleInformationList.push({
        sample_num: 1,
        sample_name: "",
        main_component: "",
        is_magnetic: 1,
        is_gold_spraying: 1,
        attribute_id: "",
        data: [],
      });
      arr.forEach((item, index) => {
        this.sampleInformationList[
          this.sampleInformationList.length - 1
        ].data.push(item);
      });
    },

    // 删除样品信息
    removeSample(index) {
      this.$confirm("是否确定删除该样品信息?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.sampleInformationList.splice(index, 1);
      });
    },
    // 数据处理
    mergeData(str) {
      // 按逗号分割字符串
      const pairs = str.split(";");

      // 使用一个对象来存储合并的数据
      const map = {};

      // 遍历所有的键值对
      pairs.forEach((pair) => {
        const [key, value] = pair.split(":");
        if (!map[key]) {
          // 如果对象中没有这个键，则初始化一个空数组
          map[key] = [];
        }
        // 将值添加到对应键的数组中
        map[key].push(value);
      });

      // 将对象中的键值对转换为目标格式的字符串
      const result = Object.entries(map)
        .map(([key, values]) => `${key}:${values.join(":")}`)
        .join(";");

      return this.removeTrailingCharacters(result);
    },
    removeTrailingCharacters(str) {
      // 正则表达式匹配最后一个数字及其后面的所有字符
      const regex = /(\d+)([^0-9]*)$/;

      // 用空字符串替换最后一个数字后的所有字符
      const result = str.replace(regex, "$1");

      return result;
    },

    // 确定预约接口
    okFn() {
      // 数据校验
      let arr = [];
      this.sampleInformationList.forEach((e, i) => {
        this.$refs["subForm"][i].validate((valid) => {
          arr.push(valid);
        });
      });
      const status = arr.find((e) => e == false);
      if (status == false) {
        // 校验失败
        this.$message.error("请完善信息！");
      } else {
        // 校验成功
        const {
          name,
          mobileNumber,
          companyName,
          mark,
          testId,
          address,
          recycle,
          addresseeName,
          addresseeMobile,
          remote_video,
          list,
        } = this.yyObj;
        for (let i = 0; i < this.sampleInformationList.length; i++) {
          for (let j = 0; j < this.sampleInformationList[i].data.length; j++) {
            if (
              this.sampleInformationList[i].data[j].attributeManageList.length >
              1
            ) {
              const status = this.sampleInformationList[i].data[
                j
              ].attributeManageList.find((e) => e.checked == true);
              if (status) {
              } else {
                return this.$message.error("请完善信息！");
              }
            }

            for (
              let k = 0;
              k <
              this.sampleInformationList[i].data[j].attributeManageList.length;
              k++
            ) {
              if (
                this.sampleInformationList[i].data[j].attributeManageList[k]
                  .checked == true
              ) {
                this.sampleInformationList[
                  i
                ].attribute_id += `${this.sampleInformationList[i].data[j].attributeManageList[k].parent_id}:${this.sampleInformationList[i].data[j].attributeManageList[k].id};`;
              }
            }
          }
        }
        this.sampleInformationList.forEach((item) => {
          item.attribute_id = this.mergeData(item.attribute_id);
          delete item.data;
        });
        // 数据转码
        let obj = {
          sampleInformationList: this.sampleInformationList,
        };
        let str = JSON.stringify(obj);
        let codeStr = encodeURIComponent(str);

        // 接口
        subTestApi({
          sampleInformationList: codeStr,
          userName: name,
          mobile: mobileNumber,
          company_name: companyName,
          content: mark,
          class_id: testId,
          address,
          recycle,
          addresseeName,
          addresseeMobile,
          order_list: list.map((item) => item.id).join(),
          is_video: remote_video,
        }).then((res) => {
          if (res.res) {
            this.closeDialog(false);
          }
          this.$notify({
            title: "提示",
            message: res.res
              ? "预约成功，稍后专属业务员会向您致电，敬请接听！"
              : res.resMsg,
            type: res.res ? "success" : "error",
          });
        });
      }
    },
  },
};
</script>

<template>
  <div class="sample-info">
    <el-dialog
      title="添加样品信息"
      v-loading.fullscreen.lock="uploading"
      v-model="dialog"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      width="600px"
    >
      <div class="sample-list">
        <div v-for="(item, idx) in sampleInformationList" :key="item.id">
          <div class="sample-title">
            <span>样品信息-{{ idx + 1 }}</span>
            <span
              @click="removeSample(idx)"
              v-show="sampleInformationList.length > 1"
              >删除</span
            >
          </div>
          <el-form
            :model="item"
            ref="subForm"
            :rules="formRules"
            label-position="top"
          >
            <el-form-item label="样品数量：" prop="sample_num">
              <el-input-number
                v-model="item.sample_num"
                :min="1"
                :max="999"
                label="请输入样品数量"
              ></el-input-number>
            </el-form-item>
            <el-form-item label="名称/类型：" prop="sample_name">
              <el-input v-model="item.sample_name" maxlength="11"></el-input>
            </el-form-item>
            <div v-for="(a, b) in item.data" :key="b">
              <el-form-item
                :label="a.name"
                v-if="a.selection == 1 && a.attributeManageList.length > 0"
              >
                <div class="syxBtnBox">
                  <div
                    v-for="subItem in a.attributeManageList"
                    :key="subItem.id"
                    :style="{
                      color: subItem.checked ? '#fff' : 'gray',
                      border: subItem.checked
                        ? '1px solid #f39800'
                        : '1px solid gray',
                      background: subItem.checked ? '#f39800' : '#fff',
                    }"
                    @click="btnFn(true, subItem, a.attributeManageList)"
                  >
                    {{ subItem.name }}
                  </div>
                </div>
              </el-form-item>
              <el-form-item
                :label="a.name"
                v-if="a.selection == 2 && a.attributeManageList.length > 0"
              >
                <div class="syxBtnBox">
                  <div
                    v-for="subItem in a.attributeManageList"
                    :key="subItem.id"
                    :style="{
                      color: subItem.checked ? '#fff' : 'gray',
                      border: subItem.checked
                        ? '1px solid #f39800'
                        : '1px solid gray',
                      background: subItem.checked ? '#f39800' : '#fff',
                    }"
                    @click="btnFn(false, subItem, a.attributeManageList)"
                  >
                    {{ subItem.name }}
                  </div>
                </div>
              </el-form-item>
            </div>
            <el-form-item label="主要成分：" prop="main_component">
              <el-input v-model="item.main_component" maxlength="11"></el-input>
            </el-form-item>
            <el-form-item label="是否含磁：" prop="is_magnetic">
              <el-select v-model="item.is_magnetic" placeholder="请选择">
                <el-option
                  v-for="subItem in [
                    { id: 0, name: '是' },
                    { id: 1, name: '否' },
                  ]"
                  :key="subItem.id"
                  :label="subItem.name"
                  :value="subItem.id"
                >
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="是否喷金：" prop="is_gold_spraying">
              <el-select v-model="item.is_gold_spraying" placeholder="请选择">
                <el-option
                  v-for="subItem in [
                    { id: 0, name: '是' },
                    { id: 1, name: '否' },
                  ]"
                  :key="subItem.id"
                  :label="subItem.name"
                  :value="subItem.id"
                >
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </div>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="addSample">添加样品</el-button>
        <div class="btns">
          <el-button @click="closeDialog(true)">取&nbsp;消</el-button>
          <el-button type="primary" @click="okFn">确&nbsp;定</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>


<style scoped>
/deep/ .el-checkbox-button__inner {
  border: 1px #cacaca solid !important;
  border-radius: 5px !important;
  margin: 0 5px 5px 0 !important;
}
/deep/ .el-checkbox-button.is-checked .el-checkbox-button__inner {
  color: #fff;
  background-color: #f39800;
  border-color: #f39800;
  border: 1px #f39800 solid !important;
  box-shadow: -1px 0 0 0 #f39800;
}
/deep/ .el-radio-button__inner {
  border: 1px #cacaca solid !important;
  border-radius: 15px !important;
  margin: 0 5px 5px 0 !important;
}
/deep/ .el-radio-button__orig-radio:checked + .el-radio-button__inner {
  color: #fff;
  background-color: #f39800;
  border-color: #f39800;
  border: 1px #f39800 solid !important;
  box-shadow: -1px 0 0 0 #f39800;
}

/deep/ .dialog-footer {
  display: flex;
  justify-content: space-between;
}

/deep/ .el-dialog {
  width: 600px !important;

  .el-dialog__body {
    padding: 0 20px;
  }
}

/deep/ .el-form-item__content {
  line-height: 1;
}

/deep/ .el-form-item__label {
  padding: 0 !important;
}
</style>

<style scoped lang="scss">
.sample-list {
  & > div:nth-child(n + 2) {
    margin-top: 50px;
  }
}

.sample-title {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;

  span:first-child {
    font-size: 18px;
    font-weight: bold;
    color: var(--mainColor);
  }

  span:last-child {
    color: #f00;
    cursor: pointer;
  }
}

.sample-list {
  max-height: 560px;
  overflow-y: scroll;
  text-align: left;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(233, 99, 2, 0.3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }
}
.syxBtnBox {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  div {
    padding: 7px 13px;
    border-radius: 5px;
    border: 1px gray solid;
    margin: 0 9px 3px 0;
    cursor: pointer;
  }
}
</style>
