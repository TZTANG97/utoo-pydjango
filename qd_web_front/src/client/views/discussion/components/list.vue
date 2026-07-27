<template>
  <div
    class="discussion-feed"
    :class="{ 'discussion-feed--scroll': areaScroll }"
    ref="scrollArea"
    @scroll="handleScrollArea"
  >
    <div v-if="!isLoading && items.length === 0" class="feed-empty">
      <el-empty description="暂无讨论内容" />
    </div>

    <div class="feed-list">
      <article
        v-for="(item, index) in items"
        :key="'entry-' + item.id"
        class="post-card"
      >
        <header class="post-card__head">
          <img
            class="post-card__avatar"
            :src="authorAvatar(item)"
            :alt="displayAuthor(item)"
          />
          <div class="post-card__meta">
            <div class="post-card__author-row">
              <span class="post-card__author">{{ displayAuthor(item) }}</span>
              <span v-if="listType === 3 && item.isAudit != 1" class="post-card__badge">待审核</span>
            </div>
            <div class="post-card__time-row">
              <time
                class="post-card__time"
                :title="fullTime(item.addTime)"
              >发布于 {{ relativeTime(item.addTime) }}</time>
              <span v-if="listType === 1 && item.likeTime" class="post-card__time-extra">
                · 点赞于 {{ relativeTime(item.likeTime) }}
              </span>
              <span v-else-if="listType === 2 && item.collectTime" class="post-card__time-extra">
                · 收藏于 {{ relativeTime(item.collectTime) }}
              </span>
            </div>
          </div>
        </header>

        <h2 class="post-card__title" @click="toDetail(item.id)">{{ item.title || '无标题' }}</h2>

        <div class="post-card__body">
          <text-truncation
            :ref="'truncation' + index"
            :content="item.content"
            :accessory="item.accessoryList"
            :index="index"
            @openText="openText"
          />
        </div>

        <footer class="post-card__footer">
          <div class="post-card__actions">
            <button
              type="button"
              class="action-chip"
              :class="{ 'action-chip--active': item.comments }"
              @click="menuType(item, 1)"
            >
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ item.comments ? '收起评论' : commentBtnLabel(item) }}</span>
            </button>
            <button
              type="button"
              class="action-chip"
              :class="{ 'action-chip--active': item.isLike == 1 }"
              @click="menuType(item, 2, index)"
            >
              <el-icon><Pointer /></el-icon>
              <span>{{ item.isLike == 1 ? '已喜欢' : '喜欢' }}</span>
            </button>
            <button
              type="button"
              class="action-chip"
              :class="{ 'action-chip--active': item.isCollect == 1 }"
              @click="menuType(item, 3, index)"
            >
              <el-icon><Star /></el-icon>
              <span>{{ item.isCollect == 1 ? '已收藏' : '收藏' }}</span>
            </button>
            <button
              v-if="listType == 3"
              type="button"
              class="action-chip action-chip--danger"
              @click="menuType(item, 4, index)"
            >
              <el-icon><Delete /></el-icon>
              <span>删除</span>
            </button>
          </div>
          <button
            v-if="item.isExpanded"
            type="button"
            class="post-card__collapse"
            @click="putAway(index)"
          >
            收起正文
          </button>
        </footer>

        <section v-if="item.comments" class="post-card__comments">
          <div v-if="item._commentsLoading" class="comments-loading">
            <div class="feed-spinner" />
            <span>评论加载中...</span>
          </div>
          <comment-section
            v-else
            :key="'comments-' + item.id + '-' + (item.commentList?.length || 0)"
            :listType="listType"
            :row="item"
            :commentList="item.commentList || []"
          />
        </section>
      </article>
    </div>

    <div v-if="isLoading && hasMore" class="feed-status">
      <div class="feed-spinner" />
      <span>加载中...</span>
    </div>

    <div v-if="!hasMore && !isLoading && items.length > 0" class="feed-end">
      已经到底啦
    </div>
  </div>
</template>

<script>
import textTruncation from "@client/views/discussion/components/textTruncation.vue";
import { mapGetters } from "vuex";
import CommentSection from "@client/views/discussion/comments/CommentSection.vue";
import {
  commenttreebulder,
  deleteentry,
  entryComments,
  entryMenu,
  likeList,
  publishList,
} from "@client/api/discussion";
import { buildOssImageUrl, defaultAvatarUrl } from "@client/utils/oss-image";
import { formatFullTime, formatRelativeTime } from "@client/utils/format-time";
import { ChatDotRound, Delete, Pointer, Star } from "@element-plus/icons-vue";
import "quill/dist/quill.core.css";
import "quill/dist/quill.snow.css";
import "quill/dist/quill.bubble.css";

export default {
  props: {
    areaScroll: {
      type: Boolean,
      default: false
    },
    detailShow: {
      type: Boolean,
      default: false,
    },
    listType: {
      type: Number,
      default: 0
    },
    sortBy: {
      type: String,
      default: 'addTime_desc',
    },
  },
  components: {
    CommentSection,
    textTruncation,
    ChatDotRound,
    Delete,
    Pointer,
    Star,
  },
  data() {
    return {
      items: [], // 存储列表数据
      page: 1, // 当前页码
      pageSize: 10,
      isLoading: false,
      hasMore: true,
      loadPending: false,
      totalItems: 56, // 总数据量，实际项目中可能从接口获取
      showMoreBtn: false,
      isExpanded: false,
    };
  },
  computed: {
    ...mapGetters(['avatar'])
  },
  watch: {
    listType() {
      this.resetList();
    },
    sortBy() {
      this.resetList();
    },
  },

  mounted() {
    this.resetList();
    if(!this.areaScroll) {
      window.addEventListener('scroll', this.handleScroll);
    }
  },

  beforeUnmount() {
    // 移除滚动事件监听，防止内存泄漏
    window.removeEventListener('scroll', this.handleScroll);
  },

  methods: {
    relativeTime(value) {
      return formatRelativeTime(value);
    },
    fullTime(value) {
      return formatFullTime(value);
    },
    displayAuthor(item) {
      const name = item?.userName;
      if (name && String(name).trim()) return String(name).trim();
      return `用户${item?.userId || ""}`;
    },
    authorAvatar(item) {
      return buildOssImageUrl(item?.path, item?.name) || defaultAvatarUrl();
    },

    toDetail(id) {
      window.open(location.origin + `/#/discussion/detail/${id}`, '_blank');
    },

    commentBtnLabel(item) {
      const n = item.commentCount ?? (item.commentList && item.commentList.length) ?? 0;
      return n > 0 ? `评论(${n})` : '评论';
    },
    async loadComments(row) {
      if (row._commentsLoaded && Array.isArray(row.commentList)) {
        return;
      }
      if (row._commentsLoading) return;
      row._commentsLoading = true;
      try {
        const res = await entryComments({ entryId: row.id });
        row.commentList = this._commentsPayload(res);
        row._commentsLoaded = true;
      } catch (e) {
        this.$message.error('加载评论失败');
        row.comments = false;
        row._commentsLoaded = false;
      } finally {
        row._commentsLoading = false;
      }
    },

    async menuType(row, type, index) {
      if(type == 1) {
        if (row.comments) {
          row.comments = false;
          return;
        }
        row.comments = true;
        if (!row._commentsLoaded) {
          await this.loadComments(row);
        }
      } else if(type == 2) {
        let data = {
          entryId: row.id,
          type: 1,
          isFlag: row.isLike == 1 ? 0 : 1
        }
        entryMenu(data).then(res => {
          if(res.res == true) {
            row.isLike = row.isLike == 1 ? 0 : 1;
            if(this.listType == 1) {
              this.items.splice(index, 1)
            }
          }
        })
      } else if(type == 3) {
        let data = {
          entryId: row.id,
          type: 2,
          isFlag: row.isCollect == 1 ? 0 : 1
        }
        entryMenu(data).then(res => {
          if(res.res == true) {
            row.isCollect = row.isCollect == 1 ? 0 : 1;
            if(this.listType == 2) {
              this.items.splice(index, 1)
            }
          }
        })
      } else if(type == 4) {
        this.$confirm('是否确认删除？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          deleteentry({id: row.id}).then(res => {
            if(res.res) {
              this.items.splice(index, 1)
              this.$message.success("操作成功")
              this.$forceUpdate()
            }
          })
        })
      }
      this.$forceUpdate();
    },

    openText(index) {
      this.items[index].isExpanded = !this.items[index].isExpanded;
      this.$forceUpdate()
    },
    putAway(index) {
      this.$refs['truncation' + index][0].toggleExpand()
    },

    // 处理滚动事件
    handleScrollArea() {
      if(!this.areaScroll) return;
      // 如果正在加载或没有更多数据，不执行操作
      if (this.isLoading || !this.hasMore) return;

      // 获取滚动区域的 DOM 元素
      const scrollArea = this.$refs.scrollArea;
      if (!scrollArea) return;

      // 计算滚动相关高度
      const { scrollTop, clientHeight, scrollHeight } = scrollArea;

      // 当距离底部小于 100px 时，触发加载更多
      if (scrollHeight - scrollTop - clientHeight <= 100) {
        this.loadMore();
      }
    },

    // 处理滚动事件
    handleScroll() {
      // 如果正在加载或没有更多数据，则不执行
      if (this.isLoading || !this.hasMore) return;

      // 计算滚动距离
      const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      const clientHeight = document.documentElement.clientHeight || window.innerHeight;
      const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;

      // 当滚动到距离底部200px以内时，加载更多
      if (scrollTop + clientHeight >= scrollHeight - 200) {
        this.loadMore();
      }
    },

    resetList() {
      this.items = [];
      this.page = 1;
      this.hasMore = true;
      this.isLoading = false;
      this.loadPending = false;
      this.loadMore();
    },

    parseSort() {
      const raw = String(this.sortBy || 'addTime_desc');
      const idx = raw.lastIndexOf('_');
      if (idx <= 0) return { orderBy: 'addTime', orderType: 'desc' };
      return {
        orderBy: raw.slice(0, idx),
        orderType: raw.slice(idx + 1) === 'asc' ? 'asc' : 'desc',
      };
    },

    _commentsPayload(res) {
      if (!res || !res.res) return [];
      const p = res.obj ?? res.data ?? [];
      return Array.isArray(p) ? p : (p.commentList || []);
    },

    _listPayload(res) {
      if (!res || !res.res) {
        const msg = res?.resMsg || res?.message || '请先登录后查看讨论'
        if (msg) this.$message.warning(msg)
        return { rows: [], total: 0 }
      }
      const payload = res.obj ?? res.data ?? {}
      if (Array.isArray(payload)) {
        return { rows: payload, total: payload.length }
      }
      const rows = payload.data || []
      const total = payload.recordsTotal ?? payload.recordsFiltered ?? rows.length
      return { rows, total }
    },

    loadMore() {
      if (this.loadPending || !this.hasMore) return;

      this.loadPending = true;
      this.isLoading = true;
      const { orderBy, orderType } = this.parseSort();
      const params = {
        draw: this.page,
        length: this.pageSize,
        start: (this.page - 1) * this.pageSize,
        orderBy,
        orderType,
      };
      const finish = () => {
        this.isLoading = false;
        this.loadPending = false;
      };
      const onPage = (res) => {
        const { rows: newItems, total } = this._listPayload(res);
        this.items = [...this.items, ...newItems];
        this.page++;
        const loaded = this.items.length;
        this.hasMore =
          total > 0 ? loaded < total : newItems.length >= this.pageSize;
        finish();
      };
      const onErr = (err) => {
        console.warn('[discussion] loadMore failed', err);
        this.hasMore = false;
        this.$message.error('讨论列表加载失败，请刷新页面重试');
        finish();
      };
      let req;
      if (this.listType == 0) {
        req = commenttreebulder(params);
      } else if (this.listType == 1 || this.listType == 2) {
        req = likeList({ ...params, type: this.listType });
      } else if (this.listType == 3) {
        req = publishList(params);
      } else {
        finish();
        return;
      }
      req.then(onPage).catch(onErr);
    }
  }
};
</script>

<style scoped lang="scss">
.discussion-feed {
  &--scroll {
    overflow: auto;
    max-height: calc(100vh - 220px);
  }
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
  }
}

.post-card__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.post-card__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid #f0f0f0;
}

.post-card__meta {
  flex: 1;
  min-width: 0;
}

.post-card__author-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.post-card__author {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.post-card__badge {
  font-size: 12px;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 2px 8px;
  border-radius: 4px;
}

.post-card__time-row {
  margin-top: 4px;
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.4;
}

.post-card__time-extra {
  color: #a3a3a3;
}

.post-card__title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.45;
  color: #141414;
  cursor: pointer;
  word-break: break-word;
  transition: color 0.15s;

  &:hover {
    color: var(--mainColor);
  }
}

.post-card__body {
  margin-bottom: 4px;
}

.post-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #f0f2f5;
}

.post-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  color: #595959;
  background: #f5f6f8;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s ease;

  .el-icon {
    font-size: 16px;
  }

  &:hover {
    background: #eee;
    color: #333;
  }

  &--active {
    color: var(--mainColor);
    background: rgba(233, 99, 2, 0.1);
  }

  &--danger:hover {
    color: #f56c6c;
    background: #fef0f0;
  }
}

.post-card__collapse {
  font-size: 13px;
  color: var(--mainColor);
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 0;

  &:hover {
    text-decoration: underline;
  }
}

.post-card__comments {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e8e8e8;
}

.comments-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  color: #8c8c8c;
  font-size: 14px;
}

.feed-empty {
  padding: 48px 0;
  background: #fff;
  border-radius: 14px;
}

.feed-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 28px;
  color: #8c8c8c;
  font-size: 14px;
}

.feed-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid #eee;
  border-top-color: var(--mainColor);
  border-radius: 50%;
  animation: feed-spin 0.8s linear infinite;
}

@keyframes feed-spin {
  to {
    transform: rotate(360deg);
  }
}

.feed-end {
  text-align: center;
  padding: 24px;
  font-size: 13px;
  color: #b0b0b0;
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=SimHei]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=SimHei]::before {
  content: "黑体";
  font-family: "SimHei";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Microsoft-YaHei]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Microsoft-YaHei]::before {
  content: "微软雅黑";
  font-family: "Microsoft YaHei";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=KaiTi]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=KaiTi]::before {
  content: "楷体";
  font-family: "KaiTi";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=FangSong]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=FangSong]::before {
  content: "仿宋";
  font-family: "FangSong";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Arial]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Arial]::before {
  content: "Arial";
  font-family: "Arial";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Times-New-Roman]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Times-New-Roman]::before {
  content: "Times New Roman";
  font-family: "Times New Roman";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=sans-serif]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=sans-serif]::before {
  content: "sans-serif";
  font-family: "sans-serif";
}

.ql-font-SimSun {
  font-family: "SimSun";
}

.ql-font-SimHei {
  font-family: "SimHei";
}

.ql-font-Microsoft-YaHei {
  font-family: "Microsoft YaHei";
}

.ql-font-KaiTi {
  font-family: "KaiTi";
}

.ql-font-FangSong {
  font-family: "FangSong";
}

.ql-font-Arial {
  font-family: "Arial";
}

.ql-font-Times-New-Roman {
  font-family: "Times New Roman";
}

.ql-font-sans-serif {
  font-family: "sans-serif";
}

/* 字号设置 */
/* 默认字号 */
.ql-snow .ql-picker.ql-size .ql-picker-label::before,
.ql-snow .ql-picker.ql-size .ql-picker-item::before {
  content: "16px";
}

/*.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="12px"]::before,*/
/*.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="12px"]::before {*/
/*  content: "12px";*/
/*  font-size: 12px;*/
/*}*/
/*.ql-size-12px {*/
/*  font-size: 14px;*/
/*}*/

/*.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="14px"]::before,*/
/*.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="14px"]::before {*/
/*  content: "14px";*/
/*  font-size: 14px;*/
/*}*/

/*.ql-size-14px {*/
/*  font-size: 14px;*/
/*}*/

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="16px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="16px"]::before {
  content: "16px";
  font-size: 16px;
}

.ql-size-16px {
  font-size: 16px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="18px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="18px"]::before {
  content: "18px";
  font-size: 18px;
}

.ql-size-18px {
  font-size: 18px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="20px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="20px"]::before {
  content: "20px";
  font-size: 20px;
}

.ql-size-20px {
  font-size: 20px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="22px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="22px"]::before {
  content: "22px";
  font-size: 22px;
}

.ql-size-22px {
  font-size: 22px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="26px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="26px"]::before {
  content: "26px";
  font-size: 26px;
}

.ql-size-26px {
  font-size: 26px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="28px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="28px"]::before {
  content: "28px";
  font-size: 28px;
}

.ql-size-28px {
  font-size: 28px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="30px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="30px"]::before {
  content: "30px";
  font-size: 30px;
}

.ql-size-30px {
  font-size: 30px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="34px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="34px"]::before {
  content: "34px";
  font-size: 34px;
}

.ql-size-34px {
  font-size: 34px;
}


.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="36px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="36px"]::before {
  content: "36px";
  font-size: 36px;
}

.ql-size-36px {
  font-size: 36px;
}


</style>
