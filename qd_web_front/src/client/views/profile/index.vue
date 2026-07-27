<script>
import {
  changePwdApi,
  savaAuthInfoApi,
  saveAuthCompanyInfoApi,
  addUserInvoiceInfoApi,
  getUserInvoiceInfoApi,

  uploadAvatarApi,
} from "@client/api/user";
import { mapGetters, mapMutations } from "vuex";
import {
  addNewAddressApi,
  addNewInvoiceApi,
  delAddressApi,
  delInvoiceApi,
  fetchAddressListApi,
  fetchbasicInfoApi,
  fetchCompanyInfoApi,
  fetchInvoiceListApi,
  updateAddressApi,
  updateBasicInfoApi,
  updateInvoiceApi,
} from "@client/api/index";
import address from "@client/static/address";
import {
  validEmail,
  validMobile,
  validTaxNum,
  validBankAccount,
  validHasChinese,
} from "@client/utils/validate";

export default {
  name: "Profile",
  data() {
    var verifyName = (rule, value, callback) => {
      let val = value.replace(/\s/g, "");
      this.basicsInfoForm.name = val;
      if (!val) {
        callback(new Error("姓名不能为空"));
      } else {
        callback();
      }
    };

    const validateMobileNumber = (rule, value, callback) => {
      if (!value) {
        callback(new Error("电话号码不能为空"));
      } else if (!validMobile(value)) {
        callback(new Error("电话号码格式不正确"));
      } else {
        callback();
      }
    };

    return {
      address,
      // 用户选择，1 个人 2企业
      auth_type: 1,
      // 个人认证
      person_info: {
        company_name: "",
        trueName: "",
        // mobile: '',
        email: "",
        idcard: "",
        area_id: [],
        addreddInfo: "",
      },
      // 企业认证信息
      company_info: {
        id: "",
        name: "",
        country: "中国",
        areaId: [],
        address: "",
        contractPhone: "",
        taxNum: "",
        bank: "",
        bankCardNum: "",
      },
      person_info_rules: {
        trueName: [
          { required: true, trigger: "blur", message: "姓名不能为空" },
        ],
        // mobile: [
        //   {required: true, trigger: 'blur', message: '手机号不能为空'}
        // ],
        // email: [
        //   {required: true, trigger: 'blur', message: '电子邮件不能为空'}
        // ],
        // idcard: [
        //   {required: true, trigger: 'blur', message: '身份证号不能为空'}
        // ],
        // area_id: [
        //   {required: true, trigger: 'blur', message: '省市区不能为空'}
        // ],
        // addreddInfo: [
        //   {required: true, trigger: 'blur', message: '收货地址'}
        // ],
      },
      company_info_rules: {
        // name: [
        //   {required: true, trigger: 'blur', message: '企业名称不能为空'}
        // ],
        // country: [
        //   {required: true, trigger: 'blur', message: '国家不能为空'}
        // ],
        // areaId: [
        //   {required: true, trigger: 'blur', message: '省市区不能为空'}
        // ],
        // address: [
        //   {required: true, trigger: 'blur', message: '详细地址不能为空'}
        // ],
        // contractPhone: [
        //   {required: true, trigger: 'blur', message: '电话不能为空'}
        // ],
        // taxNum: [
        //   {required: true, trigger: 'blur', message: '纳税人识别号不能为空'}
        // ],
        // bank: [
        //   {required: true, trigger: 'blur', message: '企业开户银行不能为空'}
        // ],
        // bankCardNum: [
        //   {required: true, trigger: 'blur', message: '企业银行账号不能为空'}
        // ],
      },
      changePwdRules: {
        oldPwd: [{ required: true, trigger: "blur", message: "请输入旧密码" }],
        newPwd: [{ required: true, trigger: "blur", message: "请输入新密码" }],
        confirmNewPwd: [
          { required: true, trigger: "blur", message: "请再次输入新密码" },
        ],
      },
      changePwd: {
        oldPwd: "",
        newPwd: "",
        confirmNewPwd: "",
      },
      saving: false,
      // 已认证的身份
      userType: 1,

      // 发票信息
      invoiceForm: {
        id: "",
        invoice_title: "",
        tax_number: "",
        opened_bank_name: "",
        opened_bank_account: "",
        email: "",
        reg_address: "",
        reg_mobile: "",
      },
      // 个人资料
      profile_form: {
        avatar: "",
        mobile: "",
      },
      loading: false,
      invoiceFormRules: {
        invoice_title: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, "");
              this.invoiceForm.invoice_title = val;
              if (!val) {
                callback(new Error("发票抬头不能为空"));
              } else {
                callback();
              }
            },
            trigger: "blur",
          },
        ],
        email: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, "");
              this.invoiceForm.email = val;
              if (!val) {
                callback(new Error("邮箱不能为空"));
              } else if (!validEmail(val)) {
                callback(new Error("格式错误"));
              } else {
                callback();
              }
            },
            trigger: "blur",
          },
        ],
        //     else if (!validTaxNum(val)) {
        //   callback(new Error('格式错误'))
        // }
        tax_number: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, "");
              this.invoiceForm.tax_number = val;
              if (!val) {
                callback(new Error("企业税号不能为空"));
              } else {
                callback();
              }
            },
            trigger: "blur",
          },
        ],
        // opened_bank_account: [
        //   {
        //     validator: (rules, value, callback) => {
        //       let val = value.replace(/\s/g, '');
        //       this.invoiceForm.opened_bank_account = val
        //       if (!val) {
        //         callback()
        //       } else if (!validBankAccount(val)) {
        //         callback('格式错误')
        //       } else {
        //         callback()
        //       }
        //     },
        //     trigger: 'blur'
        //   }
        // ],
        // reg_mobile: [
        //   {
        //     validator: (rules, value, callback) => {
        //       let val = value.replace(/\s/g, '');
        //       this.invoiceForm.reg_mobile = val
        //       if (!val) {
        //         callback()
        //       } else if (!validMobile(val)) {
        //         callback('格式错误')
        //       } else {
        //         callback()
        //       }
        //     }, trigger: 'blur'
        //   }
        // ],
        // opened_bank_name: [
        //   {
        //     validator: (rules, value, callback) => {
        //       let val = value.replace(/\s/g, '');
        //       this.invoiceForm.opened_bank_name = val
        //       if (!val) {
        //         callback()
        //       } else if (!validHasChinese(val)) {
        //         callback(new Error('格式错误'))
        //       } else {
        //         callback()
        //       }
        //     }, trigger: 'blur'
        //   }
        // ],
        // reg_address: [
        //   {
        //     validator: (rules, value, callback) => {
        //       let val = value.replace(/\s/g, '');
        //       this.invoiceForm.reg_address = val
        //       if (!val) {
        //         callback()
        //       } else if (!validHasChinese(val)) {
        //         callback(new Error('格式错误'))
        //       } else {
        //         callback()
        //       }
        //     }, trigger: 'blur'
        //   }
        // ]
      },
      activeTabs: "5",
      disabledCompanyAuth: false,
      page: 1,
      company_list: [],
      isRefresh: true,
      // 认证成功之后，disabled认证按钮
      auth_success: false,

      basicsInfoForm: {
        name: "",
        mobile: "",
        email: "",
        ide: "",
        province: "",
        avatar: "",
        is_accept_message: false,
      },
      imageId: "",
      ide_list: [
        {
          label: "高校",
          value: 1,
        },
        {
          label: "科研院所",
          value: 2,
        },
        {
          label: "企业",
          value: 3,
        },
        {
          label: "医院",
          value: 4,
        },
        {
          label: "其他",
          value: 5,
        },
      ],
      basicsInfoRules: {
        name: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, "");
              this.basicsInfoForm.name = val;
              callback();
            },
            trigger: "blur",
          },
        ],
        email: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, "");
              this.basicsInfoForm.email = val;
              if (!val) {
                callback();
              } else if (!validEmail(val)) {
                callback(new Error("邮箱格式不正确"));
              } else {
                callback();
              }
            },
            trigger: "blur",
          },
        ],
        mobile: [
          { required: true, trigger: "blur", message: "请输入电话号码" },
          { validator: validateMobileNumber, trigger: "blur" },
        ],
      },

      addressTable: [],
      dialogVisible: false,
      addressForm: {
        id: "",
        name: "",
        mobile: "",
        province: [""],
        address: "",
      },
      addressRules: {
        name: [
          { required: true, trigger: "blur", message: "请输入姓名" },
          { validator: verifyName, trigger: "blur" },
        ],
        mobile: [
          { required: true, trigger: "blur", message: "请输入电话号码" },
          { validator: validateMobileNumber, trigger: "blur" },
        ],
        province: [
          { required: true, trigger: "change", message: "请选择地区" },
        ],
        address: [
          { required: true, trigger: "blur", message: "请输入详细地址" },
        ],
      },

      invoiceTableData: [],
      invoiceDialog: false,
    };
  },
  computed: {
    ...mapGetters(["avatar", "authInfo"]),
  },
  async mounted() {
    this.applyProfileRouteIntent();
    // this.getStoreAuthInfo()
    // this.profile_form['mobile'] = this.authInfo['mobile']

    //  添加自动检索企业列表的触底事件
    // const company_list = document.querySelector('.el-autocomplete-suggestion__wrap')
    // company_list.addEventListener('scroll', e => {
    //   const {scrollTop, clientHeight, scrollHeight} = e.target
    //   if (scrollTop + clientHeight === scrollHeight) {
    //     if (this.isRefresh) {
    //       this.getCompanyList(this.company_info['name'], this.page)
    //     }
    //   }
    // })
  },

  watch: {
    $route(to) {
      if (to.name !== "Profile") return;
      const active = to.query.active ?? to.params.active;
      if (String(active) !== "2" || to.query.openInvoice !== "1") return;
      this.handleTabChange("2");
      this.$nextTick(() => this.openAddInvoiceDialog());
    },
    // 监听用户选择的企业信息的修改
    "company_info.name": {
      handler(n) {
        if (!n) {
          this.handleSelect({}, false);
        }
      },
    },
  },
  methods: {
    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),
    // 获取公司列表
    getCompanyList(keyword, page) {
      fetchCompanyInfoApi(keyword, page).then((res) => {
        if (res.res) {
          if (res.obj.data.length !== 10) {
            this.isRefresh = false;
          }
          res.obj.data.forEach((item) => {
            this.company_list.push(item);
          });
          this.page += 1;
        }
      });
    },

    // 选中企业
    handleSelect(e, disabledCompanyAuth = true) {
      this.company_info["id"] = e.id || "";
      this.company_info["name"] = e.name || "";
      this.company_info["areaId"] = e.areaId ? e.areaId.split(",") : "";
      this.company_info["address"] = e.address || "";
      this.company_info["contractPhone"] = e.contractPhone || "";
      this.company_info["taxNum"] = e.taxNum || "";
      this.company_info["bank"] = e.bank || "";
      this.company_info["bankCardNum"] = e.bankCardNum || "";
      // 禁止修改企业认证信息
      this.disabledCompanyAuth = disabledCompanyAuth;
    },

    // 远程搜索企业特名称
    async querySearchAsync(keyword, cb) {
      this.handleSelect({ name: keyword }, false);
      this.page = 1;
      this.isRefresh = true;
      const res = await fetchCompanyInfoApi(keyword, this.page);
      if (res.res) {
        this.company_list = res.obj.data;
        cb(this.company_list);
        if (res.obj.data.length !== 10) {
          this.isRefresh = false;
        }
        this.page += 1;
      } else {
        cb();
      }
    },

    // 获取一下store里的信息
    getStoreAuthInfo() {
      // userType 1个人 2企业
      if (this.authInfo) {
        // 判断store里面村的是哪种身份
        if (this.authInfo.userType === 1 && this.authInfo.trueName) {
          // this.userType为已认证的身份
          // this.auth_type 为当前选中的身份
          this.userType = this.auth_type = 1;
          const {
            company_name,
            trueName,
            mobile,
            email,
            idcard,
            area_id,
            address,
          } = this.authInfo;
          this.person_info["company_name"] = company_name;
          this.person_info["trueName"] = trueName;
          // this.person_info['mobile'] = mobile
          this.person_info["email"] = email;
          this.person_info["idcard"] = idcard;
          this.person_info["area_id"] = area_id.split(",");
          this.person_info["addreddInfo"] = address;
        } else if (this.authInfo.userType === 2 && this.authInfo.company_name) {
          this.userType = this.auth_type = 2;
          const {
            company_name,
            country,
            areaId,
            address,
            mobile,
            taxNum,
            bank,
            bankCardNum,
            company_id,
          } = this.authInfo;
          // authInfo需要加一个公司id
          this.company_info["id"] = company_id || "";
          this.company_info["name"] = company_name;
          this.company_info["country"] = country;
          this.company_info["areaId"] = areaId.split(",");
          this.company_info["address"] = address;
          this.company_info["contractPhone"] = mobile;
          this.company_info["taxNum"] = taxNum;
          this.company_info["bank"] = bank;
          this.company_info["bankCardNum"] = bankCardNum;
          if (company_id) {
            this.disabledCompanyAuth = true;
          }
        }
      }
    },

    // 保存认证信息
    saveAuthInfo() {
      let params, form_name;
      // 个人
      if (this.auth_type === 1) {
        params = { ...this.person_info };
        form_name = "person";
        params.area_id = params.area_id[2];
      } else {
        if (!this.company_info.name)
          return this.$notify.warning("请输入企业名称");
        // name提交, company_name获取
        params = {
          id: this.company_info["id"],
          name: this.company_info["name"],
          country: this.company_info["country"],
          areaId: this.company_info["areaId"][2],
          address: this.company_info["address"],
          mobile: this.company_info["contractPhone"],
          taxNum: this.company_info["taxNum"],
          bank: this.company_info["bank"],
          bankCardNum: this.company_info["bankCardNum"],
        };
        form_name = "company";
      }

      this.$refs[form_name].validate((valid) => {
        if (valid) {
          this.saving = true;
          params["userType"] = this.auth_type;
          if (this.auth_type === 1) {
            savaAuthInfoApi(params)
              .then((res) => {
                if (res.res) {
                  params["address"] = params["addreddInfo"];
                  delete params["addreddInfo"];
                  this.$store.commit("user/SET_AUTH_INFO", params);
                  this.$store.commit("user/SET_NAME", params["trueName"]);
                  this.userType = this.auth_type;
                  this.auth_success = true;
                }
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
              })
              .finally((_) => {
                this.saving = false;
              });
          } else {
            saveAuthCompanyInfoApi(params)
              .then((res) => {
                if (res.res) {
                  params["company_name"] = params["name"];
                  delete params["name"];
                  this.$store.commit("user/SET_AUTH_INFO", params);
                  this.$store.commit("user/SET_NAME", params["name"]);
                  this.userType = this.auth_type;
                  this.auth_success = true;
                }
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
              })
              .finally((_) => {
                this.saving = false;
              });
          }
        } else {
          return false;
        }
      });
    },

    // 更改认证方式
    changeAuthType(e) {
      let flag = this.disabledCompanyAuth;
      if (e === 1) {
        this.$refs["company"].resetFields();
      } else {
        this.$refs["person"].resetFields();
      }
      if (this.userType === e) {
        this.getStoreAuthInfo();
      }
    },

    // 确定修改密码
    confirmChangePwd() {
      this.$refs["changePwdForm"].validate((valid) => {
        if (valid) {
          changePwdApi({
            oldPassword: this.changePwd.oldPwd,
            password: this.changePwd.newPwd,
            password1: this.changePwd.confirmNewPwd,
          }).then((res) => {
            this.$notify({
              title: "提示",
              type: res.res ? "success" : "warning",
              message: res.resMsg,
            });
            if (res.res) {
              this.$refs["changePwdForm"].resetFields();
            }
          });
        } else {
          return false;
        }
      });
    },

    // 获取基本信息
    getUserInfo() {
      fetchbasicInfoApi().then((res) => {
        if (res.res) {
          const {
            mobile,
            trueName,
            email,
            identity,
            area_id,
            avatar,
            is_accept_message = 1,
          } = res.obj;
          this.basicsInfoForm.name = trueName;
          this.basicsInfoForm.mobile = mobile;
          this.basicsInfoForm.ide = identity;
          this.basicsInfoForm.email = email;
          this.basicsInfoForm.province = area_id ? area_id.split(",") : "";
          this.basicsInfoForm.avatar = avatar;
          this.basicsInfoForm.is_accept_message = !is_accept_message;
        }
      });
    },

    // 获取收件地址
    getAddressList() {
      fetchAddressListApi().then((res) => {
        if (res.res) {
          const payload = res.obj || res.data || {};
          this.addressTable = payload.expUserDeliveryAddresses || [];
        }
      });
    },

    // Tab 切换（须用 tab-change：tab-click 时 activeTabs 尚未更新，首次点击不会拉对应列表）
    handleTabChange(name) {
      this.activeTabs = String(name);
      const idx = Number(name);
      if (idx === 1) {
        this.$refs["changePwdForm"]?.resetFields();
      }
      if (idx === 2) {
        this.getInvoiceList();
      }
      if (idx === 5) {
        this.getUserInfo();
      }
      if (idx === 6) {
        this.getAddressList();
      }
    },

    // 获取发票信息
    getInvoiceInfo() {
      this.CHANGE_LOADING(1);
      getUserInvoiceInfoApi()
        .then((res) => {
          if (res.res) {
            const {
              invoice_title,
              taxNum,
              bank,
              bankCardNum,
              address,
              mobile,
              email,
              address_info,
            } = res.obj;
            this.invoiceForm["rise"] = invoice_title;
            this.invoiceForm["tax_id"] = taxNum;
            this.invoiceForm["bank_name"] = bank;
            this.invoiceForm["bank_account"] = bankCardNum;
            this.invoiceForm["reg_address"] = address;
            this.invoiceForm["reg_mobile"] = mobile;
            this.invoiceForm["email"] = email;
            this.invoiceForm["receipt_address"] = address_info;
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    //   上传头像
    uploadAvatar() {
      const file = this.$refs["upload"].files[0],
        type = file.type,
        size = file.size;
      if (type !== "image/jpeg" && type !== "image/png") {
        this.$refs["upload"].value = "";
        return this.$notify.warning({
          title: "提示",
          message: "只能上传PNG和JPG格式",
        });
      }

      if (size / 1000 > 2048) {
        this.$refs["upload"].value = "";
        return this.$notify.warning({
          title: "提示",
          message: "头像大小不能超过2M",
        });
      }

      this.CHANGE_LOADING(1);
      uploadAvatarApi(file)
        .then((res) => {
          if (res.res) {
            this.basicsInfoForm["avatar"] = res.obj["url"];
            this.imageId = res.obj["imageId"];
          } else {
            this.$notify({
              type: "warning",
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally((_) => {
          this.$refs["upload"].value = "";
          this.CHANGE_LOADING();
        });
    },

    // 更改省市区
    handleChange(type) {
      if (type === 1) {
        this.person_info.addreddInfo = "";
      } else {
        this.company_info.address = "";
      }
    },

    // 保存基本信息
    saveBaseInfo() {
      this.$refs["basicInfo"].validate((valid) => {
        if (valid) {
          this.CHANGE_LOADING(1);
          const {
            name,
            mobile,
            email,
            ide,
            province,
            avatar,
            is_accept_message,
          } = this.basicsInfoForm;
          updateBasicInfoApi({
            userName: name,
            mobile: mobile,
            email: email,
            identity: ide,
            area_id: province ? province.join() : "",
            imageId: this.imageId,
            is_accept_message: is_accept_message ? 0 : 1,
          })
            .then((res) => {
              this.$notify({
                type: res.res ? "success" : "warning",
                message: res.resMsg,
                title: "提示",
              });
              if (res.res) {
                this.$store.commit("user/SET_AVATAR", avatar);
              }
            })
            .finally((_) => {
              this.CHANGE_LOADING();
            });
        } else {
          return false;
        }
      });
    },

    applyProfileRouteIntent() {
      const active = this.$route.query.active ?? this.$route.params.active;
      if (!active) {
        this.handleTabChange(this.activeTabs);
        return;
      }
      this.handleTabChange(String(active));
      if (String(active) === "2") {
        const shouldOpen =
          this.$route.query.openInvoice === "1" ||
          this.$route.params.active === "2";
        if (shouldOpen) {
          this.$nextTick(() => this.openAddInvoiceDialog());
        }
      }
    },

    openAddInvoiceDialog() {
      this.invoiceForm.id = "";
      this.invoiceDialog = true;
      this.$nextTick(() => {
        this.$refs.invoiceForm?.resetFields();
      });
    },

    handleClose() {
      this.$refs["addressForm"]?.resetFields();
      this.$refs["invoiceForm"]?.resetFields();
      // 因为id字段没有使用,所以需要手动清除
      this.addressForm.id = "";
      this.invoiceForm.id = "";
      this.dialogVisible = false;
      this.invoiceDialog = false;
    },

    // 添加/编辑 收件地址
    confirmAddAddress() {
      this.$refs["addressForm"].validate((e) => {
        if (e) {
          this.CHANGE_LOADING(1);
          const { name, mobile, province, address, id } = this.addressForm;
          if (id) {
            updateAddressApi({
              id,
              delivery_name: name,
              delivery_phone: mobile,
              delivery_address: province.join(),
              detail_address: address,
            })
              .then((res) => {
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
                if (res.res) {
                  this.handleClose();
                  let newAddress = "",
                    arr = this.address;
                  let obj = arr.find((item) => item.value === province[0]);
                  newAddress += obj.label;
                  arr = obj.children;
                  obj = arr.find((item) => item.value === province[1]);
                  newAddress += obj.label;
                  arr = obj.children;
                  obj = arr.find((item) => item.value === province[2]);
                  newAddress += obj.label;

                  let idx = this.addressTable.findIndex(
                    (item) => item.id === id
                  );
                  this.$set(this.addressTable[idx], "delivery_name", name);
                  this.$set(this.addressTable[idx], "delivery_phone", mobile);
                  this.$set(
                    this.addressTable[idx],
                    "delivery_address_id",
                    province.join()
                  );
                  this.$set(this.addressTable[idx], "detail_address", address);
                  this.$set(
                    this.addressTable[idx],
                    "delivery_address",
                    newAddress
                  );
                }
              })
              .finally((_) => {
                this.CHANGE_LOADING();
              });
          } else {
            addNewAddressApi({
              delivery_name: name,
              delivery_phone: mobile,
              delivery_address: province.join(),
              detail_address: address,
            })
              .then((res) => {
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
                if (res.res) {
                  this.handleClose();
                  this.getAddressList();
                }
              })
              .finally((_) => {
                this.CHANGE_LOADING();
              });
          }
        } else {
          return false;
        }
      });
    },

    // 编辑地址
    // dialog第一次打开时得表单情况会被当作初始化情况
    editAddress(row) {
      this.dialogVisible = true;
      this.$nextTick(() => {
        const {
          id,
          delivery_address_id,
          delivery_name,
          delivery_phone,
          detail_address,
        } = row;
        this.addressForm.id = id;
        this.addressForm.name = delivery_name;
        this.addressForm.mobile = delivery_phone;
        this.addressForm.province = delivery_address_id.split(",");
        this.addressForm.address = detail_address;
      });
    },

    changeAddressStatus(id, type) {
      delAddressApi({
        id,
        type,
      }).then((res) => {
        if (res.res) {
          let idx = this.addressTable.findIndex((item) => item.id === id);
          if (type === 1) {
            this.addressTable.splice(idx, 1);
          } else {
            let defaulted = this.addressTable.findIndex(
              (item) => item.is_default === 1
            );
            this.$set(this.addressTable[defaulted], "is_default", 0);
            this.$set(this.addressTable[idx], "is_default", 1);
          }
        } else {
          this.$notify({
            type: "warning",
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },

    // 删除地址
    deleteAddress(id) {
      this.$confirm("删除该地址?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.changeAddressStatus(id, 1);
      });
    },

    // 获取发票列表
    getInvoiceList() {
      fetchInvoiceListApi().then((res) => {
        if (res.res) {
          const payload = res.obj || res.data || {};
          this.invoiceTableData = payload.invoiceInfs || [];
        } else {
          this.invoiceTableData = [];
          this.$notify.warning({
            title: "提示",
            message: res.resMsg || "获取发票列表失败",
          });
        }
      });
    },

    // 新增发票
    confirmAddInvoice() {
      this.$refs["invoiceForm"].validate((e) => {
        if (e) {
          const {
            id,
            invoice_title,
            tax_number,
            opened_bank_name,
            opened_bank_account,
            email,
            reg_address,
            reg_mobile,
          } = this.invoiceForm;

          this.CHANGE_LOADING(1);
          if (id) {
            updateInvoiceApi({
              id,
              invoice_title: invoice_title,
              taxNum: tax_number,
              bank: opened_bank_name,
              bankCardNum: opened_bank_account,
              address: reg_address,
              mobile: reg_mobile,
              email: email,
            })
              .then((res) => {
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
                if (res.res) {
                  this.handleClose();
                  let idx = this.invoiceTableData.findIndex(
                    (item) => item.id === id
                  );
                  this.$set(
                    this.invoiceTableData[idx],
                    "invoice_title",
                    invoice_title
                  );
                  this.$set(this.invoiceTableData[idx], "taxNum", tax_number);
                  this.$set(this.invoiceTableData[idx], "email", email);
                  this.$set(
                    this.invoiceTableData[idx],
                    "bank",
                    opened_bank_name
                  );
                  this.$set(
                    this.invoiceTableData[idx],
                    "bankCardNum",
                    opened_bank_account
                  );
                  this.$set(this.invoiceTableData[idx], "address", reg_address);
                  this.$set(this.invoiceTableData[idx], "mobile", reg_mobile);
                }
              })
              .finally((_) => {
                this.CHANGE_LOADING();
              });
          } else {
            addNewInvoiceApi({
              invoice_title: invoice_title,
              taxNum: tax_number,
              bank: opened_bank_name,
              bankCardNum: opened_bank_account,
              address: reg_address,
              mobile: reg_mobile,
              email: email,
            })
              .then((res) => {
                this.$notify({
                  type: res.res ? "success" : "warning",
                  message: res.resMsg,
                  title: "提示",
                });
                if (res.res) {
                  this.handleClose();
                  this.getInvoiceList();
                }
              })
              .finally((_) => {
                this.CHANGE_LOADING();
              });
          }
        } else {
          return false;
        }
      });
    },

    changeInvoiceStatus(id, type) {
      delInvoiceApi({
        id,
        type,
      }).then((res) => {
        if (res.res) {
          let idx = this.invoiceTableData.findIndex((item) => item.id === id);
          if (type === 1) {
            this.invoiceTableData.splice(idx, 1);
          } else {
            let defaulted = this.invoiceTableData.findIndex(
              (item) => item.is_default === 1
            );
            this.$set(this.invoiceTableData[defaulted], "is_default", 0);
            this.$set(this.invoiceTableData[idx], "is_default", 1);
          }
        } else {
          this.$notify({
            type: "warning",
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },

    //   删除发票
    delInvoice(id) {
      this.$confirm("删除该发票?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.changeInvoiceStatus(id, 1);
      });
    },

    // 编辑发票
    editInvoice(row) {
      this.invoiceDialog = true;
      this.$nextTick(() => {
        const {
          id,
          address,
          bank,
          bankCardNum,
          email,
          invoice_title,
          mobile,
          taxNum,
        } = row;
        this.invoiceForm.id = id;
        this.invoiceForm.invoice_title = invoice_title;
        this.invoiceForm.tax_number = taxNum;
        this.invoiceForm.opened_bank_name = bank;
        this.invoiceForm.opened_bank_account = bankCardNum;
        this.invoiceForm.email = email;
        this.invoiceForm.reg_address = address;
        this.invoiceForm.reg_mobile = mobile;
      });
    },
    numberToChinese(num) {
      const chineseNums = [
        "零",
        "一",
        "二",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
      ];
      return num
        .toString()
        .split("")
        .map((digit) => chineseNums[digit])
        .join("");
    },
  },
};
</script>

<template>
  <div class="profile">
    <el-tabs type="border-card" @tab-change="handleTabChange" v-model="activeTabs">
      <el-tab-pane name="5" label="基本信息" style="position: relative">
        <el-form
          :model="basicsInfoForm"
          :rules="basicsInfoRules"
          ref="basicInfo"
          label-position="top"
          class="basic-info"
        >
          <el-form-item label="姓名" prop="name">
            <el-input
              clearable
              v-model="basicsInfoForm.name"
              placeholder="请输入姓名"
              maxlength="20"
            ></el-input>
            <span style="color: #c9c9c9">（限制少于20个字符）</span>
          </el-form-item>
          <el-form-item label="电话" prop="mobile">
            <el-input
              clearable
              v-model="basicsInfoForm.mobile"
              :disabled="true"
              placeholder="请输入电话"
            ></el-input>
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input
              clearable
              v-model="basicsInfoForm.email"
              placeholder="请输入邮箱"
            ></el-input>
          </el-form-item>
          <el-form-item label="身份" prop="ide">
            <el-select
              clearable
              v-model="basicsInfoForm.ide"
              placeholder="请选择身份"
            >
              <el-option
                v-for="item in ide_list"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="所在省市区" prop="province">
            <el-cascader
              v-model="basicsInfoForm.province"
              :options="address"
              clearable
              placeholder="请选择所在省市区"
            />
          </el-form-item>
          <!--          <el-form-item label="接手公众号消息" prop="is_accept_message">-->
          <!--            <el-switch v-model="basicsInfoForm.is_accept_message"></el-switch>-->
          <!--          </el-form-item>-->
        </el-form>

        <img
          v-if="basicsInfoForm.avatar"
          class="user-head"
          @click="$refs['upload'].click()"
          :src="basicsInfoForm.avatar"
          alt="用户头像"
        />
        <img
          v-else
          class="user-head"
          src="@client/static/logo.png"
          alt="用户头像"
          @click="$refs['upload'].click()"
        />
        <input type="file" v-show="false" ref="upload" @change="uploadAvatar" />

        <el-button
          size="medium"
          class="submit-btn"
          type="primary"
          @click="saveBaseInfo"
          >保&nbsp;存</el-button
        >
      </el-tab-pane>
      <!--      <el-tab-pane name="0" label="账号信息">-->
      <!--        <div class="profile-form">-->
      <!--          <div class="auth-type">-->
      <!--            <span>认证身份：</span>-->
      <!--            <el-radio @input="changeAuthType" v-model="auth_type" :label="1">个人</el-radio>-->
      <!--            <el-radio @input="changeAuthType" v-model="auth_type" :label="2">企业</el-radio>-->
      <!--          </div>-->

      <!--          <el-form label-position="right" label-width="120px" ref="person" :model="person_info"-->
      <!--                   :rules="person_info_rules" v-show="auth_type === 1">-->
      <!--            <el-form-item label="公司/学校：" prop="company_name">-->
      <!--              <el-input v-model="person_info.company_name"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="姓名：" prop="trueName">-->
      <!--              <el-input v-model="person_info.trueName"></el-input>-->
      <!--            </el-form-item>-->
      <!--            &lt;!&ndash;            <el-form-item label="手机号：" prop="mobile">&ndash;&gt;-->
      <!--            &lt;!&ndash;              <el-input v-model="person_info.mobile"></el-input>&ndash;&gt;-->
      <!--            &lt;!&ndash;            </el-form-item>&ndash;&gt;-->
      <!--            <el-form-item label="电子邮件：" prop="email">-->
      <!--              <el-input v-model="person_info.email"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="身份证号：" prop="idcard">-->
      <!--              <el-input v-model="person_info.idcard"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="省/市/区：" prop="area_id">-->
      <!--              &lt;!&ndash;              <el-input v-model="person_info.area_id"></el-input>&ndash;&gt;-->
      <!--              <el-cascader-->
      <!--                v-model="person_info.area_id"-->
      <!--                :options="address"-->
      <!--                clearable-->
      <!--                placeholder="请选择地址"-->
      <!--                @change="handleChange(1)"/>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="收货地址：" prop="addreddInfo">-->
      <!--              <el-input v-model="person_info.addreddInfo"></el-input>-->
      <!--            </el-form-item>-->
      <!--          </el-form>-->

      <!--          <el-form label-position="right" label-width="120px" ref="company" :model="company_info"-->
      <!--                   :rules="company_info_rules" v-show="auth_type === 2">-->
      <!--            &lt;!&ndash;            <el-form-item label="头像：">&ndash;&gt;-->
      <!--            &lt;!&ndash;              <img class="user-head" :src="avatar" alt="">&ndash;&gt;-->
      <!--            &lt;!&ndash;            </el-form-item>&ndash;&gt;-->
      <!--            <el-form-item label="企业名称：" prop="name">-->
      <!--              <el-autocomplete-->
      <!--                v-model="company_info.name"-->
      <!--                value-key="name"-->
      <!--                :fetch-suggestions="querySearchAsync"-->
      <!--                placeholder="请输入企业名称"-->
      <!--                @select="handleSelect"-->
      <!--              ></el-autocomplete>-->
      <!--              &lt;!&ndash;              <el-input v-model="company_info.name"></el-input>&ndash;&gt;-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="注册国家地址：" prop="country">-->
      <!--              <el-input v-model="company_info.country" :disabled="true"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="省/市/区：" prop="areaId">-->
      <!--              &lt;!&ndash;              <el-input :disabled="disabledCompanyAuth" v-model="company_info.areaId"></el-input>&ndash;&gt;-->
      <!--              <el-cascader-->
      <!--                :disabled="disabledCompanyAuth"-->
      <!--                v-model="company_info.areaId"-->
      <!--                :options="address"-->
      <!--                clearable-->
      <!--                placeholder="请选择地址"-->
      <!--                @change="handleChange(2)"/>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="详细地址：" prop="address">-->
      <!--              <el-input :disabled="disabledCompanyAuth" v-model="company_info.address"></el-input>-->
      <!--            </el-form-item>-->
      <!--            &lt;!&ndash;            <el-form-item label="电话：" prop="contractPhone">&ndash;&gt;-->
      <!--            &lt;!&ndash;              <el-input v-model="company_info.contractPhone"></el-input>&ndash;&gt;-->
      <!--            &lt;!&ndash;            </el-form-item>&ndash;&gt;-->
      <!--            <el-form-item label="纳税人识别号：" prop="taxNum">-->
      <!--              <el-input :disabled="disabledCompanyAuth" v-model="company_info.taxNum"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="企业开户银行：" prop="bank">-->
      <!--              <el-input :disabled="disabledCompanyAuth" v-model="company_info.bank"></el-input>-->
      <!--            </el-form-item>-->
      <!--            <el-form-item label="企业银行账户：" prop="bankCardNum">-->
      <!--              <el-input :disabled="disabledCompanyAuth" v-model="company_info.bankCardNum"></el-input>-->
      <!--            </el-form-item>-->
      <!--          </el-form>-->
      <!--          <el-button v-if="!auth_success" size="medium" class="submit-btn" :loading="saving" type="primary"-->
      <!--                     @click="saveAuthInfo">-->
      <!--            认&nbsp;证-->
      <!--          </el-button>-->
      <!--        </div>-->
      <!--      </el-tab-pane>-->
      <el-tab-pane name="2" label="发票信息">
        <div class="invoice-list btf-roll">
          <div
            class="invoice-item"
            v-for="(item, idx) in invoiceTableData"
            :key="idx"
          >
            <div class="title">

              <span class="fapiao">发票{{ numberToChinese(idx + 1) }}： <!-- <i class="el-icon-caret-bottom"></i> --> </span>
              <span class="default" v-if="item.is_default">默认</span>
            </div>

            <div class="invoiceBox">
              <div class="rise syx_style">
                <span>发票抬头：</span> <span>{{ item.invoice_title }}</span>
              </div>
              <div class="tax-num syx_style">
                <span>企业税号：</span> <span>{{ item.taxNum }}</span>
              </div>
              <div class="bank-name syx_style">
                <span>开户行名称：</span> <span>{{ item.bank }}</span>
              </div>
              <div class="bank-account syx_style">
                <span>开户行账号：</span> <span>{{ item.bankCardNum }}</span>
              </div>
              <div class="bank-account syx_style">
                <span>邮箱：</span> <span>{{ item.email }}</span>
              </div>
              <div class="reg-address syx_style">
                <span>注册地址：</span> <span>{{ item.address }}</span>
              </div>
              <div class="reg-mobile syx_style">
                <span>注册电话号码：</span> <span>{{ item.mobile }}</span>
              </div>
              <div class="handle">
                <el-button size="mini" type="warning" @click="editInvoice(item)"
                  >编辑</el-button
                >
                <el-button
                  size="mini"
                  type="warning"
                  @click="delInvoice(item.id)"
                  >删除</el-button
                >
                <el-button
                  size="mini"
                  type="warning"
                  v-if="!item.is_default"
                  class="set-default"
                  @click="changeInvoiceStatus(item.id, 2)"
                  >设为默认
                </el-button>
              </div>
            </div>
          </div>
        </div>
        <el-button
          style="margin-top: 10px"
          size="small"
          type="warning"
          v-if="invoiceTableData.length < 10"
          @click="openAddInvoiceDialog"
          >添加发票
        </el-button>
      </el-tab-pane>
      <el-tab-pane name="6" label="收件地址">
        <el-table :data="addressTable" style="width: 100%">
          <el-table-column prop="delivery_name" label="收件人姓名" width="180">
          </el-table-column>
          <el-table-column prop="delivery_phone" label="电话号码" width="180">
          </el-table-column>
          <el-table-column label="地址">
            <template #default="{ row: { delivery_address, detail_address } }">
              {{ delivery_address.replace(/\s/g, "") }}{{ detail_address }}
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button type="text" @click="editAddress(row)">编辑</el-button>
              <el-button type="text" @click="deleteAddress(row.id)"
                >删除</el-button
              >
              <div class="default" v-if="row.is_default">默认</div>
              <el-button
                type="text"
                v-else
                class="set-default"
                @click="changeAddressStatus(row.id, 2)"
                >设为默认
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button
          v-if="addressTable.length < 10"
          type="text"
          @click="dialogVisible = true"
          >新增地址</el-button
        >
      </el-tab-pane>
      <el-tab-pane name="1" label="修改密码">
        <div class="profile-form">
          <el-form
            label-position="right"
            label-width="110px"
            :model="changePwd"
            :rules="changePwdRules"
            ref="changePwdForm"
          >
            <el-form-item label="旧密码：" prop="oldPwd">
              <el-input
                class="el-input"
                show-password
                v-model="changePwd.oldPwd"
                maxlength="20"
                placeholder="请输入旧密码"
              ></el-input>
            </el-form-item>
            <el-form-item label="新密码：" prop="newPwd">
              <el-input
                class="el-input"
                show-password
                v-model="changePwd.newPwd"
                maxlength="20"
                placeholder="请输入新密码"
              ></el-input>
            </el-form-item>
            <el-form-item label="确认新密码：" prop="confirmNewPwd">
              <el-input
                class="el-input"
                show-password
                v-model="changePwd.confirmNewPwd"
                maxlength="20"
                placeholder="请再次输入新密码"
              ></el-input>
            </el-form-item>
          </el-form>
          <el-button
            size="medium"
            class="submit-btn"
            type="primary"
            @click="confirmChangePwd"
            >确&nbsp;定</el-button
          >
        </div>
      </el-tab-pane>

      <!--      <el-tab-pane name="3" label="个人资料">-->
      <!--        <el-form label-position="right" label-width="120px" ref="profile" :model="profile_form" v-loading="loading">-->
      <!--          <el-form-item label="头像：">-->
      <!--            <img class="avatar" @click="$refs['upload'].click()" :src="profile_form['avatar']" alt=""-->
      <!--                 v-if="profile_form.avatar">-->
      <!--            <svg-icon v-else icon-class="default-head"-->
      <!--                      class-name="default-head" @click="$refs['upload'].click()"></svg-icon>-->
      <!--            <input type="file" v-show="false" ref="upload" @change="uploadAvatar">-->
      <!--          </el-form-item>-->
      <!--          <el-form-item label="手机号：">-->
      <!--            <el-input v-model="profile_form.mobile" :disabled="true"></el-input>-->
      <!--          </el-form-item>-->
      <!--        </el-form>-->
      <!--      </el-tab-pane>-->
    </el-tabs>

    <el-dialog
      :title="addressForm.id ? '编辑地址' : '新增地址'"
      v-model="dialogVisible"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      @close="handleClose"
    >
      <el-form
        :model="addressForm"
        label-position="top"
        :rules="addressRules"
        ref="addressForm"
      >
        <el-form-item label="收件人姓名:" prop="name">
          <el-input
            placeholder="请输入收件人名称"
            v-model="addressForm.name"
            maxlength="20"
          ></el-input>
        </el-form-item>
        <el-form-item label="电话号码:" prop="mobile">
          <el-input
            placeholder="请输入电话号码"
            v-model="addressForm.mobile"
          ></el-input>
        </el-form-item>
        <el-form-item label="选择地区:" prop="province">
          <el-cascader
            v-model="addressForm.province"
            :options="address"
            clearable
            placeholder="请选择地区"
          />
        </el-form-item>
        <el-form-item label="详细地址:" prop="address">
          <el-input
            type="textarea"
            placeholder="请输入详细地址"
            v-model="addressForm.address"
            maxlength="60"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">取&nbsp;消</el-button>
          <el-button type="primary" @click="confirmAddAddress"
            >确&nbsp;定</el-button
          >
        </div>
      </template>
    </el-dialog>

    <el-dialog
      :title="invoiceForm.id ? '编辑发票' : '新增发票'"
      v-model="invoiceDialog"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      @close="handleClose"
    >
      <el-form
        :model="invoiceForm"
        label-position="right"
        label-width="100px"
        :rules="invoiceFormRules"
        ref="invoiceForm"
      >
        <el-form-item
          label="发票抬头:"
          prop="invoice_title"
          class="required-label"
        >
          <el-input
            placeholder="请输入发票抬头"
            v-model="invoiceForm.invoice_title"
            maxlength="30"
          ></el-input>
        </el-form-item>
        <el-form-item
          label="企业税号:"
          prop="tax_number"
          class="required-label"
        >
          <el-input
            placeholder="请输入企业税号"
            v-model="invoiceForm.tax_number"
            maxlength="30"
          ></el-input>
        </el-form-item>
        <el-form-item label="邮箱:" prop="email" class="required-label">
          <el-input
            placeholder="请输入邮箱"
            v-model="invoiceForm.email"
            maxlength="30"
          ></el-input>
        </el-form-item>
        <el-form-item label="开户行名称:" prop="opened_bank_name">
          <el-input
            placeholder="请输入开户行名称"
            v-model="invoiceForm.opened_bank_name"
            maxlength="30"
          ></el-input>
        </el-form-item>
        <el-form-item label="开户行账号:" prop="opened_bank_account">
          <el-input
            placeholder="请输入开户行账号"
            v-model="invoiceForm.opened_bank_account"
            maxlength="30"
          ></el-input>
        </el-form-item>
        <el-form-item label="注册地址:" prop="reg_address">
          <el-input
            placeholder="请输入注册地址"
            v-model="invoiceForm.reg_address"
            maxlength="40"
          ></el-input>
        </el-form-item>
        <el-form-item label="注册电话:" prop="reg_mobile">
          <el-input
            placeholder="请输入注册电话"
            v-model="invoiceForm.reg_mobile"
            maxlength="11"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">取&nbsp;消</el-button>
          <el-button type="primary" @click="confirmAddInvoice"
            >确&nbsp;定</el-button
          >
        </div>
      </template>
    </el-dialog>
  </div>
</template>
<!--//width: 30% !important;-->
<!--//&:nth-child(2) {-->
<!--//  margin: 0 5%;-->
<!--//}-->
<!--//.el-input {-->
<!--//  width: 100%;-->
<!--//}-->
<style scoped>
/deep/ .el-table__row {
  .set-default {
    display: none;
  }

  &:hover {
    .set-default {
      display: inline-block;
    }
  }
}

/deep/.el-tabs__content {
  max-height: 632px;
  overflow: auto;
}

/deep/ .el-tabs--border-card {
  width: 800px !important;
}

/deep/ .el-dialog {
  width: 700px !important;
}

/deep/ .el-textarea__inner {
  width: 400px;
  max-height: 105px;
}

.el-select {
  width: 400px;
}

.avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  cursor: pointer;
}

.default-head {
  fill: #99a9bf;
  font-size: 150px;
  cursor: pointer;
}

.el-tabs {
  width: 50%;
  margin: auto;
}

/deep/ .el-radio__input.is-checked .el-radio__inner {
  border-color: #26c2cd;
  background: #26c2cd;
}

.el-cascader,
.el-autocomplete {
  .el-input {
    width: 400px;
  }
}

/deep/ .el-radio__input.is-checked + .el-radio__label {
  color: #26c2cd;
}
</style>

<style scoped lang="scss">
.invoice-list {
  max-height: 552px;
  overflow: auto;
  font-size: 18px;

  .invoice-item {
    margin-top: 30px;
    .handle {
      text-align: right;
      padding-right: 10px;
      .el-button {
        font-size: 15px;
      }
    }

    .title {
      position: relative;
      display: flex;
      justify-content: space-between;
      padding-right: 12px;
      color: var(--mainColor);
      padding: 0 10px 0 5px;
      i{
        position: absolute;
        top: 10px;
        left: 17px;
        font-size: 30px;
      }
      .default {
        font-size: 16px;
        margin-left: 50px;
        text-align: center;
        border: 1px #e6a23c solid;
        border-radius: 25px;
        padding: 4px 10px;
      }
    }

    div {
      margin-top: 15px;
    }
  }
}

.default {
  display: inline-block;
  vertical-align: middle;
  color: var(--mainColor);
  margin-left: 10px;
}

.auth-type {
  display: flex;
  margin-bottom: 22px;
  height: 40px;
  align-items: center;

  span {
    display: block;
    font-size: 14px;
    color: #606266;
    font-weight: 700;
    padding-right: 12px;
    width: 120px;
    text-align: right;
  }
}

.user-head {
  cursor: pointer;
  position: absolute;
  right: 0;
  top: 0;
  width: 150px;
  height: 150px;
  border-radius: 50%;
}

.submit-btn {
  display: block;
  margin: auto;
  width: 200px;
  font-size: 20px;
}

.el-input {
  width: 400px;
}

.profile {
  min-width: 1240px;
  margin: 50px auto;
}
.syx_style {
  display: flex;
  margin-left: 65px;
  span:nth-child(1) {
    width: 160px;
  }
  span:nth-child(2) {
    width: 300px;
  }
}
.invoiceBox{
  margin-right: 10px;
  padding-bottom: 10px;
  border: 1px #dddcdc solid;
  border-radius: 5px;
}
</style>
