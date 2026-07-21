<template>
	<view class="container">
		<!-- 公司列表数据 -->
		<view class="" v-if="userInfo.userType == 1 && userInfo.roleName!='R类人员'">
			<view class="topTitle">
				公司列表
			</view>
			<view style="margin: 10rpx 0 6rpx 0;" @click="topDateFn(1)">
				日期：{{ topDateData }}
			</view>
			<view @click="topType(1)">
				类型：{{ oneDateType }}
			</view>
			<view class="tableBox">
				<view class="tableData" v-for="(item,index) in getArr(companyList)" :key="b" v-show="item.syrmb > 0">
					<view>序号：{{index+1}}</view>
					<view> <text v-if="companyList.length != index+1">公司名称：</text> {{item.company_name}}</view>
					<view v-if="companyList.length != index+1">实验（RMB)：{{item.syrmb}}</view>
					<view v-if="companyList.length == index+1">实验（RMB)总额：{{item.syrmb}}</view>
				</view>
			</view>
			<!-- <text>总额：{{ysallamount}}</text> -->
		</view>
		<!-- 图表数据 -->
		<view class="" v-if="userInfo.userType == 1 && userInfo.roleName!='R类人员'">
			<!--			<view class="topTitleOther">-->
			<!--				<text>最近6个月生产订单数量记录</text>-->
			<!--				<view class="right">-->
			<!--				</view>-->
			<!--			</view>-->
			<!--			<view class="uchartData">-->
			<!--				<qiun-data-charts @getIndex="getIndexy" :canvas2d="true" type="column" :opts="opts"-->
			<!--					:chartData="chartData" />-->
			<!--			</view>-->
			<!--			<view class="topTitleOther">-->
			<!--				<text>生产订单数量 总数量：{{}}</text>-->
			<!--				<view class="right">-->
			<!--				</view>-->
			<!--			</view>-->
			<!--			<view class="uchartData">-->
			<!--				<qiun-data-charts @getIndex="getIndexs" :canvas2d="true" type="pie" :opts="bopts"-->
			<!--					:chartData="expSaleAryrmbObj" />-->
			<!--			</view>-->
			<!--			<view class="topTitleOther">-->
			<!--				<text>设计完成订单距离需求时间剩余天数</text>-->
			<!--				<view class="right">-->
			<!--				</view>-->
			<!--			</view>-->
			<!--			<view class="uchartData">-->
			<!--				<qiun-data-charts @getIndex="getIndexy" :canvas2d="true" type="column" :opts="opts"-->
			<!--					:chartData="chartData" />-->
			<!--			</view>-->
<!--			<view class="topTitleOther">-->
<!--				<text>生产订单状态预览</text>-->
<!--				<view class="right">-->
<!--				</view>-->
<!--			</view>-->
<!--			<view class="uchartData">-->
<!--				<qiun-data-charts @getIndex="getIndexs" :canvas2d="true" type="pie" :opts="bopts"-->
<!--													:chartData="expSaleAryrmbObj" />-->
<!--			</view>-->
			<view class="topTitleOther">
				<text>实验订单金额</text>
				<view class="right">
					<text @click="topDateFn(2)">{{otherDate}}</text>
					<text @click="resetFn(1)">重置</text>
					<text @click="topType(2)">{{allData}}</text>
				</view>
			</view>
			<view class="uchartData">
				<qiun-data-charts @getIndex="getIndexy" :canvas2d="true" type="column" :opts="opts"
													:chartData="chartData" />
			</view>
			<text>{{otherDate == '选择年份' ? '全年' : otherDate+'年'}}销售总额：人民币 {{expqnxsrmb}}</text>
			<view class="topTitleOther">
				<text>实验分包订单金额</text>
				<view class="right">
					<text @click="topDateFn(3)">{{otherDatefb}}</text>
					<text @click="resetFn(2)">重置</text>
					<text @click="topType(3)">{{allDatafb}}</text>
				</view>
			</view>
			<view class="uchartData">
				<qiun-data-charts @getIndex="getIndexe" :canvas2d="true" type="column" :opts="opts"
													:chartData="chartDatafb" />
			</view>
			<text>{{otherDatefb == '选择年份' ? '全年' : otherDatefb+'年'}}销售总额（包含未审核订单)：人民币 {{expqnxsrmbfb}}</text>
			<view class="topTitleOther">
				<text>实验已收/应收</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexs" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expSaleAryrmbObj" />
			</view>
			<view class="num">
				已收
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexsi" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expoverdueAryrmballObj" />
			</view>
			<view class="num">
				应收
			</view>
			<text>总额：{{syysysallamount}}，已收总额：{{ysallamount}}，应收总额：{{overdueallamount}}</text>
			<view class="topTitleOther">
				<text>实验分包已收/应收</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexw" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expysAryrmballfbObj" />
			</view>
			<view class="num">
				已收
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexl" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expoverdueAryrmballfbObj" />
			</view>
			<view class="num">
				应收
			</view>
			<text>总额：{{expsuballamount}}，已收总额：{{ysallamountfb}}，应收总额：{{overdueallamountfb}}</text>
		</view>

		<view class="" v-if="userInfo.userType != 1  || userInfo.userType == 2 && userInfo.roleName == 'R类人员'">
			<view class="topTitleOther">
				<text>个人实验总额{{otherDate == '选择年份' ? 'ALL' : otherDate}}年</text>
				<view class="right">
					<text @click="topDateFn(2)">{{otherDate}}</text>
					<text @click="resetFn(1)">重置</text>
				</view>
			</view>
			<view class="uchartData">
				<qiun-data-charts @getIndex="getIndexshi" :ontouch="true" :canvas2d="true" type="column" :opts="opts2"
													:chartData="chartData" />
			</view>
			<text>{{otherDate == '选择年份' ? '全年' : otherDate+'年'}}实验总额：人民币 {{qnxsrmbExp}} | 美元 {{qnxsusExp}} |
				实验的订单数量：人民币订单总数：{{ddslrmbExp}}, 美元订单总数：{{ddslusExp}}</text>

			<view class="topTitleOther">
				<text>个人实验分包总额{{otherDatefb == '选择年份' ? 'ALL' : otherDatefb}}年</text>
				<view class="right">
					<text @click="topDateFn(3)">{{otherDatefb}}</text>
					<text @click="resetFn(2)">重置</text>
				</view>
			</view>
			<view class="uchartData">
				<qiun-data-charts @getIndex="getIndexsy" :ontouch="true" :canvas2d="true" type="column" :opts="opts2"
													:chartData="chartDatafb" />
			</view>
			<text>{{otherDatefb == '选择年份' ? '全年' : otherDatefb+'年'}}实验分包总额：人民币 {{qnxsrmbExpSub}} | 美元 {{qnxsusExpSub}} |
				实验的订单数量：人民币订单总数：{{ddslrmbExpsub}}, 美元订单总数：{{ddslusExpSub}}</text>

			<view class="topTitleOther">
				<text>个人实验应付款</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData">
				<!-- <qiun-data-charts :canvas2d="true" type="pie" :opts="bopts" :chartData="pie1" /> -->
			</view>
			<text>应付总额：美元：0，人民币：0</text>
			<view class="topTitleOther">
				<text>个人实验应收款</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData" v-if="overdueAryussy.length != 0">
				<qiun-data-charts @getIndex="getIndexq" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryussyObj" />
			</view>
			<view class="num" v-if="overdueAryussy.length != 0">
				美元
			</view>
			<view class="uchartData" v-if="overdueAryrmbsy.length != 0">
				<qiun-data-charts @getIndex="getIndexq" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryrmbsyObj" />
			</view>
			<view class="num" v-if="overdueAryrmbsy.length != 0">
				人民币
			</view>
			<text>应收总额：美元：{{overdueussy}}，人民币：{{overduermbsy}}</text>
			<view class="topTitleOther">
				<text>个人实验分包应付款</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData" v-if="overdueAryusPaysyfb.length != 0">
				<qiun-data-charts @getIndex="getIndexb" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryusPaysyfbObj" />
			</view>
			<view class="num" v-if="overdueAryusPaysyfb.length != 0">
				美元
			</view>
			<view class="uchartData" v-if="overdueAryrmbPaysyfb.length != 0">
				<qiun-data-charts @getIndex="getIndexb" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryrmbPaysyfbObj" />
			</view>
			<view class="num" v-if="overdueAryrmbPaysyfb.length != 0">
				人民币
			</view>
			<text>应付总额：美元：{{overdueusPaysyfb}}，人民币：{{overduermbPaysyfb}}</text>
			<view class="topTitleOther">
				<text>个人实验分包应收款</text>
				<view class="right">
				</view>
			</view>
			<!-- @click="goto(9)" -->
			<view class="uchartData" v-if="overdueAryrmbsyfb.length != 0">
				<qiun-data-charts @getIndex="getIndexj" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryrmbsyfbObj" />
			</view>
			<view class="num" v-if="overdueAryrmbsyfb.length != 0">
				人民币
			</view>
			<view class="uchartData" v-if="overdueAryussyfb.length != 0">
				<qiun-data-charts @getIndex="getIndexj" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="overdueAryussyfbObj" />
			</view>
			<view class="num" v-if="overdueAryussyfb.length != 0">
				美元
			</view>
			<text>应收总额：美元：{{overdueussyfb}}，人民币：{{overduermbsyfb}}</text>
		</view>
		<view class="" v-if="userInfo.userType != 1 && deptType == 2 && userInfo.roleName!='R类人员'">
			<view class="topTitleOther">
				<text>实验已收/应收</text>
				<view class="right">
				</view>
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexs" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expSaleAryrmbObj" />
			</view>
			<view class="num">
				已收
			</view>
			<view class="uchartData" style="height: 700rpx">
				<qiun-data-charts @getIndex="getIndexsi" :canvas2d="true" type="pie" :opts="bopts"
													:chartData="expoverdueAryrmballObj" />
			</view>
			<view class="num">
				应收
			</view>
			<text>总额：{{syysysallamount}}，已收总额：{{ysallamount}}，应收总额：{{overdueallamount}}</text>
		</view>

		<u-picker v-if="dateShow" v-model="dateShow" mode="time" @confirm="dateConfirm" :params="params"></u-picker>
		<u-select v-if="moneyShow" v-model="moneyShow" @confirm="moneyConfirm" :list="list"></u-select>
	</view>
</template>

<script>
import {
	digitalManageCenterxcx,
	queryAll,
	selExpSaleByYear,
	selCompanySaleByYear,
	selUserAmountByYearsygrxcx,
	selUserAmountByYearsyfbgrxcx,
	digitalManageCenter
} from '@/api/staffB.js'
export default {
	data() {
		return {
			dateShow: false,
			moneyShow: false,
			params: {
				year: true,
				month: false,
				day: false,
				hour: false,
				minute: false,
				second: false
			},
			topDateData: '选择年份',
			oneDateType: '全部',
			list: [{
				value: '1',
				label: '全部'
			},
				{
					value: '2',
					label: '订单未发起审核'
				},
			],
			chartData: {},
			chartDatafb: {},
			opts2: {
				padding: [15, 15, 0, 5],
				enableScroll: true,
				legend: {
					show: true,
				},
				xAxis: {
					disableGrid: true,
					itemCount: 4,
					scrollShow: true,
				},
				yAxis: {
					data: [{
						min: 0
					}]
				},
				extra: {
					column: {
						type: "group",
						width: 30,
						activeBgColor: "#000000",
						activeBgOpacity: 0.08
					}
				}
			},
			opts: {
				padding: [15, 15, 0, 5],
				enableScroll: false,
				legend: {
					show: false,
				},
				xAxis: {
					disableGrid: true
				},
				yAxis: {
					data: [{
						min: 0
					}]
				},
				extra: {
					column: {
						type: "group",
						width: 30,
						activeBgColor: "#000000",
						activeBgOpacity: 0.08
					}
				}
			},
			bopts: {
				// color: ["#1890FF", "#91CB74", "#FAC858", "#EE6666", "#73C0DE", "#3CA272", "#FC8452", "#9A60B4",
				// 	"#ea7ccc"
				// ],
				padding: [80, 40, 60, 40],
				legend: {
					show: false
				},
				fontSize:12,
				enableScroll: false,
				extra: {
					pie: {
						activeOpacity: 0.5,
						activeRadius: 10,
						offsetAngle: 0,
						labelWidth: 15,
						border: false,
						borderWidth: 3,
						borderColor: "#FFFFFF"
					}
				}
			},
			otherDate: '选择年份',
			otherDatefb: '选择年份',
			allData: '全部',
			allDatafb: '全部',
			num: '',
			type: '',
			companyList: [],
			ysallamount: 0,
			expqnxsrmb: 0,
			expqnxsrmbfb: 0,
			syysysallamount: 0,
			overdueallamount: 0,
			expsuballamount: 0,
			ysallamountfb: 0,
			overdueallamountfb: 0,
			expSaleAryrmbObj: {},
			expoverdueAryrmballObj: {},
			expysAryrmballfbObj: {},
			expoverdueAryrmballfbObj: {},
			selectList: [],
			userInfo: {
				// userType: 2
			},
			pie1: {},
			qnxsrmbExp: 0,
			qnxsusExp: 0,
			ddslrmbExp: 0,
			ddslusExp: 0,
			qnxsrmbExpSub: 0,
			qnxsusExpSub: 0,
			ddslrmbExpsub: 0,
			ddslusExpSub: 0,
			overdueussy: 0,
			overduermbsy: 0,
			overdueusPaysyfb: 0,
			overduermbPaysyfb: 0,
			overdueussyfb: 0,
			overduermbsyfb: 0,
			overdueAryussyObj: {},
			overdueAryussy: [],
			overdueAryrmbsyObj: {},
			overdueAryrmbsy: [],
			overdueAryusPaysyfbObj: {},
			overdueAryusPaysyfb: [],
			overdueAryrmbPaysyfbObj: {},
			overdueAryrmbPaysyfb: [],
			overdueAryussyfbObj: {},
			overdueAryussyfb: [],
			overdueAryrmbsyfbObj: {},
			overdueAryrmbsyfb: [],
			deptType: 0,
			id: '',
			name: '',
			date: '',
			allId: '',
			allId1: '',
		}
	},
	mounted() {
		this.userInfo = uni.getStorageSync('userInfo');
		console.log(this.userInfo, 'userInfo')
		// 初始化数据
		this.digitalManageCenterxcxFn()
		if (this.userInfo.userType == 1) {
			// 实验选择下拉框数据
			queryAll(2).then(res => {
				if (res.res) {
					let arr = [{
						value: '',
						label: '全部'
					}]
					res.obj.forEach(item => {
						arr.push({
							value: item.id,
							label: item.name
						})
					})
					this.selectList = arr
				}
			})
			// 实验订单数据初始化
			this.selExpSaleByYearFn(this.otherDate, this.allData, 6)
			this.selExpSaleByYearFn(this.otherDatefb, this.allDatafb, 8)
			this.selCompanySaleByYearFn(this.topDateData, this.oneDateType)
			// 新图表数据
			this.digitalManageCenterFn()
		}
	},
	methods: {
		getArr(arr) {
			let data = [];
			arr.forEach(item => {
				if(item.syrmb > 0) {
					data.push(item)
				}
			})
			return data
		},
		digitalManageCenterFn(){
			digitalManageCenter().then(res=>{
				console.log(res,'ressss')
			})
		},
		getIndexj(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(9)
		},
		getIndexq(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(7)
		},
		getIndexb(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(8)
		},
		getIndexy(data) {
			if (data.currentIndex.index == -1) return
			this.date = data.opts.categories[data.currentIndex.index]
			this.id = null
			this.name = null
			this.goto(1)
		},
		getIndexe(data) {
			if (data.currentIndex.index == -1) return
			this.date = data.opts.categories[data.currentIndex.index]
			this.id = null
			this.name = null
			this.goto(2)
		},
		getIndexs(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(3)
		},
		getIndexsi(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(4)
		},
		getIndexw(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(5)
		},
		getIndexl(data) {
			if (data.currentIndex == -1) return
			this.id = data.opts._series_[data.currentIndex].id
			this.name = data.opts._series_[data.currentIndex].name
			this.date = null
			this.goto(6)
		},
		getIndexshi(data) {
			if (data.currentIndex.index == -1) return
			this.date = data.opts.categories[data.currentIndex.index]
			this.id = null
			this.name = null
			this.goto(10)
		},
		getIndexsy(data) {
			if (data.currentIndex.index == -1) return
			this.date = data.opts.categories[data.currentIndex.index]
			this.id = null
			this.name = null
			this.goto(11)
		},
		// 图表数据
		selUserAmountByYearsygrxcxFn(data) {
			selUserAmountByYearsygrxcx(data).then(res => {
				if (res.res) {
					this.ddslrmbExp = res.obj.ddslrmbExp
					this.ddslusExp = res.obj.ddslusExp
					this.qnxsrmbExp = res.obj.qnxsrmbExp
					this.qnxsusExp = res.obj.qnxsusExp
					let data = {
						categories: res.obj.xmonths,
						series: [{
							name: '实验人民币',
							data: res.obj.userSaleAryrmbExp
						},
							{
								name: '实验美金',
								data: res.obj.userSaleAryusExp
							}
						]
					};
					this.chartData = JSON.parse(JSON.stringify(data));
				}
				console.log(res, '666666')
			})
		},
		selUserAmountByYearsyfbgrxcxFn(data) {
			selUserAmountByYearsyfbgrxcx(data).then(res => {
				if (res.res) {
					this.ddslrmbExpSub = res.obj.ddslrmbExpSub
					this.ddslusExpSub = res.obj.ddslusExpSub
					this.qnxsrmbExpSub = res.obj.qnxsrmbExpSub
					this.qnxsusExpSub = res.obj.qnxsusExpSub
					let data1 = {
						categories: res.obj.xmonths,
						series: [{
							name: '实验人民币',
							data: res.obj.userSaleAryrmbExpSub
						},
							{
								name: '实验美金',
								data: res.obj.userSaleAryusExpSub
							}
						]
					};
					this.chartDatafb = JSON.parse(JSON.stringify(data1));
				}
			})
		},
		// 初始化数据
		digitalManageCenterxcxFn() {
			digitalManageCenterxcx().then(res => {
				if (!res.res) return
				if (this.userInfo.userType != 1) {
					this.qnxsrmbExp = res.obj.qnxsrmbExp
					this.qnxsusExp = res.obj.qnxsusExp
					this.ddslrmbExp = res.obj.ddslrmbExp
					this.ddslusExp = res.obj.ddslusExp
					this.qnxsrmbExpSub = res.obj.qnxsrmbExpSub
					this.qnxsusExpSub = res.obj.qnxsusExpSub
					this.ddslrmbExpsub = res.obj.ddslrmbExpSub
					this.ddslusExpSub = res.obj.ddslusExpSub
					this.overdueussy = res.obj.overdueussy
					this.overduermbsy = res.obj.overduermbsy
					this.overdueusPaysyfb = res.obj.overdueusPaysyfb
					this.overduermbPaysyfb = res.obj.overduermbPaysyfb
					this.overdueussyfb = res.obj.overdueussyfb
					this.overduermbsyfb = res.obj.overduermbsyfb
					// 柱状图1
					let data = {
						categories: res.obj.xmonths,
						series: [{
							name: '实验人民币',
							data: res.obj.userSaleAryrmbExp
						},
							{
								name: '实验美金',
								data: res.obj.userSaleAryusExp
							}
						]
					};
					this.chartData = JSON.parse(JSON.stringify(data));

					// 柱状图2
					let data1 = {
						categories: res.obj.xmonths,
						series: [{
							name: '实验分包人民币',
							data: res.obj.userSaleAryrmbExpSub
						}, {
							name: '实验分包美金',
							data: res.obj.userSaleAryusExpSub
						}]
					};
					this.chartDatafb = JSON.parse(JSON.stringify(data1));


					// 个人实验应收款人民币
					let overdueAryrmbsy = []

					res.obj.overdueAryrmbsy.forEach(item => {
						overdueAryrmbsy.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryrmbsy = overdueAryrmbsy
					console.log(this.overdueAryrmbsy, 'this.overdueAryrmbsy')
					this.overdueAryrmbsyObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryrmbsy
						}]
					}));
					// 个人实验应收款美元
					let overdueAryussyObj = []

					res.obj.overdueAryussy.forEach(item => {
						overdueAryussyObj.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryussy = overdueAryussyObj
					console.log(this.overdueAryussy, 'this.overdueAryussy')
					this.overdueAryussyObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryussyObj
						}]
					}));
					// 个人实验分包应付款美元
					let overdueAryusPaysyfb = []
					res.obj.overdueAryusPaysyfb.forEach(item => {
						overdueAryusPaysyfb.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryusPaysyfb = overdueAryusPaysyfb
					this.overdueAryusPaysyfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryusPaysyfb
						}]
					}));
					// 个人实验分包应付款人民币
					let overdueAryrmbPaysyfbObj = []
					res.obj.overdueAryrmbPaysyfb.forEach(item => {
						overdueAryrmbPaysyfbObj.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryrmbPaysyfb = overdueAryrmbPaysyfbObj
					this.overdueAryrmbPaysyfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryrmbPaysyfbObj
						}]
					}));

					// 个人实验分包应收款人民币
					let overdueAryrmbsyfb = []
					res.obj.overdueAryrmbsyfb.forEach(item => {
						overdueAryrmbsyfb.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryrmbsyfb = overdueAryrmbsyfb
					this.overdueAryrmbsyfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryrmbsyfb
						}]
					}));
					// 个人实验分包应收款美元
					let overdueAryussyfb = []
					res.obj.overdueAryussyfb.forEach(item => {
						overdueAryussyfb.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: false,
						})
					})
					this.overdueAryussyfb = overdueAryussyfb
					this.overdueAryussyfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: overdueAryussyfb
						}]
					}));

					// if (this.deptType == 2) {
					// 实验分包已收

					// }
				}

				if (this.userInfo.userType == 1) {
					this.companyList = res.obj.companyInfo
					this.ysallamount = res.obj.ysallamount
					this.expqnxsrmb = res.obj.expqnxsrmb
					this.expqnxsrmbfb = res.obj.expqnxsrmbfb
					this.syysysallamount = res.obj.syysysallamount
					this.overdueallamount = res.obj.overdueallamount
					this.expsuballamount = res.obj.expsuballamount
					this.ysallamountfb = res.obj.ysallamountfb
					this.overdueallamountfb = res.obj.overdueallamountfb
					if (res.obj.deptType) this.deptType = res.obj.deptType
					// 实验已收
					let expysAryrmball = []
					res.obj.expysAryrmball.forEach(item => {
						let name = item.company_name.slice(0, 6)
						expysAryrmball.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: true,
							labelText: name
						})
					})
					this.expSaleAryrmbObj = JSON.parse(JSON.stringify({
						series: [{
							data: expysAryrmball
						}]
					}));
					// 实验应收
					let expoverdueAryrmball = []
					res.obj.expoverdueAryrmball.forEach(item => {
						let name = item.company_name.slice(0, 6)
						expoverdueAryrmball.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: true,
							labelText: name
						})
					})
					this.expoverdueAryrmballObj = JSON.parse(JSON.stringify({
						series: [{
							data: expoverdueAryrmball
						}]
					}));
					let expysAryrmballfb = []
					res.obj.expysAryrmballfb.forEach(item => {
						let name = item.company_name.slice(0, 6)
						expysAryrmballfb.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: true,
							labelText: name
						})
					})
					this.expysAryrmballfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: expysAryrmballfb
						}]
					}));
					// 实验分包应收
					let expoverdueAryrmballfb = []
					res.obj.expoverdueAryrmballfb.forEach(item => {
						let name = item.company_name.slice(0, 6)
						expoverdueAryrmballfb.push({
							name: item.company_name,
							value: Math.max(item.total, 0),
							id: item.company_id,
							labelShow: true,
							labelText: name
						})
					})
					this.expoverdueAryrmballfbObj = JSON.parse(JSON.stringify({
						series: [{
							data: expoverdueAryrmballfb
						}]
					}));
				}

			})
		},
		// 跳转
		goto(num) {
			if (num == 1) {
				uni.navigateTo({
					url: '/staffB/experimentEdOrAble/experimentEdOrAble?type=' + num + '&name=' + this.name +
							'&id=' + this.id + '&date=' + this.date + '&test_type=' + this.allId
				});
			} else if (num == 2) {
				uni.navigateTo({
					url: '/staffB/experimentEdOrAble/experimentEdOrAble?type=' + num + '&name=' + this.name +
							'&id=' + this.id + '&date=' + this.date + '&test_type=' + this.allId1
				});
			} else {
				uni.navigateTo({
					url: '/staffB/experimentEdOrAble/experimentEdOrAble?type=' + num + '&name=' + this.name +
							'&id=' + this.id + '&date=' + this.date
				});
			}

			// if (num == 1) {
			// 	uni.navigateTo({
			// 		url: '/staff/order_list/order_list?type=syx666&all=null&date='+this.date
			// 	});
			// } else if (num == 2) {
			// 	uni.navigateTo({
			// 		url: '/staff/order_list/order_list?type=syx888&all=null&date='+this.date
			// 	});
			// } else {
			// 	uni.navigateTo({
			// 		url: '/staffB/experimentEdOrAble/experimentEdOrAble?type=' + num + '&name=' + this.name + '&id=' + this.id
			// 	});
			// }
			// if (num == 3) {
			// 	uni.navigateTo({
			// 		url: '/staff/order_list/order_list?type=6&all=1'
			// 	});
			// }
			// if (num == 4) {
			// 	uni.navigateTo({
			// 		url: '/staff/order_list/order_list?type=8&all=1'
			// 	});
			// }
		},
		// 公司列表数据
		selCompanySaleByYearFn(year, type) {
			let obj = {
				year: year == '选择年份' ? '' : year,
				type: type == '全部' ? '1' : '2',
			}
			selCompanySaleByYear(obj).then(res => {
				if (!res.res) return
				let arr = []
				res.obj.companyInfo.forEach(item => {
					arr.push({
						company_name: item.company_name,
						syrmb: item.syrmb,
						id: item.id
					})
				})
				this.companyList = arr
			})
		},
		// 实验柱状图 图表数据
		selExpSaleByYearFn(year, test_type, order_type) {
			let idData = ''
			if (test_type != '全部') {
				idData = this.selectList.find(e => e.label == test_type).value
			}
			let obj = {
				year: year == '选择年份' ? '' : year,
				test_type: idData,
				order_type: order_type
			}
			selExpSaleByYear(obj).then((res) => {
				if (!res.res) return
				let data = {
					categories: res.obj.expmonth,
					series: [{
						name: '',
						data: res.obj.expSaleAryrmb
					}]
				};

				if (order_type == 6) {
					this.chartData = JSON.parse(JSON.stringify(data));
					this.expqnxsrmb = res.obj.expqnxsrmb
				}
				if (order_type == 8) {
					this.chartDatafb = JSON.parse(JSON.stringify(data));
					this.expqnxsrmbfb = res.obj.expqnxsrmb
				}
			})
		},
		// 时间确定
		dateConfirm(val) {
			if (this.userInfo.userType != 1) {
				if (this.num == 2) {
					this.otherDate = val.year
					this.selUserAmountByYearsygrxcxFn(this.otherDate)
				} else {
					this.otherDatefb = val.year
					this.selUserAmountByYearsyfbgrxcxFn(this.otherDatefb)
				}
			} else {
				if (this.num == 1) {
					this.topDateData = val.year
					this.selCompanySaleByYearFn(this.topDateData, this.oneDateType)
				} else if (this.num == 2) {
					this.otherDate = val.year
					this.selExpSaleByYearFn(this.otherDate, this.allData, 6)
				} else {
					this.otherDatefb = val.year
					this.selExpSaleByYearFn(this.otherDatefb, this.allDatafb, 8)
				}
			}

		},
		// 非时间确定
		moneyConfirm(val) {
			console.log(val, 'val')
			if (this.type == 1) {
				this.oneDateType = val[0].label
				this.allId = ''
				this.allId1 = ''
				this.selCompanySaleByYearFn(this.topDateData, this.oneDateType)
			} else if (this.type == 2) {
				this.allData = val[0].label
				this.allId = val[0].value
				console.log(this.allId, 'this.allId')
				this.selExpSaleByYearFn(this.otherDate, this.allData, 6)
			} else {
				this.allDatafb = val[0].label
				this.allId1 = val[0].value
				console.log(this.allId1, 'this.allId1')
				this.selExpSaleByYearFn(this.otherDatefb, this.allDatafb, 8)
			}
			// const list = JSON.parse(JSON.stringify(this.selectList))
			// this.selectList = []
			// this.selectList = list

		},
		// 弹出时间选择
		topDateFn(num) {
			this.num = num
			this.dateShow = true
		},
		// 弹出非时间选择
		topType(type) {
			if (type == 1) {
				this.list = [{
					value: '1',
					label: '全部'
				},
					{
						value: '2',
						label: '订单未发起审核'
					},
				]
			} else {
				this.list = this.selectList
			}
			this.type = type
			this.moneyShow = true
		},
		// 重置
		resetFn(num) {
			if (this.userInfo.userType != 1) {
				if (num == 1) {
					this.otherDate = '选择年份'
					this.selUserAmountByYearsygrxcxFn('')
				}
				if (num == 2) {
					this.otherDatefb = '选择年份'
					this.selUserAmountByYearsyfbgrxcxFn('')
				}
			} else {
				if (num == 1) {
					this.otherDate = '选择年份'
					this.allData = '全部'
					this.selExpSaleByYearFn(this.otherDate, this.allData, 6)
					this.allId = ''
				}
				if (num == 2) {
					this.otherDatefb = '选择年份'
					this.allDatafb = '全部'
					this.selExpSaleByYearFn(this.otherDatefb, this.allDatafb, 8)
					this.allId1 = ''
				}
			}

		}
	}
}
</script>
<style>
/* 	.u-drawer {
  z-index: 9999998 !important;
}

.u-mask {
  z-index: 9999997 !important;
}

.u-drawer-content {
  z-index: 9999999 !important;
} */
</style>

<style lang="scss" scoped>
.container {
	padding: 20rpx;
}

.topTitle {
	border-left: 10rpx solid #888888;
	padding-left: 10rpx;
	font-size: 32rpx;
	font-weight: 700;
	margin: 20rpx 0 10rpx 0;
}

.topTitleOther {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin: 30rpx 0 10rpx 0;

	&>text {
		border-left: 10rpx solid #888888;
		padding-left: 10rpx;
		font-size: 32rpx;
		font-weight: 700;
	}

	.right {
		display: flex;
		justify-content: space-around;
		color: gray;

		text {
			margin-left: 10rpx;
		}
	}
}

.tableBox {
	padding: 20rpx 20rpx 0 20rpx;

	.tableData {
		width: 100%;
		margin-bottom: 30rpx;
		box-shadow: 7rpx 7rpx 4rpx #efefef;
		padding: 15rpx;

		&>view {
			margin: 8rpx 0;
		}
	}
}

.uchartData {
	width: 100%;
	height: 500rpx;
	margin: 20rpx 0;
	// position: relative;
	// z-index: 1;
	// canvas{
	// 	position: relative;
	// 	z-index: 1 !important;
	// }
}

.num {
	width: 100%;
	text-align: center;
	color: gray;
	margin: 0 0 20rpx 0;
}
</style>
