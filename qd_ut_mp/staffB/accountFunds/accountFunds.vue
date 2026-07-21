<template>
	<view class="container">
		<view class="aBox" v-if="type == 'a'">
			<view>
				<view class="title">
					<text>实验详情(包含实验分包)</text>
					<!-- <u-icon v-if="dateData == ''" @click="dateShowFn(index)" name="calendar"></u-icon> -->
					<text v-if="dateData == ''" @click="dateShowFn(index)">全部</text>
					<text v-if="dateData != ''" @click="dateShowFn(index)">{{dateData}}</text>
				</view>
				<view class="otherInfo">
					<text>实验总额：￥{{ AObj.qnsyzermb }}&emsp;${{ AObj.qnsyzeus }}</text>
					<text>实验回款总收益：￥{{ AObj.rmbSyhkzsy }} &emsp;${{ AObj.usSyhkzsy }}</text>
					<text>实验应收款总额：￥{{ AObj.rmbSyyskze }} &emsp;${{ AObj.usSyyskze }}</text>
					<text>实验分包应付款总额：￥{{ AObj.rmbSyfbyfkze }} &emsp;${{ AObj.usSyfbyfkze }}</text>
				</view>
			</view>
		</view>
		<view class="bBox" v-else-if="type == 'b'">
			<view v-for="(item,index) in typeBList" :key="index">
				<view class="title">
					<text>{{item.title}}</text>
				</view>
				<view v-for="subItem,subIndex in item.data" :key="subIndex" class="otherInfo">
					<text
						v-if="(is_rate != 1 && index == 2 && (subIndex != 2 && subIndex != 3))||(is_rate != 1 && index == 1 && (subIndex != 2 && subIndex != 3))||(is_rate != 1 && index == 0 && (subIndex != 2)) || is_rate == 1">{{subItem.title}}：{{subItem.money}}
						<text style="vertical-align: top;" v-if="index != 0 && subIndex == 3">%</text> </text>
				</view>
			</view>
		</view>
		<view class="cBox" v-else-if="type == 'c'">
			<view class="search-header syxSearch">
				<input type="text" v-model="key_words" placeholder="请输入订单号" maxlength="30">
				<img src="../../static/rmb.png" v-if="rmb" @click="rmbFn" alt="" />
				<img src="../../static/us.png" v-else @click="rmbFn" alt="" />
				<view class="btn" @click="searchFn">
					搜索
				</view>
			</view>
			<!-- <view class="search">
					<u-input style="width: 70%;" v-model="searchData" type="text" border />
					<u-icon class="cicon" @click="rmbFn" v-if="rmb" name="rmb"></u-icon>
					<u-icon class="cicon" @click="rmbFn" v-else name="thumb-up"></u-icon>
				</view>
				<button @click="searchFn">搜索</button> -->
			<view class="screen">
				<view @click="dateShowFn()">{{ dateData }}&nbsp;<u-icon name="arrow-down"></u-icon> </view>
			</view>
			<view class="cBoxItem">
				<view v-for="item,index in typeCList" :key="index">
					<view class="title">
						<text>订单-{{index+1}}</text>
						<text></text>
					</view>
					<view class="otherInfo">
						<text>创建时间：{{$alterTime(item.addTime)}}</text>
						<text>名称：{{logNameFn(item)}}</text>
						<text>金额：{{item.logAmount}}</text>
						<text>可用金额：{{item.afterLogAmount}}</text>
						<text>状态：{{statusFn(item.logStatus)}}</text>
						<!-- <text v-if="item.czNum" style="color: #E96302;">来源订单：{{ item.czNum }}</text> -->
						<navigator v-if="item.czNum && item.accType != 13" style="color: #f39800;padding: 20rpx;margin: 10rpx 0;"
							:url="`/staffB/source_detial/source_detial?id=${item.id}`" hover-class="none">
							来源订单：{{ item.czNum }}
						</navigator>
						<navigator v-if="item.czNum && item.accType == 13" style="color: #f39800;padding: 20rpx;margin: 10rpx 0;"
							:url="`/staff/order_detail/order_detail?id=${item.orderId}`" hover-class="none">
							来源订单：{{ item.czNum }}
						</navigator>
						<text v-if="btnShowFn(item)">操作： <text @click="closeFn(item,index)" style="display: inline-block;color: #f39800;margin-top: -5rpx;">取消申请</text></text>
					</view>
				</view>
			</view>
			<my-loading :loading="isLoading" :isRefresh="is_refresh" :total="typeCList.length"></my-loading>

		</view>
		<view class="defgBox" v-else>
			<view class="group">
				<view class="group-item">
					<view class="group-label">
						<text>{{ type == 'd' ? '充值账户' : type == 'e' ? '提现账户' : type == 'f' ? '转入账户' : type == 'g' ? '借贷款账户' : ''}}：</text>
					</view>
					<view class="group-content">
						<view v-if="rmb" class="text-content" @click="isRmbFn">
							人民币账户 &nbsp; <u-icon name="arrow-right"></u-icon>
						</view>
						<view v-else class="text-content" @click="isRmbFn">
							美元账户 &nbsp; <u-icon name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<text>{{ type == 'd' ? '充值用户' : type == 'e' ? '提现用户' : type == 'f' ? '转账用户' : type == 'g' ? '借贷款用户' : ''}}：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<text @click="userFn">
								{{name}}
							</text>
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'e'">
					<view class="group-label">
						<text>提现银行：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<text v-if="dateData == ''" @click="dateShow = true">请选择提现银行 &nbsp; <u-icon
									name="arrow-right"></u-icon></text>
							<text v-else @click="dateShow = true">{{dateData}}</text>
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'e'">
					<view class="group-label">
						<text>提现卡号：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<input required placeholder='请输入提现卡号' v-model="branKCard" type="number" />
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'e'">
					<view class="group-label">
						<text>提现金额：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<input required placeholder='请输入提现金额' v-model="money" type="number" />
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'f'">
					<view class="group-label">
						<text>转入用户：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<text v-if="dateData == ''" @click="dateShow = true">请选择转入用户 &nbsp; <u-icon
									name="arrow-right"></u-icon></text>
							<text v-else @click="dateShow = true">{{dateData}}</text>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<text>可用余额：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							{{sureUseMoney}}
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'g'">
					<view class="group-label">
						<text>借贷款金额：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<input required placeholder='请输入借贷款金额' v-model="money" type="number" />
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'd'">
					<view class="group-label">
						<text>充值金额：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<input required placeholder='请输入充值金额' v-model.number="money" type="number" />
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'f'">
					<view class="group-label">
						<text>转账金额：</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<input required placeholder='请输入转账金额' v-model="money" type="number" />
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<text>{{ type == 'd' ? '充值备注' : type == 'e' ? '提现备注' : type == 'f' ? '转账备注' : type == 'g' ? '借贷款备注' : ''}}</text>
					</view>
					<view class="group-content">
						<view class="text-content">
							<textarea v-model="msg" placeholder="请输入备注内容" maxlength="120" />
						</view>
					</view>
				</view>
				<view class="group-item" v-if="type == 'f'">
					<view class="group-label">
						<text>转账凭证：</text>
					</view>
					<view class="group-content">
						<view class="text-content" @click="uploadFile(3)">
							<image style="width: 35rpx;height: 35rpx;margin-right: 10rpx;vertical-align: middle;"
								src="@/static/img/upload.png" mode=""></image>
							<text>上传</text>
						</view>
					</view>
				</view>
				<view class="files-list" v-if="files.length">
					<view class="file-item" v-for="(item, index) in files" :key="index">
						<view class="oh" @click="preImage(index, 'files')">{{ item.name }}</view>
						<image src="@/static/delete.png" mode="" @click="deleteFile(index, 'files')"></image>
					</view>
				</view>
				<upload-progress ref="prg"></upload-progress>
			</view>
			<view class="msg">
				<u-icon v-if="type == 'g' || type == 'd' || type == 'f'" name="info-circle"></u-icon>
				<text v-if="type == 'g'"><u-icon name="info-circle"></u-icon>借贷款需向财务确认借贷信息哦！</text>
				<text v-if="type == 'd'"><u-icon name="info-circle"></u-icon>充值需向财务确认转账账户信息哦！</text>
				<text v-if="type == 'f'"><u-icon name="info-circle"></u-icon>转账需向财务确认转账账户信息哦！</text>
			</view>
			<view class="btn">
				<button @click="okFn">确认</button>
			</view>
		</view>
		<u-picker v-if="dateShow" v-model="dateShow" :range="selector" mode="selector" range-key="name"
			@confirm="dateConfirm"></u-picker>
		<u-modal v-model="show" :show-cancel-button='true' @confirm="confirm" ref="uModal" :async-close="true"
			content="是否确定取消申请？"></u-modal>
	</view>
</template>

<script>
	import {
		selExpSumByYearxcx,
		getLog,
	} from '@/api/index.js'
	import {
		accountLogAdd1,
		accountLogAdd2,
		accountTransferAdd,
		accountLoanAdd,
		accountUser,
		accountUserId,
		assetAccountxcx,
		yesterdayIncome,
		assetAccxcx,
		yesterdayIncomexcx,
		selBankList,
		accountDetailxcx,
		passApi
	} from '@/api/staffB.js'
	import MyLoading from "@/components/loading.vue"
	import popupBottom from '../popupBottom'
	import uploadProgress from '../uploadProgress'
	export default {
		components: {
			MyLoading,
			popupBottom,
			uploadProgress
		},
		data() {
			return {
				files: [],
				type: '',
				AObj: {
					qnsyzermb: 0,
					qnsyzeus: 0,
					rmbSyhkzsy: 0,
					usSyhkzsy: 0,
					rmbSyyskze: 0,
					usSyyskze: 0,
					rmbSyfbyfkze: 0,
					usSyfbyfkze: 0,
				},
				dateShow: false,
				selector: [],
				dateData: '', // 不只是时间数据，和其他共用
				typeBList: [{
						title: '账户统计',
						data: [{
								title: '实际可用总资产（人民币)',
								money: 20
							},
							{
								title: '投资冻结总额（人民币)',
								money: 20
							},
							{
								title: '人民币利息可用总额',
								money: 20
							},
							{
								title: '美金利息可用总额',
								money: 20
							},
						]
					},
					{
						title: '人民币账户',
						data: [{
								title: '可用余额',
								money: 20
							},
							{
								title: '冻结余额',
								money: 20
							},
							{
								title: '昨日收益',
								money: 20
							},
							{
								title: '年化利率',
								money: 20
							},
						]
					},
					{
						title: '美元账户',
						data: [{
								title: '可用余额',
								money: 20
							},
							{
								title: '冻结金额',
								money: 20
							},
							{
								title: '昨日收益',
								money: 20
							},
							{
								title: '年化利率',
								money: 20
							},
						]
					},
				],
				accTypeList: [{
						id: '',
						name: '全部'
					},
					{
						id: '13',
						name: '实验回款'
					},

				],
				key_words: '',
				typeCList: [],
				rmb: true,
				accountType: 1,
				sonDetial: {},
				userData: {},
				money: '',
				msg: '',
				branKCard: '',
				bankList: [],
				userList: [],
				selExpSumByYearxcxObj: {},
				page: 1,
				is_refresh: true,
				isLoading: false,
				Cid: '',
				sureUseMoney: 0,
				accountList: [],
				is_rate: 0,
				name: '',
				typeUser: false,
				nowUserId: '',
				orderId:0,
				show:false,
			}
		},
		onLoad(data) {
			const userType = uni.getStorageSync('userInfo')
			this.userData = userType
			this.name = this.userData.wx_nickname
			this.nowUserId = this.userData.userId
			this.type = data.type
			let title = ''
			if (data.type == 'a') {
				title = '订单资金详情'
				this.selExpSumByYearxcxFn(this.dateData)
				let arr = [{
					id: '',
					name: '全部'
				}]
				let year = new Date().getFullYear();
				for (var i = 0; i < 6; i++) {
					arr.push({
						id: i + 1,
						name: year--
					})
				}
				this.selector = arr
			}
			if (data.type == 'b') {
				title = '账户统计'
				this.assetAccountxcxFn()
				this.assetAccxcxFn()
				this.yesterdayIncomexcxFn()
			}
			if (data.type == 'c') {
				title = '明细列表'
				this.selector = this.accTypeList
				this.dateData = '全部'
				// this.getLogFn(1, this.page, 10, this.key_words, this.accountType, this.Cid, '')
			}
			if (data.type == 'd') {
				title = '充值申请'
			}
			if (data.type == 'e') {
				title = '提现申请'
				this.selector = this.bankList
				this.selBankListFn()
			}
			if (data.type == 'f') {
				title = '转账申请'
				this.accountUserFn(1)
			}
			if (data.type == 'g') title = '借贷款申请'
			uni.setNavigationBarTitle({
				title: title
			})
			this.accountUserIdFn(1)
			yesterdayIncome().then(res => {
				console.log(res, 'res')
			})
		},
		onShow() {
			if(this.type == 'c'){
				this.typeCList = []
				this.getLogFn(1, this.page, 10, this.key_words, this.accountType, this.Cid, '')
			}
		},
		onReachBottom() {
			if (this.is_refresh && this.type == 'c') {
				this.page++;
				this.getLogFn(1, this.page, 10, this.key_words, this.accountType, this.Cid, '')
			}
		},
		methods: {
			// 操作按钮展示
			btnShowFn(item) {
				if (item.logStatus == 2) {
					if (item.accType == 1 || item.accType == 2) {
						return true
					} else {
						return false
					}
				} else if (item.logStatus == 3) {
					return true
				} else if (item.logStatus == 4) {
					return true
				} else {
					return false
				}
			},
			// 银行列表
			selBankListFn() {
				selBankList().then(res => {
					res.obj.forEach(item => {
						this.bankList.push({
							id: item.id,
							name: item.bankName
						})
					})
				})
			},
			yesterdayIncomexcxFn() {
				yesterdayIncomexcx().then(res => {
					if (res.res) {
						this.typeBList[1].data[2].money = res.obj.rmbzrsy
						this.typeBList[2].data[2].money = res.obj.uszrsy
					}
				})
			},
			preImage(idx, k) {
				let list = this[k].map(e => e.path + '/' + e.name)
				this.$preFile(idx, list)
			},
			// 删除
			deleteFile(idx, k) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定删除该资料吗？',
					success(e) {
						if (e.confirm) {
							that[k].splice(idx, 1)
						}
					}
				})
			},
			// 账户资金
			assetAccxcxFn() {
				assetAccxcx().then(res => {
					if (res.res) {
						if (res.obj.accounts[0].accountType == 1) {
							this.typeBList[1].data[0].money = res.obj.accounts[0].availableBalance
							this.typeBList[1].data[1].money = res.obj.accounts[0].freezingBalance
							this.typeBList[2].data[0].money = res.obj.accounts[1].availableBalance
							this.typeBList[2].data[1].money = res.obj.accounts[1].freezingBalance
						} else {
							this.typeBList[1].data[0].money = res.obj.accounts[1].availableBalance
							this.typeBList[1].data[1].money = res.obj.accounts[1].freezingBalance
							this.typeBList[2].data[0].money = res.obj.accounts[0].availableBalance
							this.typeBList[2].data[1].money = res.obj.accounts[0].freezingBalance
						}


					}
				})
			},
			// 账户资金
			assetAccountxcxFn() {
				assetAccountxcx().then(res => {
					if (res.res) {
						this.is_rate = res.obj.syUsers.is_rate
						this.typeBList[0].data[0].money = res.obj.totala
						this.typeBList[0].data[1].money = res.obj.totalf
						this.typeBList[0].data[2].money = res.obj.rmbi
						this.typeBList[0].data[3].money = res.obj.usi

						this.typeBList[1].data[3].money = res.obj.setting.rmbRate
						this.typeBList[2].data[3].money = res.obj.setting.usRate

					}
				})
			},
			// 获取可用金额
			accountUserIdFn(num) {
				let obj = {
					userId: this.userData.userId,
					type: num
				}
				accountUserId(obj).then(res => {
					this.sureUseMoney = res
				})
			},
			// 人民币 or 美元
			isRmbFn() {
				this.rmb = !this.rmb
				let num = 1
				if (this.rmb) {
					num = 1
				} else {
					num = 2
				}
				if(this.type == 'e'){
				}else{
					this.accountUserFn(num)
				}
				this.accountUserIdFn(num)
			},
			// 获取用户列表
			accountUserFn(num) {
				let arr = []
				accountUser(num).then(res => {
					res.data.forEach(item => {
						arr.push({
							id: item.userId,
							name: `${item.userName}（${item.trueName}）`
						})
					})

					this.selector = arr
				})
			},
			// 选择器
			dateConfirm(val) {
				if (this.typeUser) {
					this.name = this.selector[val].name
					this.nowUserId = this.selector[val].id
					this.typeUser = false
					console.log(this.nowUserId, '66666')
					console.log()
				} else {
					if (this.type == 'a') {

						if (this.selector[val].name == '全部') {
							this.dateData = ''
						} else {
							this.dateData = this.selector[val].name
						}
						this.selExpSumByYearxcxFn(this.dateData)
					}
					if (this.type == 'b') {
						this.dateData = this.selector[val].name
					}
					if (this.type == 'c') {
						this.dateData = this.selector[val].name
						this.Cid = this.selector[val].id
						this.typeCList = []
						this.getLogFn(1, this.page, 10, this.key_words, this.accountType, this.Cid, '')
					}
					if (this.type == 'd') {
						this.dateData = this.selector[val].name
					}
					if (this.type == 'e') {
						this.dateData = this.selector[val].name
						this.bankName = this.selector[val].id
					}
					if (this.type == 'f') {
						this.dateData = this.selector[val].name
						this.userId = this.selector[val].id
					}
				}

			},
			// 提交资料
			uploadFile(type) {
				// 3 订单资料
				// 4 测试资料
				this.$uploadFile2(this.$refs[type === 3 ? 'prg' : 'prg2'], {
					type
				}).then(res => {
					this.files = []
					// .push(res)
					this.files.push(res)
					// this[type === 3 ? 'files' : 'testFiles'][0] = res
				})
			},
			// 账户统计
			selExpSumByYearxcxFn(data) {
				selExpSumByYearxcx(data).then(res => {
					this.selExpSumByYearxcxObj = res.obj
					console.log(res, 'res')
					if (res.res) {
						this.AObj = res.obj
					}
				})
			},
			dateShowFn(index) {
				this.dateShow = true
			},
			// 订单列表接口
			getLogFn(draw, start, length, order_id, accountType, accType, year) {
				this.isLoading = true
				// let draw = 10,
				// 	start = 1,
				// 	length = 20,
				// 	order_id = '',
				// 	accountType = 1,
				// 	accType = '',
				// 	year = '';
				let str =
					`?draw=${draw}&start=${(this.page - 1) * 10}&length=${length}&order_id=${order_id}&accountType=${accountType}&accType=${accType}&year=${year}`
				getLog(str).then(res => {
					if (res.res) {
						if (res.obj.data.length !== 10) this.is_refresh = false
						this.typeCList = [...this.typeCList, ...res.obj.data]
					} else {
						this.$tip(res.error)
					}
					console.log(res, res)
				}).finally(() => {
					this.isLoading = false
				})
			},
			// 状态
			statusFn(data) {
				if (data == -1) return '已驳回'
				if (data == 0) return '已取消'
				if (data == -2) return '取消申请'
				if (data == 1) return '交易成功'
				if (data == 2) return '待审核'
				if (data == 3) return '待打款'
				if (data == 4) return '待付款'
				if (data == 5) return '待确认'
			},
			// 取消操作
			confirm() {
				passApi(this.orderId).then(res => {
					if(res.res){
						this.$toast('取消成功')
						this.show = false
						setTimeout(()=>{
							this.typeCList = []
							this.getLogFn(1, this.page, 10, this.key_words, this.accountType, this.Cid, '')
						},800)
					}else{
						this.$tip(res.error)
						this.show = false
					}
				})
				// this.show = false
			},
			closeFn(data){
				this.orderId = data.id
				this.show = true
			},
			logNameFn(data) {
				let str = ''
				if (data.accType == 1) {
					str = "充值记录"
				} else if (data.accType == 2) {
					str = "提现记录";
				} else if (data.accType == 3) {
					str = data.log_name;
				} else if (data.accType == 4) {
					if (data.log_name) {
						str = data.log_name;
					} else {
						str = "年化收益";
					}
				} else if (data.accType == 5) {
					if (data.log_name) {
						str = data.log_name;
					} else {
						str = "租赁回款";
					}
				} else if (data.accType == 8) {
					if (data.log_name) {
						str = data.log_name;
					} else {
						str = "销售回款";
					}
				} else if (data.accType == 10) {
					str = "扣款记录";
				} else if (data.accType == 11) {
					str = "转账记录";
				} else if (data.accType == 6) {
					str = data.log_name;
				} else if (data.accType == 7) {
					str = data.log_name;
				} else if (data.accType == 12) {
					if (data.log_name) {
						str = data.log_name;
					} else {
						str = "借贷记录";
					}
				} else if (data.accType == 17) {
					if (data.log_name) {
						str = data.log_name;
					} else {
						str = "借贷利息清算";
					}
				} else if (data.accType == 20) {
					str = "借贷款本金扣款"
				} else if (data.accType == 21) {
					str = "项目资金支出";
				} else {
					str = data.log_name;
				}
				return str;
			},
			// 订单列表搜索
			searchFn() {
				this.list = []
				this.page = 1
				this.is_refresh = true
				this.typeCList = []
				let num = this.dateData == '全部' ? '' : this.dateData == '实验回款' ? 13 : ''
				this.getLogFn(1, this.page, 10, this.key_words, this.accountType, num, '')
			},
			// 人民币/美元
			rmbFn() {
				this.rmb = !this.rmb
				if (this.rmb) {
					this.accountType = 1
				} else {
					this.accountType = 2
				}
			},
			// 确定
			okFn() {
				if (this.type == 'd') {
					var obj = {
						accountType: this.rmb ? 1 : 2,
						trueName: this.dateData,
						userId: this.nowUserId,
						addreddInfo: '',
						logAmount: this.money,
						pdLogInfo: this.msg,
					}
					accountLogAdd1(obj).then(res => {
						if (res.res) {
							this.$toast('充值申请成功')
							setTimeout(() => {
								uni.navigateBack();
							}, 1200)
						} else {
							this.$toast(res.resMsg == null ? '充值申请失败' : res.resMsg)
						}
					})
				} else if (this.type == 'e') {
					if (!this.bankName) return this.$toast('请输入提现银行')
					if (!this.branKCard) return this.$toast('请输入银行卡号')
					var obj = {
						accountType: this.rmb ? 1 : 2,
						userId: this.nowUserId,
						bankName: this.bankName,
						branKCard: this.branKCard,
						addreddInfo: '',
						logAmount: this.money,
						pdLogInfo: this.msg,
					}
					accountLogAdd2(obj).then(res => {
						if (res.res) {
							this.$toast('提现申请成功')
							setTimeout(() => {
								uni.navigateBack();
							}, 1200)
						} else {
							this.$toast(res.resMsg == null ? '提现申请失败' : res.resMsg)
						}
					})
				} else if (this.type == 'f') {
					let ids = this.files.map(item => item['id'] + '')
					if (!this.userId) return this.$toast('请输入转入用户')
					var obj = {
						accountType: this.rmb ? 1 : 2,
						userId: this.nowUserId,
						inTrueName: this.dateData,
						inUserId: this.userId,
						addreddInfo: '',
						logAmount: this.money,
						pdLogInfo: this.msg,
						accessoryId: ids.join(','),
					}
					accountTransferAdd(obj).then(res => {
						if (res.res) {
							this.$toast('转账申请成功')
							setTimeout(() => {
								uni.navigateBack();
							}, 1200)
						} else {
							this.$toast(res.resMsg == null ? '转账申请失败' : res.resMsg)
						}
					})
				} else if (this.type == 'g') {
					var obj = {
						accountType: this.rmb ? 1 : 2,
						userId: this.nowUserId,
						addreddInfo: '',
						logAmount: this.money,
						pdLogInfo: this.msg,
					}
					accountLoanAdd(obj).then(res => {
						if (res.res) {
							this.$toast('借贷款申请成功')
							setTimeout(() => {
								uni.navigateBack();
							}, 1200)
						} else {
							this.$toast(res.resMsg == null ? '借贷款申请失败' : res.resMsg)
						}
					})
				}
				console.log(obj, 'obj')
			},
			// 更换用户
			userFn() {
				if(this.type != 'd') return false
				this.typeUser = true
				let num = 1
				if (this.rmb) {
					num = 1
				} else {
					num = 2
				}
				this.accountUserFn(num)
				this.dateShow = true
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/search.scss';

	.syxSearch {
		position: relative;

		img {
			position: absolute;
			top: 20rpx;
			right: 130rpx;
			width: 40rpx;
			height: 40rpx;
			z-index: 10;
		}
	}

	.aBox,
	.bBox,
	.cBox .cBoxItem {
		width: 100%;
		padding: 20rpx;
		background-color: #f9f9f9;

		&>view {
			margin-bottom: 10rpx;

			.title {
				display: flex;
				justify-content: space-between;
				background-color: #f39800;
				padding: 20rpx;
				color: #fff;
			}

			.otherInfo {
				display: flex;
				flex-direction: column;
				background-color: #fff;

				&>text {
					padding: 20rpx;
					margin: 10rpx 0;
				}
			}
		}
	}

	.bBox {
		.otherInfo {
			display: flex;
			flex-direction: column;
			background-color: #fff;

			&>text {
				padding: 0 20rpx;
				margin: 10rpx 0;
			}
		}
	}

	.cBox {
		width: 100%;
		padding: 20rpx;
		background-color: #f9f9f9;

		&>.title {
			display: flex;
			padding: 20rpx;

			.search {
				position: relative;
				width: 80%;

				.cicon {
					position: absolute;
					top: 31%;
					left: 91%;
					z-index: 20;
					color: #f39800;
				}
			}

			button {
				padding: 3rpx 18rpx;
				color: #fff;
				border-radius: 10rpx;
				font-size: 24rpx;
				background-color: #f39800;
			}
		}

		.noData {
			height: 50rpx;
			border: 1px red solid;
		}
	}

	.defgBox {
		.msg {
			border-top: 1rpx #f2f2f2 solid;
			padding-top: 10rpx;
			color: gray;
			text{
				vertical-align: top;
			}
		}

		.btn {
			margin-top: 40rpx;
			padding: 0 60rpx;

			button {
				color: #fff;
				background-color: #f39800;
				font-size: 30rpx;
				border-radius: 20rpx
			}
		}

	}

	textarea {
		border: 1rpx solid #999;
		border-radius: 7rpx;
		width: 450rpx;
		height: 200rpx;
		box-sizing: border-box;
		padding: 10rpx;
	}

	@import '@/layout/group.scss';

	.text-content {
		input {
			text-align: right;
		}

	}
</style>