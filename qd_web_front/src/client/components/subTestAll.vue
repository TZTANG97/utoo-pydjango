<script>
import {sampleattributemanageList, subTestApi} from "@client/api/test";
import { mapGetters } from "vuex";
import { getUserDefaultAddressApi, UploadPermitApi } from "@client/api/index";
import SampleInfo from "@client/components/sampleInfo.vue";

const supportedTypeList = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "application/msword",
  "application/vnd.ms-excel",
];
export default {
  components: {SampleInfo},
  props: {
    openDialog: {
      // type: Object,
      require:true
    },
    testId: {
      default: "",
      type: String,
    },
    testName: {
      default: "",
      type: String,
    },
    defaultAddress: {
      default: "",
      type: String,
    },
    special_type: { type: Number },

  },
  data() {
    const validateMobileNumber = (rule, value, callback) => {
      const reg = /^1[3-9]\d{9}$/;
      if (!value) {
        callback(new Error("请输入手机号"));
      } else if (!reg.test(value)) {
        callback(new Error("手机号格式不正确"));
      } else {
        callback();
      }
    };
    return {
      // 是否正在提交
      submitting: false,
      subForm: {
        name: "",
        mobileNumber: "",
        companyName: "",
        mark: "",
        recycle: false,
        address: "",
        addresseeName: "",
        addresseeMobile: "",
        remote_video: false,
        video_url: "",
      },
      subFormRules: {
        address: [
          {
            required: true,
            message: "地址不能为空",
            trigger: "blur",
          },
        ],
        addresseeName: [
          {
            required: true,
            message: "收件人姓名",
            trigger: "blur",
          },
        ],
        addresseeMobile: [
          {
            required: true,
            message: "收件人电话",
            trigger: "blur",
          },
        ],
        name: [
          {
            required: true,
            message: "姓名不能为空",
            trigger: "blur",
          },
        ],
        mobileNumber: [
          {
            required: true,
            validator: validateMobileNumber,
            trigger: "blur",
          },
        ],
      },
      uploading: false,
      file_list: [],
      video_list: [],
      dialog: false,
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
      formRules: {
        sample_num: [{ required: true, message: "请输入样品数量" }],
        sample_name: [{ required: true, message: "请输入名称/类型" }],
        is_magnetic: [{ required: true, message: "请选择是否含磁" }],
      },
      yyObj: {}
    };
  },
  computed: {
    ...mapGetters(["name", "mobile", "authInfo"]),
  },
  watch: {
    // 监听数据，判断是否展示下一步
    openDialog: {
      immediate: true,
      deep: true,
      handler() {
        if (this.openDialog.type === 2) {
          this.dialog = false;
          return;
        }
        this.dialog = !!this.openDialog.show;
        if (this.dialog) {
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
        }

      },
    },
  },
  methods: {

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
          is_arrive,
          is_on
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
          item.is_gold_spraying = item.gold_desc ? 1 : 0;
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
          is_arrive: is_arrive ? is_arrive : false,
          is_on: is_on ? is_on : false,
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
    // 监听dialog被打开
    async opeded() {
      const r = await getUserDefaultAddressApi();
      if (r.res) {
        this.subForm.address = r.obj;
      }
      if (this.name) {
        this.subForm.name = this.subForm.addresseeName = this.name;
      }
      if (this.mobile) {
        this.subForm.mobileNumber = this.subForm.addresseeMobile = this.mobile;
      }

      if (this.authInfo && this.authInfo.userType === 2) {
        this.subForm.addresseeName = this.authInfo.company_name;
      }
    },

    // 提交表单数据
    submitForm(data) {
      this.$refs["sub-form"].validate((valid) => {
        if (valid) {
          if (!this.name) {
            this.$confirm("是否前往登录?", "提示", {
              confirmButtonText: "确定",
              cancelButtonText: "取消",
              type: "warning",
            }).then(() => {
              this.$router.push("/login");
            });
          } else {
            const {
              name,
              mobileNumber,
              companyName,
              mark,
              address,
              recycle,
              addresseeName,
              addresseeMobile,
              remote_video,
            } = this.subForm;
            const reg = /^1[3-9]\d{9}$/;

            if (recycle) {
              if (!addresseeName)
                return this.$notify({
                  title: "提示",
                  message: "请输入收件人名称",
                  type: "warning",
                });

              if (!addresseeMobile)
                return this.$notify({
                  title: "提示",
                  message: "收件人手机号不能为空",
                  type: "warning",
                });

              if (!reg.test(addresseeMobile))
                return this.$notify({
                  title: "提示",
                  message: "收件人手机号格式错误",
                  type: "warning",
                });

              if (!address)
                return this.$notify({
                  title: "提示",
                  message: "收件人地址不能为空",
                  type: "warning",
                });
            }
            let obj = {
              sampleInformationList: null,
            };
            let str = JSON.stringify(obj);
            let codeStr = encodeURIComponent(str);
            subTestApi({
              sampleInformationList: codeStr,
              userName: name,
              mobile: mobileNumber,
              company_name: companyName,
              content: mark,
              class_id: this.testId,
              address,
              recycle,
              addresseeName,
              addresseeMobile,
              order_list: this.file_list.map((item) => item.id).join(),
              is_video: remote_video,
            }).then((res) => {
              if (res.res) {
                if (data) this.closeDialog();
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
        } else {
          return false;
        }
      });
    },

    // 关闭dialog表单
    closeDialog() {
      // 清空
      this.$refs["sub-form"].resetFields();
      this.file_list = [];
      this.video_list = [];
      this.sampleInformationList = [
        {
          data: [],
          sample_num: 1,
          sample_name: "",
          main_component: "",
          is_magnetic: 1,
          is_gold_spraying: 1,
          attribute_id: "",
        }
      ]
      this.resetInput();
      this.dialog = false;
      this.$emit("openDialogClose");
    },

    resetInput(name = "") {
      if (!name) {
        // this.$refs['video'].value = ''
        this.$refs["file"].value = "";
      } else {
        this.$refs[name].value = "";
      }
      this.uploading = false;
    },

    // 删除资料
    deleteData(id, key_name) {
      const idx = this[key_name].findIndex((e) => e.id === id);
      this[key_name].splice(idx, 1);
    },

    upload(name) {
      if (!this.name) return this.$router.push("/login");
      this.$refs[name].click();
    },

    // 上传资料
    uploadData(e, handle_name) {
      this.uploading = true;
      console.log(e,'e')
      const file = e.target.files[0],
        type = file.type;
      console.log(file,'file')
      console.log(type,'type')
      if (
        (handle_name === "file" && !supportedTypeList.includes(type)) ||
        (handle_name === "video" && type !== "video/mp4")
      ) {
        console.log("77777")
        this.resetInput(handle_name);
        return this.$notify.warning({
          title: "提示",
          message:
            handle_name === "file" ? "格式不支持" : "只能上传MP4格式的视频",
        });
      }
      console.log('66666')
      // if (file.size / 1024 / 1024 > 5) {
      //   this.resetInput(handle_name);
      //   return this.$notify.warning({
      //     title: "提示",
      //     message: `${
      //       handle_name === "file" ? "资料" : "视频"
      //     }大小不能超过 5MB!`,
      //   });
      // }

      UploadPermitApi(file)
        .then((res) => {
          if (res.res) {
            const { path, name, id } = res.obj;
            this[handle_name + "_list"].push({
              path: path + "/" + name,
              name,
              id,
            });
          } else {
            this.$notify.warning({
              title: "提示",
              message: res.errMsg,
            });
          }
        })
        .finally((_) => {
          this.resetInput(handle_name);
        });
    },
    // 下一步
    nextStep() {
      // this.submitForm(false)
      if(!this.name) {
        this.$confirm("是否前往登录?", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        }).then(() => {
          this.$router.push("/login");
        });
        return;
      }

      const {
        name,
        mobileNumber,
        companyName,
        mark,
        address,
        recycle,
        addresseeName,
        addresseeMobile,
        remote_video,
      } = this.subForm;
      const reg = /^1[3-9]\d{9}$/;

      if (recycle) {
        if (!addresseeName)
          return this.$notify({
            title: "提示",
            message: "请输入收件人名称",
            type: "warning",
          });

        if (!addresseeMobile)
          return this.$notify({
            title: "提示",
            message: "收件人手机号不能为空",
            type: "warning",
          });

        if (!reg.test(addresseeMobile))
          return this.$notify({
            title: "提示",
            message: "收件人手机号格式错误",
            type: "warning",
          });

        if (!address)
          return this.$notify({
            title: "提示",
            message: "收件人地址不能为空",
            type: "warning",
          });
      }
      let obj = this.subForm;
      obj.list = this.file_list;
      obj.testId = this.testId;
      this.yyObj = obj;
      this.okFn()

    },
  },
};
</script>

<template>
  <el-dialog
    @open="opeded"
    :before-close="closeDialog"
    v-loading.fullscreen.lock="uploading"
    v-model="dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    width="1200px"
  >
    <div style="display:flex;">
      <div style="flex: 1">
        <div style="font-size: 20px">预约实验</div>
        <el-form
          class="sub-form"
          :model="subForm"
          ref="sub-form"
          :rules="subFormRules"
          label-position="top"
        >
          <el-form-item label="姓名：(请务必与寄件人一致)" prop="name">
            <el-input v-model="subForm.name" maxlength="10"></el-input>
          </el-form-item>
          <el-form-item label="手机号：(请务必与寄件手机号一致)" prop="mobileNumber">
            <el-input v-model="subForm.mobileNumber" maxlength="11"></el-input>
          </el-form-item>
          <el-row>
            <el-col :span="12">
              <el-form-item label="样品回收：">
                <el-switch v-model="subForm.recycle" active-color="#F39800">
                </el-switch>
                <span>&nbsp;&nbsp;(样品寄回默认到付)</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="线下到场">
                <el-switch v-model="subForm.is_arrive" active-color="#F39800">
                </el-switch>
                <span>&nbsp;&nbsp;(提前2个工作日预约时间)</span>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item
            label="收件人姓名："
            prop="addresseeName"
            v-if="subForm.recycle"
          >
            <el-input v-model="subForm.addresseeName" maxlength="20"></el-input>
          </el-form-item>
          <el-form-item
            label="收件人电话："
            prop="addresseeMobile"
            v-if="subForm.recycle"
          >
            <el-input v-model="subForm.addresseeMobile" maxlength="11"></el-input>
          </el-form-item>
          <el-form-item label="收件地址：" prop="address" v-if="subForm.recycle">
            <el-input v-model="subForm.address" maxlength="40"></el-input>
          </el-form-item>
          <el-row>
            <el-col :span="12">
              <el-form-item label="云视频：">
                <el-switch v-model="subForm.remote_video" active-color="#F39800">
                </el-switch>
                <span>&nbsp;&nbsp;(根据实际测试时长结算)</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="我要上机">
                <el-switch v-model="subForm.is_on" active-color="#F39800">
                </el-switch>
                <span>&nbsp;&nbsp;(到场后全程在工程师指导下进行)</span>
              </el-form-item>
            </el-col>
          </el-row>


          <el-form-item label="上传视频：" v-if="false">
            <div class="data-list">
              <div class="data-item" v-for="item in video_list" :key="item.id">
                <a :href="item['path']" target="_blank">{{ item["name"] }}</a>
                <svg-icon
                  @click="deleteData(item.id, 'video_list')"
                  icon-class="delete"
                  class-name="delete"
                ></svg-icon>
              </div>
            </div>
            <span
              v-if="video_list.length < 5"
              type="text"
              @click="upload('video')"
              class="upload-btn"
            >上&nbsp;传
        </span>
            <input
              type="file"
              @change="uploadData($event, 'video')"
              ref="video"
              v-show="false"
            />
          </el-form-item>

          <el-form-item label="上传资料：">
            <div class="data-list">
              <div class="data-item" v-for="item in file_list" :key="item.id">
                <a :href="item['path']" target="_blank">{{ item["name"] }}</a>
                <svg-icon
                  @click="deleteData(item.id, 'file_list')"
                  icon-class="delete"
                  class-name="delete"
                ></svg-icon>
              </div>
            </div>
            <span
              v-if="file_list.length < 5"
              type="text"
              @click="upload('file')"
              class="upload-btn"
            >上&nbsp;传
        </span>
            <input
              type="file"
              @change="uploadData($event, 'file')"
              ref="file"
              v-show="false"
            />
          </el-form-item>
          <el-form-item label="实验需求：" prop="mark">
            <div>
              <div class="tipText">
                1.如有指定所需的放大倍数/标尺，请填写）
              </div>
              <div class="tipText">
                2.默认拍摄图片数量6一10张，如需增加或减少张数请填写，基于默认收费标准按张数对应增收或优惠）
              </div>
              <div class="tipText">
                3.如有测试重点关注事项，请填写或点击上传资料）
              </div>
              <div class="tipText">
                4.云视频/线下到场请按需填写您想要的时间，客服会提前2个工作日与您具体确认。关注“愉免检测“公众号会提前24小时和15分钟分别发送通知，若逾期10分钟未上线/到场则视为放弃）
              </div>
              <div class="tipText">
                5.根据不同测试项目，请按个人实际需求填写）
              </div>
            </div>
            <el-input
              v-model="subForm.mark"
              type="textarea"
              maxlength="200"
              resize="none"
            ></el-input>
          </el-form-item>
        </el-form>
      </div>
      <div style="flex: 1; margin-left: 20px">
        <div style="font-size: 20px">添加样品信息</div>
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
                <el-input v-model="item.sample_name" maxlength="50"></el-input>
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
              <el-form-item label="主要成分：(填写后默认进行EDS测试，无需则不填)" prop="main_component">
                <el-input v-model="item.main_component" maxlength="50"></el-input>
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
              <el-form-item label="默认喷金：(费用10元/样，如不喷金请在下方说明原因)" prop="gold_desc">
                <el-input v-model="item.gold_desc" maxlength="50"></el-input>
<!--                <el-select v-model="item.is_gold_spraying" placeholder="请选择">-->
<!--                  <el-option-->
<!--                    v-for="subItem in [-->
<!--                    { id: 0, name: '是' },-->
<!--                    { id: 1, name: '否' },-->
<!--                  ]"-->
<!--                    :key="subItem.id"-->
<!--                    :label="subItem.name"-->
<!--                    :value="subItem.id"-->
<!--                  >-->
<!--                  </el-option>-->
<!--                </el-select>-->
              </el-form-item>
            </el-form>
          </div>
        </div>

      </div>
    </div>
    <div slot="footer" class="dialog-footer">
      <el-button @click="closeDialog">取&nbsp;消</el-button>
      <el-button type="primary" @click="addSample">添加样品</el-button>
      <el-button
        type="primary"
        @click="nextStep"
        v-if="this.openDialog.type == 0"
      >确&nbsp;定</el-button
      >
      <el-button
        type="primary"
        @click="submitForm(true)"
        v-if="this.openDialog.type == 1"
      >确&nbsp;定</el-button
      >
    </div>
  </el-dialog>
</template>

<style scoped>
.upload-btn {
  color: var(--mainColor);
  cursor: pointer;
}

/deep/ .el-form-item__content {
  line-height: 1;
}

/deep/ .el-form-item__label {
  padding: 0 !important;
}

.data-list {
  .data-item {
    &:nth-child(n + 2) {
      margin-top: 10px;
    }

    &:last-child {
      margin-bottom: 10px;
    }

    .delete {
      margin-left: 10px;
      cursor: pointer;
      vertical-align: middle;
    }
  }
}

a:hover {
  color: var(--mainColor);
  border-bottom: 1px solid var(--mainColor);
}

.sub-form {
  max-height: 560px;
  overflow-y: scroll;
  text-align: left;
  padding: 20px;

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

/deep/ textarea {
  min-height: 150px !important;
}
.tipText {
  margin-bottom: 5px;
  line-height: 16px;
  font-size: 12px;
  color: #999999;
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
