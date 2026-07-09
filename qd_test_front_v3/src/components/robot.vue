<script>
import eventBus from "@/utils/event-bus";

export default {
  name: "Robot",
  data() {
    return {
      send_content: ''
    }
  },
  methods: {
    send() {
      if (!this.send_content) return
      console.log(this.send_content)
    },
    changeVal(val) {
      eventBus.$emit('changeVal', val)
    },
  }
}
</script>

<template>
  <div class="robot" @mouseenter="changeVal(true)" @mouseleave="changeVal(false)">
    <header>

    </header>
    <div class="chat">
      <div class="left">
        <img class="default-head" src="@/static/kf.jpg" alt="">
        <div class="content">您好，我是客服你爹 ，你爹欢迎你！</div>
      </div>

      <div class="guess">
        <div class="title">猜您想问：</div>
        <div class="label-list">
          <div class="label">保单服务</div>
          <div class="label">保单务</div>
          <div class="label">保单服务啊</div>
          <div class="label">保单</div>
          <div class="label">保单服务</div>
          <div class="label">保单服</div>
        </div>

        <div class="link-list">
          <div class="link">我要退保啊</div>
          <div class="link">我要</div>
          <div class="link">我要保</div>
          <div class="link">我要退保</div>
          <div class="link">我要退保</div>
          <div class="link">我保</div>
        </div>

        <div class="change">换一批</div>
      </div>

      <div class="right">
        <div class="content">怎么下单</div>
        <img class="default-head" src="@/static/user.png" alt="">
      </div>
    </div>
    <div class="input">
      <input type="text" maxlength="30" placeholder="请输入您的问题" @keyup.enter="send" v-model="send_content">
      <div class="send" @click="send">发送</div>
    </div>
  </div>
</template>

<style scoped lang="scss">



.guess {
  padding: 8px;
  background-color: #fff;
  border-radius: 3px;
  margin: 15px 0;

  .change {
    text-align: right;
    color: var(--mainColor);
    margin: 16px 8px 0 0;
    cursor: pointer;
  }

  .label-list {
    padding: 0 8px;
    .label {
      display: inline-block;
      padding: 4px 11px;
      background-color: #E5E5E5;
      border-radius: 25px;
      margin: 8px 8px 0 0;
      cursor: pointer;
    }
  }

  .link-list {
    padding: 0 8px;
    margin-top: 24px;
    .link {
      color: var(--mainColor);
      cursor: pointer;
      &:nth-child(n+2) {
        margin-top: 16px;
      }
    }
  }
}

header {
  height: 20px;
}

.chat {
  height: 330px;
  background-color: #E6F0F9;
  padding: 8px;
  overflow-y: scroll;
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
  ::-webkit-scrollbar {
    display: none;
  }


  .default-head {
    display: inline-block;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    vertical-align: top;
  }

  .content {
    display: inline-block;
    max-width: 288px;
    padding: 8px;
    background-color: #fff;
    border-radius: 8px;
    word-wrap: break-word;
    margin-top: 15px;
  }

  .left {
    .content {
      margin-left: 8px;
      border-top-left-radius: 0;
    }
  }

  .right {
    text-align: right;

    .content {
      margin-right: 8px;
      border-top-right-radius: 0;
      text-align: left;
    }
  }
}

.input {
  display: flex;
  align-items: center;
  position: relative;
  height: 50px;
  background-color: #fff;
  padding: 8px;
  z-index: 10;

  input {
    flex-grow: 1;
    height: 100%;
    border-radius: 25px;
    font-size: 13px;
    padding: 0 8px;
    outline: none;
    border: 1px solid var(--mainColor);
    color: #57636f;
  }

  .send {
    margin-left: 8px;
    color: var(--mainColor);
    cursor: pointer;
  }
}

.robot {
  width: 400px;
  height: 400px;
  background-color: #F4F4F4;
  font-size: 13px !important;
  color: #57636f;
  line-height: 1;
}
</style>
