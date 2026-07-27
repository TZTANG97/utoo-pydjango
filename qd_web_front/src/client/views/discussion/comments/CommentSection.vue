<template>
  <div class="comment-section">
    <h3 class="section-title">评论区</h3>
    <!-- 评论输入框 -->
    <div class="comment-input-container">
      <img
        :src="currentUserAvatar"
        alt="当前用户头像"
        class="user-avatar"
        @error="onAvatarError"
      >
      <div class="input-wrapper">
        <textarea
          v-model="newCommentContent"
          placeholder="分享你的想法..."
          class="comment-input"
        ></textarea>
        <button
          class="submit-btn"
          @click="handleCommentSubmit"
          :disabled="!newCommentContent.trim()"
        >
          发布评论
        </button>
      </div>
    </div>

    <!-- 评论列表 -->
    <div class="comments-list">
      <div
        v-for="(comment, commentIndex) in comments"
        :key="comment.id"
        class="comment-item"
      >
        <!-- 评论头部 -->
        <div class="comment-header" style="justify-content: space-between">
          <div class="comment-header">
            <img
              :src="commentAvatar(comment)"
              :alt="comment.userName + '的头像'"
              class="comment-avatar"
            >
            <div class="comment-author-info">
              <span class="author-name">{{ comment.userName }}</span>
              <span class="comment-time">{{ formatTime(comment.addTime) }}</span>
            </div>
          </div>
          <div class="isAudit">{{comment.isAudit == 1 ? '' : '待审核'}}</div>
        </div>

        <!-- 评论内容 -->
        <div class="comment-content">
          {{comment.content}}
        </div>

        <!-- 评论操作 -->
        <div class="comment-actions">
          <button
            class="action-btn like-btn"
            @click="handleLike(comment)"
          >
            <img class="menu-icon" src="@client/static/zan.png" v-if="comment.isLike != 1" />
            <img class="menu-icon" src="@client/static/zan1.png" v-if="comment.isLike == 1"/>
            <span>{{ comment.likeCount || 0 }}</span>
          </button>
          <button
            class="action-btn reply-btn"
            @click="toggleReply(commentIndex)"
          >
            <i class="fa fa-reply"></i>
            <span>回复</span>
          </button>
          <button
            class="action-btn reply-btn"
            v-if="listType == 3 || comment.deleteQx"
            @click="deleteReply(commentIndex)"
          >
            <i class="fa fa-reply"></i>
            <span>删除</span>
          </button>
        </div>

        <!-- 回复输入框 -->
        <div
          v-if="comment.showReplyInput"
          class="reply-input-container"
        >
          <img
            :src="currentUserAvatar"
            alt="当前用户头像"
            class="reply-avatar"
          >
          <div class="reply-input-wrapper">
            <textarea
              v-model="comment.newReplyContent"
              :placeholder="`回复 ${ comment.userName || '' }...`"
              class="reply-input"
            ></textarea>
            <div class="reply-actions">
              <button
                class="cancel-btn"
                @click="toggleReply(commentIndex)"
              >
                取消
              </button>
              <button
                class="submit-reply-btn"
                @click="handleReplySubmit(commentIndex)">
                回复
              </button>
            </div>
          </div>
        </div>

        <!-- 回复列表 -->
        <div class="replies-list" v-if="comment.replies.length > 0">
          <div v-for="(reply, replyIndex) in comment.replies"  :key="reply.id">
            <div class="reply-item">
              <img
                :src="commentAvatar(reply)"
                :alt="reply.userName + '的头像'"
                class="reply-avatar"
              >
              <div class="reply-content">
                <div class="top_box">
                  <div>
                    <span class="reply-author">{{ reply.userName }}</span>
                    <i class="el-icon-caret-right" style="margin-right: 6px" v-if="reply.puserName && (reply.parentId != comment.id)"></i>
                    <span class="reply-text">
                      <span v-if="reply.puserName && (reply.parentId != comment.id)">{{ reply.puserName }} </span>
                    </span>
                  </div>

                  <div class="isAudit">{{reply.isAudit == 1 ? '' : '待审核'}}</div>
                </div>

                <div style="margin-top: 5px">
                  {{ reply.content }}
                </div>
                <div class="reply-actions">
                  <span class="reply-time">{{ formatTime(reply.addTime) }}</span>
                  <button class="reply-like-btn" @click="handleReplyLike(commentIndex, replyIndex)">
                    <img class="menu-icon" src="@client/static/zan.png" v-if="reply.isLike != 1" />
                    <img class="menu-icon" src="@client/static/zan1.png" v-if="reply.isLike == 1"/>
                    <span>{{ reply.likeCount || 0 }}</span>
                  </button>
                  <button class="reply-reply-btn" @click="toggleReplyToReply(commentIndex, replyIndex)">
                    回复
                  </button>
                  <button class="reply-reply-btn" v-if="listType == 3 || reply.deleteQx" @click="deleteReplyToReply(commentIndex, replyIndex)">
                    删除
                  </button>
                </div>
              </div>
            </div>
            <!-- 回复输入框 -->
            <div
              v-if="reply.showReplyInput"
              class="reply-input-container"
            >
              <img
                :src="currentUserAvatar"
                alt="当前用户头像"
                class="reply-avatar"
              >
              <div class="reply-input-wrapper">
            <textarea
              v-model="reply.newReplyContent"
              :placeholder="`回复 ${ reply.userName || '' }...`"
              class="reply-input"
            ></textarea>
                <div class="reply-actions">
                  <button class="cancel-btn" @click="closeReply(commentIndex, replyIndex)">
                    取消
                  </button>
                  <button class="submit-reply-btn" @click="replySubmit(commentIndex, replyIndex)">
                    回复
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 查看更多回复 -->
<!--          <button v-if="comment.replies.length > 2 && !comment.showAllReplies" class="show-more-replies"-->
<!--            @click="openMoreReplies(comment)">-->
<!--            查看更多回复-->
<!--          </button>-->
        </div>
      </div>
    </div>

    <!-- 加载更多评论 -->
<!--    <button-->
<!--      v-if="hasMoreComments"-->
<!--      class="load-more-comments"-->
<!--      @click="loadMoreComments"-->
<!--    >-->
<!--      加载更多评论-->
<!--    </button>-->
  </div>
</template>

<script>

// 生成随机ID
import {mapGetters} from "vuex";
import {commentLike, deletecomment, deleteentry, insertcomment} from "@client/api/discussion"
import { buildOssImageUrl, defaultAvatarUrl } from "@client/utils/oss-image"
import { formatRelativeTime } from "@client/utils/format-time"

const generateId = () => Math.floor(Math.random() * 1000000);

export default {
  components: {

  },
  data() {
    return {
      newCommentContent: '',
      comments: [],
      hasMoreComments: true,
      page: 1,
      pageSize: 5
    };
  },
  props: {
    commentList: {
      type: Array,
      default: () => {
        return []
      }
    },
    listType: {
      type: Number,
      default: 0
    },
    row: {
      type: Object,
      default: () => {
        return {}
      }
    }
  },
  computed: {
    ...mapGetters(['avatar', 'authInfo']),
    currentUserAvatar() {
      return this.avatar || defaultAvatarUrl()
    },
  },
  watch: {
    commentList: {
      handler(list) {
        this.syncComments(list)
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    onAvatarError(e) {
      if (e?.target) e.target.src = defaultAvatarUrl()
    },
    commentAvatar(row) {
      if (row && row.avatar) {
        return row.avatar
      }
      return buildOssImageUrl(row?.path, row?.name) || defaultAvatarUrl()
    },
    syncComments(list) {
      const src = list ?? this.commentList
      this.comments = Array.isArray(src) ? [...src] : []
    },
    openMoreReplies(row) {
      console.log('显示更多评论')

    },
    deleteReply(commentIndex) {
        let comments = this.comments[commentIndex];
        this.$confirm('是否确认删除？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          deletecomment({id: comments.id}).then(res => {
            if(res.res) {
              this.comments.splice(commentIndex, 1)
              this.$message.success("操作成功")
              this.$forceUpdate()
            }
          })
        })
    },
    deleteReplyToReply(commentIndex, replyIndex) {
        let comments = this.comments[commentIndex];
        let reply = comments.replies[replyIndex];
        console.log(reply)
        this.$confirm('是否确认删除？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          deletecomment({id: reply.id}).then(res => {
            if(res.res) {
              comments.replies.splice(replyIndex, 1)
              this.$message.success("操作成功")
              this.$forceUpdate()
            }
          })
        })
    },

    // 格式化时间
    formatTime(timestamp) {
      return formatRelativeTime(timestamp) || ''
    },

    // 加载更多评论
    loadMoreComments() {
      // 模拟API请求
      setTimeout(() => {
        // const newComments = Array.from({ length: this.pageSize }, (_, i) => {
        //   const randomUser = users[Math.floor(Math.random() * users.length)];
        //   const commentLength = Math.floor(Math.random() * 300) + 20;
        //
        //   return {
        //     id: generateId(),
        //     userName: randomUser.name,
        //     avatar: randomUser.avatar,
        //     content: this.generateRandomText(commentLength),
        //     addTime: Date.now() - Math.floor(Math.random() * 86400000 * 7),
        //     likeCount: Math.floor(Math.random() * 50),
        //     liked: false,
        //     showReplyInput: false,
        //     newReplyContent: '',
        //     replies: this.generateRandomReplies(Math.floor(Math.random() * 5)),
        //     showAllReplies: false
        //   };
        // });

        // this.comments = [...this.comments, ...newComments];
        // this.page++;

        // 模拟数据有限，5页后没有更多评论
        if (this.page > 5) {
          this.hasMoreComments = false;
        }
      }, 800);
    },

    // 生成随机文本
    generateRandomText(length) {
      const words = ['这是', '一个', '非常', '好的', '想法', '我同意', '不同意', '观点', '有趣', '精彩', '确实', '应该', '可能', '一定', '不错', '支持', '反对', '建议', '考虑', '分析', '讨论', '分享', '经验', '故事', '经历', '感受', '想法', '观点', '看法', '意见'];
      let text = '';

      while (text.length < length) {
        const randomWord = words[Math.floor(Math.random() * words.length)];
        text += randomWord + ' ';
      }

      return text.trim();
    },

    // 生成随机回复
    generateRandomReplies(count) {
      return Array.from({ length: count }, () => {
        const randomUser = users[Math.floor(Math.random() * users.length)];
        return {
          id: generateId(),
          userName: randomUser.name,
          avatar: randomUser.avatar,
          toAuthor: Math.random() > 0.5 ? users[Math.floor(Math.random() * users.length)].name : null,
          content: this.generateRandomText(Math.floor(Math.random() * 100) + 10),
          addTime: Date.now() - Math.floor(Math.random() * 86400000 * 3),
          likeCount: Math.floor(Math.random() * 10),
          liked: false
        };
      });
    },

    // 提交评论
    handleCommentSubmit() {
      if (!this.newCommentContent.trim()) return;
      let data = {
        entryId: this.row.id,
        content: this.newCommentContent.trim(),
      }
      insertcomment(data).then(res => {
        console.log(res)
        if(res.res == true) {
          res.obj.replies = []
          // 添加到评论列表开头
          this.comments.unshift(res.obj);
          this.newCommentContent = '';
        }
      })

    },

    // 点赞评论
    handleLike(comment) {
      let data = {
        commentId: comment.id,
        isFlag: comment.isLike == 1 ? 0 : 1
      }
      commentLike(data).then(res => {
        if(res.res) {
          comment.likeCount = res.obj.likeCount;
          comment.isLike = comment.isLike == 1 ? 0 : 1 ;
          this.$forceUpdate();
        }
      })

    },

    // 切换回复输入框显示
    toggleReply(commentIndex) {
      this.comments[commentIndex].showReplyInput = !this.comments[commentIndex].showReplyInput;

      // 如果显示回复框，清空输入内容
      if (this.comments[commentIndex].showReplyInput) {
        this.comments[commentIndex].newReplyContent = '';
      }
      this.$forceUpdate()
    },


    // 提交回复
    handleReplySubmit(commentIndex) {
      const comment = this.comments[commentIndex];
      if (!comment.newReplyContent.trim()) return;
      let data = {
        entryId: this.row.id,
        content: comment.newReplyContent.trim(),
        topLevel: comment.id,
        parentId: comment.id
      }
      insertcomment(data).then(res => {
        console.log(res)
        if(res.res == true) {
          // 添加到评论列表开头
          comment.replies.unshift(res.obj);
          comment.newReplyContent = '';
          comment.showReplyInput = false;
        }
      })

    },

    // 点赞回复
    handleReplyLike(commentIndex, replyIndex) {
      const reply = this.comments[commentIndex].replies[replyIndex];
      let data = {
        commentId: reply.id,
        isFlag: reply.isLike == 1 ? 0 : 1
      }
      commentLike(data).then(res => {
        if(res.res) {
          reply.likeCount = res.obj.likeCount;
          reply.isLike = reply.isLike == 1 ? 0 : 1 ;
          this.$forceUpdate();
        }
      })

    },

    // 回复别人的回复
    toggleReplyToReply(commentIndex, replyIndex) {
      console.log(commentIndex, replyIndex)
      const comment = this.comments[commentIndex];
      const reply = comment.replies[replyIndex];

      reply.showReplyInput = true;
      reply.newReplyContent = ``;

      // 滚动到回复框
      this.$nextTick(() => {
        const replyInput = this.$el.querySelector(`.reply-input-container textarea`);
        if (replyInput) {
          replyInput.focus();
          // 将光标移动到末尾
          replyInput.setSelectionRange(replyInput.value.length, replyInput.value.length);
        }
      });
      this.$forceUpdate()
    },
    // 提交回复别人的回复
    replySubmit(commentIndex, replyIndex) {
      console.log(commentIndex, replyIndex)
      const comment = this.comments[commentIndex];
      const reply = comment.replies[replyIndex];
      if (!reply.newReplyContent.trim()) return;

      let data = {
        entryId: this.row.id,
        content: reply.newReplyContent.trim(),
        topLevel: comment.id,
        parentId: reply.id
      }
      insertcomment(data).then(res => {
        if(res.res == true) {
          // 添加到评论列表开头
          comment.replies.splice(replyIndex+1, 0, res.obj);
          reply.newReplyContent = '';
          reply.showReplyInput = false;
          this.$forceUpdate()
        }
      })


      // const newReply = {
      //   id: generateId(),
      //   userName: this.authInfo.show_name,
      //   avatar: this.authInfo.avatar,
      //   toAuthor: reply.userName,
      //   content: reply.newReplyContent.trim(),
      //   addTime: Date.now(),
      //   likeCount: 0,
      //   liked: false
      // };


    },
    // 切换回复输入框显示
    closeReply(commentIndex, replyIndex) {
      this.comments[commentIndex].replies[replyIndex].showReplyInput = !this.comments[commentIndex].replies[replyIndex].showReplyInput;

      // 如果显示回复框，清空输入内容
      if (this.comments[commentIndex].replies[replyIndex].showReplyInput) {
        this.comments[commentIndex].replies[replyIndex].newReplyContent = '';
      }
      this.$forceUpdate()
    },
  }
};
</script>

<style scoped>
.comment-section {
  margin: 0 auto;
  color: #333;
}

.section-title {
  font-size: 20px;
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

/* 评论输入框样式 */
.comment-input-container {
  display: flex;
  gap: 12px;
  margin-bottom: 30px;
}

.user-avatar, .comment-avatar, .reply-avatar {
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar {
  width: 40px;
  height: 40px;
}

.input-wrapper {
  flex: 1;
}

.comment-input, .reply-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: vertical;
  min-height: 80px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.comment-input:focus, .reply-input:focus {
  outline: none;
  border-color: #3498db;
}

.submit-btn {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.submit-btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.submit-btn:not(:disabled):hover {
  background-color: #2980b9;
}

/* 评论列表样式 */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.comment-item {
  padding-bottom: 24px;
  border-bottom: 1px solid #f1f1f1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
}

.author-name {
  font-weight: 500;
  font-size: 14px;
}

.comment-time {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.comment-content {
  margin-bottom: 12px;
  line-height: 1.6;
  font-size: 14px;
  white-space: break-spaces;
}

/* 评论操作按钮 */
.comment-actions {
  display: flex;
  gap: 16px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
}

.action-btn:hover {
  background-color: #f5f5f5;
  color: #3498db;
}

.like-btn .liked {
  color: #e74c3c;
}

/* 回复相关样式 */
.reply-input-container {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  margin-bottom: 16px;
}

.reply-avatar {
  width: 32px;
  height: 32px;
}

.reply-input-wrapper {
  flex: 1;
}

.reply-input {
  min-height: 60px;
  font-size: 13px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

.cancel-btn {
  padding: 6px 12px;
  background-color: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background-color: #e9e9e9;
}

.submit-reply-btn {
  padding: 6px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s;
}

.submit-reply-btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.submit-reply-btn:not(:disabled):hover {
  background-color: #2980b9;
}

/* 回复列表样式 */
.replies-list {
  margin-top: 16px;
  margin-left: 48px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reply-item {
  display: flex;
  gap: 8px;
  padding: 8px 0;
}

.reply-content {
  flex: 1;
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 8px;
  font-size: 13px;
}

.reply-author {
  font-weight: 500;
  margin-right: 6px;
}

.reply-text {
  line-height: 1.5;
}

.reply-actions {
  display: flex;
  gap: 16px;
  margin-top: 6px;
  font-size: 12px;
  color: #999;
}

.reply-like-btn, .reply-reply-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 2px;
}

.reply-like-btn:hover, .reply-reply-btn:hover {
  color: #3498db;
}

.reply-like-btn .liked {
  color: #e74c3c;
}

.show-more-replies {
  margin-top: 8px;
  padding: 4px 0;
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.show-more-replies:hover {
  text-decoration: underline;
}

/* 加载更多评论按钮 */
.load-more-comments {
  width: 100%;
  padding: 10px;
  margin-top: 20px;
  background-color: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.load-more-comments:hover {
  background-color: #e9e9e9;
}
.menu-icon {
  width: 15px;
  margin-right: 5px;
}
.isAudit {
  font-size: 14px;
  color: #999999;
}
.top_box {
  display: flex;
  justify-content: space-between;
}
</style>
