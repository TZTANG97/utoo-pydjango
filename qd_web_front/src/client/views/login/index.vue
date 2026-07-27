<template>
  <div class="container">
    <div class="operation-panel">
      <img
        v-if="login_way"
        @click="changeLoginWay(false)"
        class="qrcode-login"
        src="@client/static/qrcode.png"
        alt=""
      />
      <img
        v-else
        @click="changeLoginWay(true)"
        class="account-login"
        src="@client/static/form-login.png"
        alt=""
      />

      <div class="input-login" v-if="login_way">
        <div class="options">
          <span v-if="!optionIndex">登录</span>
          <span v-else-if="optionIndex === 1">注册</span>
          <span v-else>忘记密码</span>
        </div>
        <el-form :model="form" status-icon :rules="rules" ref="form">
          <el-form-item prop="mobile">
            <el-input
              v-model="form.mobile"
              maxlength="11"
              placeholder="请输入手机号"
            ></el-input>
          </el-form-item>
          <el-form-item prop="nick_name" v-if="optionIndex === 1">
            <el-input
              v-model="form.nick_name"
              maxlength="11"
              placeholder="请输入昵称"
            ></el-input>
          </el-form-item>
          <el-form-item prop="pwd">
            <el-input
              show-password
              v-model="form.pwd"
              maxlength="20"
              :placeholder="`请输入${optionIndex === 2 ? '新' : ''}密码`"
            ></el-input>
          </el-form-item>
          <el-form-item prop="confirm_pwd" v-if="optionIndex">
            <el-input
              show-password
              v-model="form.confirm_pwd"
              maxlength="20"
              :placeholder="`请再次输入${optionIndex === 2 ? '新' : ''}密码`"
            ></el-input>
          </el-form-item>
          <el-form-item prop="code" v-if="optionIndex">
            <el-input
              style="width: 260px !important"
              v-model="form.code"
              maxlength="6"
              placeholder="请输入验证码"
            ></el-input>
            <div class="code-loading" v-if="getCoding">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
            <el-button
              v-else
              class="get-note-code-btn"
              :style="{
                cursor: countDown === '获取验证码' ? 'pointer' : 'default',
              }"
              type="text"
              @click="getNoteCode"
              >{{ countDown }}
            </el-button>
          </el-form-item>
          <el-form-item>
            <div
              class="slider"
              @click="verified = true"
              :class="{ pass: verified }"
            >
              <div class="left-border"></div>
              <span v-if="verified">验证通过</span>
              <span v-else>点击按钮开始验证</span>
              <svg-icon class-name="slider-logo" icon-class="detect"></svg-icon>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="perAction"
              style="width: 100%"
              :loading="logining"
            >
              <span v-if="!optionIndex">登&nbsp;录</span>
              <span v-else-if="optionIndex === 1">注&nbsp;册</span>
              <span v-else>保&nbsp;存</span>
            </el-button>
            <div class="other-handle">
              <el-button
                type="text"
                @click="change(2)"
                v-if="optionIndex !== 2"
              >
                忘记密码
              </el-button>
              <el-button type="text" @click="change(0)" v-if="optionIndex">
                已有帐号？去登录
              </el-button>
              <el-button
                type="text"
                @click="change(1)"
                v-if="optionIndex !== 1"
              >
                没有账号？去注册
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <div class="qrcode-login-wrapper" v-else>
        <div
          class="wx-qrcode"
          v-loading="loadingQrcode"
          element-loading-background="rgba(0, 0, 0, 0.75)"
        >
          <img v-if="ticket" :src="ticket" alt="" />
          <div class="shadow" v-if="qrcodeStatus !== 'NOT_SCAN'">
            <div
              class="expired"
              v-if="qrcodeStatus === 'EXPIRED' || qrcodeStatus === 'ERROR'"
            >
              <span>{{ qrcodeStatusList[qrcodeStatus] }}</span>
              <div class="btn" @click="getQrcode">刷新</div>
            </div>
            <div class="scaning" v-if="qrcodeStatus === 'SCANNED'">
              <svg-icon
                icon-class="success"
                class-name="success-svg"
              ></svg-icon>
              <span>{{ qrcodeStatusList[qrcodeStatus] }}</span
              ><br />
              <span>请在手机端完成登录</span>
            </div>
          </div>
        </div>
        <div class="tip">打开手机 <span>微信</span> 扫描二维码登录或注册</div>
      </div>
    </div>
  </div>
</template>

<script>
import { Loading } from '@element-plus/icons-vue'
import { getNoteCodeApi, regApi } from "@client/api/user";
import {
  getQrcodeApi,
  getQrcodeStatusApi,
  updatePasswordApi,
  fetchForgetPwdCodeApi,
} from "@client/api";
import { getToken, setToken } from "@client/utils/auth";
import { validMobile } from "@client/utils/validate";


export default {
  name: "Play",
  components: { Loading },
  data() {
    // 验证手机号
    const validateMobileNumber = (rule, value, callback) => {
      if (!value) {
        callback(new Error("手机号不能为空"));
      } else if (!validMobile(value)) {
        callback(new Error("手机号格式不正确"));
      } else {
        callback();
      }
    };

    // 验证确认密码
    const validateConfirmPwd = (rule, value, callback) => {
      if (!value) {
        callback(new Error("请再次输入密码"));
      } else if (value !== this.form.pwd) {
        callback(new Error("两次密码输入不一致"));
      } else {
        callback();
      }
    };
    return {
      form: {
        mobile: "",
        nick_name: "",
        pwd: "",
        confirm_pwd: "",
        code: "",
      },
      rules: {
        mobile: [
          {
            validator: validateMobileNumber,
            trigger: "blur",
          },
        ],
        nick_name: [
          {
            required: true,
            message: "昵称不能为空",
            trigger: "blur",
          },
        ],
        code: [
          {
            required: true,
            message: "验证码不能为空",
            trigger: "blur",
          },
        ],
        pwd: [
          {
            required: true,
            message: "密码不能为空",
            trigger: "blur",
          },
        ],
        confirm_pwd: [
          {
            validator: validateConfirmPwd,
            trigger: "blur",
          },
        ],
      },
      // 1账号密码登录 2扫码登录
      login_way: false,
      optionIndex: 0,
      countDown: "获取验证码",
      getCoding: false,
      timer: null,
      logining: false,
      verified: false,
      ticket: "",
      checkTimer: "",
      qrcodeStatus: "NOT_SCAN",
      loadingQrcode: false,
      qrcodeStatusList: {
        SCANNED: "扫码成功",
        NOT_SCAN: "未扫码",
        EXPIRED: "二维码已过期",
        ERROR: "加载失败，请刷新",
      },
    };
  },
  mounted() {
    if (getToken()) {
      this.$router.replace("/b/order");
      return;
    }
    this.getQrcode();
  },

  destroyed() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
    }
  },
  methods: {
    change(v) {
      this.$refs.form.resetFields();
      for (const refNameKey in this.form) {
        this.form[refNameKey] = "";
      }

      if (this.optionIndex) {
        clearInterval(this.timer);
        this.countDown = "获取验证码";
      }

      this.optionIndex = v;
    },

    // 查看状态
    check() {
      const ticket = this.ticket.split("?")[1].replace("ticket=", "");
      getQrcodeStatusApi(ticket)
        .then((res) => {
          this.qrcodeStatus = res.obj;

          if (
            this.qrcodeStatus === "EXPIRED" ||
            Object.prototype.toString.call(res.obj) === "[object Object]"
          ) {
            clearInterval(this.checkTimer);
          }

          if (Object.prototype.toString.call(res.obj) === "[object Object]") {
            const { token, nickName, avatar, phone } = res.obj;
            this.$store.commit("user/SET_TOKEN", token);
            this.$store.commit("user/SET_NAME", nickName);
            this.$store.commit("user/SET_AVATAR", avatar);
            this.$store.commit("user/SET_MOBILE", phone);
            setToken(token);
            this.$router.replace("/b/order");
            localStorage.setItem("menuIdx", 1);
          }
        })
        .catch((_) => {
          clearInterval(this.checkTimer);
          this.qrcodeStatus = "ERROR";
        });
    },

    // 获取二维码
    getQrcode() {
      this.loadingQrcode = true;
      this.qrcodeStatus = "NOT_SCAN";
      getQrcodeApi()
        .then((res) => {
          const url = res?.url || res?.obj?.url || res?.data?.url;
          if (url) {
            this.ticket = url;
            this.loadingQrcode = false;
            this.qrcodeStatus = "NOT_SCAN";
            this.checkTimer = setInterval(() => {
              this.check();
            }, 1500);
            return;
          }
          this.loadingQrcode = false;
          this.qrcodeStatus = "ERROR";
          const msg =
            res?.resMsg || res?.message || "二维码加载失败，请稍后重试";
          this.$message.error(msg);
        })
        .catch(() => {
          this.loadingQrcode = false;
          this.qrcodeStatus = "ERROR";
          this.$message.error("二维码加载失败，请检查网络或联系管理员");
        });
    },

    // 修改登录方式
    changeLoginWay(val) {
      if (this.login_way === val) return;
      this.login_way = val;
      if (this.login_way) {
        clearInterval(this.checkTimer);
        this.ticket = "";
        this.qrcodeStatus = "NOT_SCAN";
      } else {
        this.form.code = "";
        this.form.pwd = "";
        this.form.nick_name = "";
        this.form.mobile = "";
        this.form.confirm_pwd = "";
        this.optionIndex = 0;
        this.getQrcode();
      }
    },

    // 获取短信验证码
    getNoteCode() {
      if (this.countDown !== "获取验证码") return;
      if (!this.form.mobile) {
        return this.$notify({
          type: "warning",
          title: "提示",
          message: "请输入手机号",
        });
      } else if (!validMobile(this.form.mobile)) {
        return this.$notify({
          type: "warning",
          title: "提示",
          message: "手机号格式不正确",
        });
      }

      this.getCoding = true;

      if (this.optionIndex === 1) {
        getNoteCodeApi(this.form.mobile)
          .then((res) => {
            if (res.res) {
              let time = 60;
              this.countDown = time + "s";
              this.timer = setInterval(() => {
                if (!time) {
                  clearInterval(this.timer);
                  this.countDown = "获取验证码";
                } else {
                  this.countDown = time + "s";
                  time--;
                }
              }, 1000);
            } else {
              this.$notify({
                title: "提示",
                type: "warning",
                message: res.resMsg,
              });
            }
          })
          .finally((_) => {
            this.getCoding = false;
          });
      } else {
        //   ===2
        fetchForgetPwdCodeApi(this.form.mobile)
          .then((res) => {
            if (res.res) {
              let time = 60;
              this.countDown = time + "s";
              this.timer = setInterval(() => {
                if (!time) {
                  clearInterval(this.timer);
                  this.countDown = "获取验证码";
                } else {
                  this.countDown = time + "s";
                  time--;
                }
              }, 1000);
            } else {
              this.$notify({
                title: "提示",
                type: "warning",
                message: res.resMsg,
              });
            }
          })
          .finally((_) => {
            this.getCoding = false;
          });
      }
    },

    // 登录
    perAction() {
      this.$refs["form"].validate((valid) => {
        if (!valid) return;
        const { mobile, code, pwd, confirm_pwd, nick_name } = this.form;

        if (!this.verified) {
          return this.$notify.warning({
            title: "提示",
            message: "请验证",
          });
        }

        if (!this.optionIndex) {
          this.logining = true;
          this.$store
            .dispatch("user/login", {
              mobile: mobile,
              pwd: pwd,
            })
            .then((res) => {
              if (!res.res) {
                this.$notify({
                  type: "error",
                  message: res.resMsg,
                  title: "提示",
                });
                this.verified = false;
              } else {
                this.$router.replace("/b/order");
                localStorage.setItem("menuIdx", 1);
              }
            })
            .finally((_) => {
              this.logining = false;
            });
        } else if (this.optionIndex === 1) {
          this.logining = true;
          regApi({
            mobile: mobile,
            password1: pwd,
            code: code,
            companyName: "",
            password2: confirm_pwd,
            userName: nick_name,
          })
            .then((res) => {
              if (res.res) {
                this.change(0);
                localStorage.setItem("menuIdx", 1);
              }
              this.$notify({
                type: res.res ? "success" : "error",
                message: res.resMsg,
                title: "提示",
              });
            })
            .finally((_) => {
              this.logining = false;
            });
        } else {
          this.logining = true;
          updatePasswordApi({
            telephone: mobile,
            tel_code: code,
            password: pwd,
            password1: confirm_pwd,
          })
            .then((res) => {
              this.$notify({
                type: res.res ? "success" : "error",
                message: res.resMsg,
                title: "提示",
              });
              if (res.res) {
                this.change(0);
              }
            })
            .finally((_) => {
              this.logining = false;
            });
        }
      });
    },
  },
};
</script>

<style scoped lang="scss">
.other-handle {
  display: flex;
  justify-content: space-between;
}

.input-login {
  width: 450px;
  padding: 50px;
}

.success-svg {
  display: block;
  width: 70px;
  height: 70px;
  margin: 0 auto 5px;
  fill: var(--mainColor);
}

.slider {
  position: relative;
  width: 100%;
  height: 40px;
  border-radius: 4px;
  background-color: #ffffff;
  cursor: pointer;
  box-sizing: border-box;
  overflow: hidden;
  text-align: center;
  line-height: 40px;
  font-size: 14px;
  box-shadow: inset 0 -7px 15px #f0f0f0;
  color: #676767;
  border: 1px solid #cccccc;
  transition: all 0.3s;

  .slider-logo {
    position: absolute;
    right: 30px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24px;
    fill: #cfcfcf;
    transition: all 0.3s;
  }
}

.slider:hover {
  box-shadow: inset 0 7px 15px #f0f0f0 !important;
}

.left-border {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 5px;
  background-color: var(--mainColor);
  transition: all 0.3s;
}

.pass {
  border: 1px solid var(--mainColor);
  background-color: #f3fdec;
  color: var(--mainColor);
  box-shadow: none;
  text-align: left;
  padding-left: 30px;
  // 禁止触发hover
  pointer-events: none;

  .left-border {
    background-color: var(--mainColor);
  }

  .slider-logo {
    fill: var(--mainColor);
  }
}

.get-note-code-btn,
.code-loading {
  display: inline-block;
  vertical-align: middle;
  margin-left: 10px;
  width: 80px;
  color: var(--mainColor);
  text-align: center;
}

.code-loading {
  font-size: 20px;
}

.code {
  cursor: pointer;
  margin-left: 10px;
  width: 80px;
  height: 36px;
}

.login-btn {
  height: 40px;
  background-color: var(--mainColor);
  border-radius: 8px;
  text-align: center;
  color: #fff;
  line-height: 40px;
  margin: auto;
  font-size: 17px;
  cursor: pointer;
}

.option-active {
  color: var(--mainColor) !important;
  position: relative;

  &::after {
    display: block;
    position: absolute;
    left: 50%;
    margin-left: -12px;
    bottom: -15px;
    content: "";
    width: 24px;
    height: 4px;
    background-color: var(--mainColor);
    border-radius: 2px;
  }
}

.options {
  display: flex;
  justify-content: center;
  font-size: 24px;
  //color: rgba(233, 99, 2, .4);
  color: var(--mainColor) !important;

  div {
    cursor: pointer;
    transition: all 0.3s;
  }

  .reg {
    margin-left: 44px;
  }
}

.company-name {
  font-size: 24px;
}

.company-intdc {
  font-size: 16px;
  margin-top: 43px;
  max-width: 386px;
}

.qrcode-login-wrapper {
  display: flex;
  flex-direction: column;
  text-align: center;
  align-items: center;
  justify-content: center;
  width: 400px;
  height: 400px;

  .tip {
    margin-top: 20px;

    span {
      color: var(--mainColor);
    }
  }
}

.wx-qrcode {
  position: relative;
  width: 200px;
  height: 200px;
  border: 1px solid #f1f1f1;
  border-radius: 3px;

  img,
  .shadow {
    width: 100%;
    height: 100%;
  }

  .shadow {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: 0;
    background-color: rgba(0, 0, 0, 0.7);

    .scaning {
      font-size: 15px;
    }

    .scaning,
    .expired {
      width: 100%;
      line-height: 1.3;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translateX(-50%) translateY(-50%);
      color: #fff;

      span {
        font-weight: bold;
      }
    }

    .expired {
      .btn {
        width: 70px;
        height: 30px;
        border-radius: 3px;
        text-align: center;
        line-height: 30px;
        font-size: 10px;
        background-color: var(--mainColor);
        margin: 10px auto 0;
        cursor: pointer;
      }
    }
  }
}

.qrcode-login,
.account-login {
  position: absolute;
  right: 0;
  top: 0;
  width: 60px;
  height: 60px;
  cursor: pointer;
}

.operation-panel {
  position: fixed;
  transform: translate(-50%, -50%);
  left: 50%;
  top: 50%;
  background-color: #fff;
  border-radius: 24px;
  box-shadow: 0 0 10px #e1e1e1;
  overflow: hidden;
}
</style>

<style scoped>
/deep/ .el-form {
  margin-top: 30px;
}

/deep/ .el-input__inner {
  height: 40px !important;
}

/deep/ .el-form-item__content {
  margin-top: 6px;
}

.body {
  position: relative;
  background-color: #eff6ff !important;
}
</style>
