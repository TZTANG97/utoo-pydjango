<script>
import {
  cancelConsultApi,
  fetchSubOrderDetailApi,
  downloadOrderFileApi,
} from "@client/api/index";

export default {
  name: "SubDetail",
  data() {
    return {
      id: "",
      detail: null,
      files: [],
      tableData: [],
      subList: [],
      nameList:[]
    };
  },
  mounted() {
    this.id = this.$route.query.id;
    this.getDetail();
  },
  methods: {
    downloadOrderFileApi,
    getDetail() {
      fetchSubOrderDetailApi(this.id).then((res) => {
        if (res.res) {
          let arr = []
          let list = []
          this.detail = res.obj;
          this.files = res.obj.files;
          this.tableData = res.obj.ypList;
          // 处理样品详情数据
          res.obj.ypList.forEach((item, index) => {
            list.push({
              index: index,
              data: item.sampleAttributeManageList,
            });
            item.sampleAttributeManageList.forEach(a=>{
              arr.push(a.sttribute_name)
            })

          });
          this.nameList = Array.from(new Set(arr))
          for (let i = 0; i < list.length; i++) {
            for (let j = 0; j < list[i].data.length; j++) {
              this.subList.push({
                index:list[i].index,
                name:list[i].data[j].sttribute_name,
                data:list[i].data[j].attributeListsanji,
              })
            }
          }
          for (let i = 0; i < this.subList.length; i++) {
            this.subList[i].sttribute_name = ''
              for (let j = 0; j < this.subList[i].data.length; j++) {
                this.subList[i].sttribute_name += this.subList[i].data[j].sttribute_name + '，'
              }
              if (this.subList[i].sttribute_name.endsWith('，')) {
								this.subList[i].sttribute_name = this.subList[i].sttribute_name.slice(0, -1);
							}

              // delete this.subList[i]
          }
          console.log(this.subList, "this.subList");
        } else {
          this.$notify.warning({
            title: "提示",
            message: res.resMsg,
          });
        }
      });
      [
        {}
      ]
    },
    viewDetail() {
      if (this.detail.order_status >= 30) {
        this.$router.push(`/b/order_detail/${this.detail.order_id}`);
      } else {
        this.$notify.warning({
          title: "提示",
          message: !this.detail.order_status ? "订单已取消" : "订单未审核",
        });
      }
    },
    cancelSub() {
      this.$confirm("确认取消预约?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        cancelConsultApi(this.id).then((res) => {
          this.$notify({
            type: res.res ? "success" : "warning",
            title: "提示",
            message: res.resMsg,
          });
          if (res.res) {
            this.getDetail();
          }
        });
      });
    },
  },
};
</script>

<template>
  <div class="container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>预约详情</span>
      </div>
      <el-descriptions v-if="detail">
        <el-descriptions-item label="订单编号" v-if="detail.order_id">
          {{ detail["order_num"] }}
        </el-descriptions-item>
        <el-descriptions-item label="实验分类">
          {{ detail["className"] ? detail["className"] : "暂无" }}
        </el-descriptions-item>
        <el-descriptions-item label="姓名">{{
          detail["userName"] ? detail["userName"] : "暂无"
        }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{
          detail["mobile"] ? detail["mobile"] : "暂无"
        }}</el-descriptions-item>
        <!-- <el-descriptions-item label="公司名称"
          >{{ detail["company_name"] ? detail["company_name"] : "暂无" }}
        </el-descriptions-item> -->
        <el-descriptions-item label="客服人员"
          >{{ detail["syUserName"] ? detail["syUserName"] : "暂无" }}
        </el-descriptions-item>
        <el-descriptions-item label="样品是否回收"
          >{{ detail.reverso_context ? detail.reverso_context : "暂无" }}
        </el-descriptions-item>
        <el-descriptions-item label="样品收件地址"
          >{{ detail["send_address"] ? detail["send_address"] : "暂无" }}
        </el-descriptions-item>
        <el-descriptions-item label="实验需求"
          >{{ detail["content"] ? detail["content"] : "暂无" }}
        </el-descriptions-item>
        <template v-if="detail['reverso_context']">
          <el-descriptions-item label="收件人姓名"
            >{{ detail["addressee_name"] ? detail["addressee_name"] : "暂无" }}
          </el-descriptions-item>
          <el-descriptions-item label="收件人电话">
            {{
              detail["addressee_mobile"] ? detail["addressee_mobile"] : "暂无"
            }}
          </el-descriptions-item>
          <el-descriptions-item label="云视频">
            {{ detail["is_video"] ? "是" : "否" }}
          </el-descriptions-item>
          <el-descriptions-item label="是否线下到场">
            {{ detail["is_arrive"] ? "是" : "否" }}
          </el-descriptions-item>
          <el-descriptions-item label="是否我要上机">
            {{ detail["is_on"] ? "是" : "否" }}
          </el-descriptions-item>
        </template>
        <el-descriptions-item label="订单资料" v-if="files.length">
          <div class="order-data-list">
            <div v-for="(file, idx) in files" :key="idx">
              <a
                :href="`${file.path}/${file.name}`"
                target="_blank"
                :download="`${file.info}.${file.ext}`"
              >
                {{ file.info }}
              </a>
              <span @click="downloadOrderFileApi(file)">下载</span>
            </div>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-table
      :data="tableData"
      border
      style="width: 100%; margin-top: 10px"
      v-if="tableData.length > 0"
    >
      <el-table-column
        prop="sample_num"
        label="样品数量"
        width="180"
        align="center"
      >
      </el-table-column>
      <el-table-column
        prop="sample_name"
        label="样品名称/类型"
        width="180"
        align="center"
      >
      </el-table-column>
      <el-table-column prop="main_component" label="主要成分" align="center">
      </el-table-column>
      <el-table-column v-for="a,b in nameList" :key="b" :label="a" align="center">
        <template slot-scope="scope">
          <span v-for="item,index in subList" :key="index">
            <span v-if="a == item.name && scope.$index == item.index">{{ item.sttribute_name }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column label="是否含磁" align="center">
        <template slot-scope="scope">
          {{ scope.row.is_magnetic == 0 ? "是" : "否" }}
        </template>
      </el-table-column>
      <el-table-column label="是否喷金" align="center">
        <template slot-scope="scope">
          {{scope.row.is_gold_spraying == 0 ? "是" : "否" }}
          <span v-if="scope.row.gold_desc && scope.row.is_gold_spraying == 1">({{scope.row.gold_desc}})</span>
        </template>
      </el-table-column>
    </el-table>

    <el-button
      type="primary"
      @click="cancelSub"
      style="margin-top: 20px"
      v-if="detail && detail.is_cancel"
      >取消预约</el-button
    >

    <template v-if="detail && detail.childs.length">
      <el-table
        :data="detail.childs"
        style="width: 100%; margin-top: 20px"
        border
        stripe
      >
        <el-table-column align="center" label="产品名称" prop="goods_name" />
        <el-table-column align="center" label="产品型号" prop="goods_spec" />
        <el-table-column
          align="center"
          label="产品品牌"
          prop="goods_brand_name"
        />
        <el-table-column align="center" label="数量" prop="goods_nums" />
        <el-table-column
          align="center"
          label="实验项目"
          prop="experiment_project_name"
        />
        <el-table-column
          align="center"
          label="实验分类"
          prop="experiment_class_name"
        />
        <el-table-column align="center" label="实验金额">
          <template #default="{ row }">
            {{ row.goods_price ? row.goods_price.toFixed(2) : "0.00" }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="标准金额">
          <template #default="{ row }">
            {{ row.reference_price ? row.reference_price.toFixed(2) : "0.00" }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="总价">
          <template #default="{ row }">
            {{
              row.goods_nums && row.goods_price
                ? (row.goods_nums * row.goods_price).toFixed(2)
                : "0.00"
            }}
          </template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<style scoped lang="scss">
.order-data-list {
  span {
    color: var(--mainColor);
    cursor: pointer;
  }
  a {
    color: var(--mainColor);
  }
}

.container {
  padding: 20px;
}
</style>
