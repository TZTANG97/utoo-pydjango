import request from '@client/utils/request'

// 获取帖子列表
const DISCUSSION_TIMEOUT = 60000

export function commenttreebulder(params) {
  return request({
    url: '/entry/commenttreebulder.ajax',
    params,
    timeout: DISCUSSION_TIMEOUT,
  })
}

// 获取喜欢|收藏的帖子列表
export function likeList(params) {
  return request({
    url: '/entry/likeList.ajax',
    params,
    timeout: DISCUSSION_TIMEOUT,
  })
}
// 获取发布的帖子列表
export function publishList(params) {
  return request({
    url: '/entry/publishList.ajax',
    params,
    timeout: DISCUSSION_TIMEOUT,
  })
}

// 喜欢收藏
export function entryMenu(params) {
  return request({
    url: '/entry/isLike.ajax',
    method: 'get',
    params,
  })
}

// 评论
export function insertcomment(params) {
  return request({
    url: '/entry/insertcomment.ajax',
    method: 'get',
    params,
  })
}


// 评论
export function insertentry(params) {
  return request({
    url: '/entry/insertentry.ajax',
    method: 'post',
    data: params,
  })
}

// 点赞评论
export function commentLike(params) {
  return request({
    url: '/entry/commentLike.ajax',
    method: 'get',
    params: params,
  })
}

// 按帖子懒加载评论树
export function entryComments(params) {
  return request({
    url: '/entry/commentsByEntry.ajax',
    method: 'get',
    params,
    timeout: DISCUSSION_TIMEOUT,
  })
}

// 帖子详情
export function entryDetail(params) {
  return request({
    url: '/entry/entryDetail.ajax',
    method: 'get',
    params: params,
  })
}

// 删除帖子
export function deleteentry(params) {
  return request({
    url: '/entry/deleteentry.ajax',
    method: 'get',
    params: params,
  })
}

// 删除评论
export function deletecomment(params) {
  return request({
    url: '/entry/updatecomment.ajax',
    method: 'get',
    params: params,
  })
}

