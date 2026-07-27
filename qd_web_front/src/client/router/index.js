/* Layout */
import Layout from '@client/layout'
import Home from '@client/views/home'

/**
 * Note: sub-menu only appear when route children.length >= 1
 * Detail see: https://panjiachen.github.io/vue-element-admin-site/guide/essentials/router-and-nav.html
 *
 * hidden: true                   if set true, item will not show in the sidebar(default is false)
 * alwaysShow: true               if set true, will always show the root menu
 *                                if not set alwaysShow, when item has more than one children route,
 *                                it will becomes nested mode, otherwise not show the root menu
 * redirect: noRedirect           if set noRedirect will no redirect in the breadcrumb
 * name:'router-name'             the name is used by <keep-alive> (must set!!!)
 * meta : {
 roles: ['admin','editor']    control the page roles (you can set multiple roles)
 title: 'title'               the name show in sidebar and breadcrumb (recommend set)
 icon: 'svg-name'/'el-icon-x' the icon show in the sidebar
 breadcrumb: false            if set false, the item will hidden in breadcrumb(default is true)
 activeMenu: '/example/list'  if set path, the sidebar will highlight the path you set
 }
 */

/**
 * constantRoutes
 * a base page that does not have permission requirements
 * all roles can be accessed
 */
/** 动态路由（本项目的业务路由均在 constantRoutes，保留空数组供 permission 模块） */
export const asyncRoutes = []

export const constantRoutes = [
  {
    path: '/',
    hidden: true,
    component: Home,
    redirect: { path: '/home' },
    children: [
      {
        path: 'home',
        name: 'Test',
        component: () => import('@client/views/test/index')
      },
      {
        path: 'test_detail/:id',
        component: () => import('@client/views/testDetail/index')
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@client/views/login/index')
      },
      {
        path: 'cate',
        name: 'Cate',
        component: () => import('@client/views/cate/index'),
        meta: { title: '实验项目' }
      },
      {
        path: 'cateDetail',
        name: 'CateDetail',
        component: () => import('@client/views/cateDetail/index'),
        meta: { title: '分类详情' }
      },
      {
        path: 'discussion',
        name: 'Discussion',
        hidden: true,
        meta: {title: '讨论'},
        component: () => import('@client/views/discussion/index')
      },

      {
        path: 'discussion/detail/:id',
        name: 'DiscussionDetail',
        hidden: true,
        meta: {title: '讨论详情'},
        component: () => import('@client/views/discussion/detail')
      },
    ]
  },
  {
    path: '/make/:id',
    name: 'Make',
    hidden: true,
    meta: {title: '查看预约单'},
    component: () => import('@client/views/make/index')
  },
  {
    path: '/companyInt',
    name: 'CompanyInt',
    hidden: true,
    meta: {title: '公司介绍'},
    component: () => import('@client/views/companyInt/index')
  },
  // {
  //   path: '/b',
  //   component: Layout,
  //   // 重定向到子路由
  //   redirect: '/b/welcome',
  //   children: [{
  //     path: 'welcome',
  //     name: 'Welcome',
  //     component: () => import('@client/views/welcome/index'),
  //     meta: {title: '仪表盘', icon: 'dashboard'},
  //     hidden: true
  //   }]
  // },
  {
    path: '/b',
    component: Layout,
    redirect: '/b/order',
    children: [
      {
        path: 'order',
        name: 'Order',
        component: () => import('@client/views/order/index.vue'),
        meta: {title: '我的订单', icon: 'order'}
      },
      {
        path: 'order_detail/:id',
        name: 'OrderDetail',
        component: () => import('@client/views/orderDetail/index'),
        hidden: true,
        meta: { title: '订单详情' }
      },
      {
        path: 'order_detail2/:id',
        name: 'OrderDetail2',
        component: () => import('@client/views/orderDetail2/index'),
        hidden: true,
        meta: { title: '兑换详情' }
      },
      {
        path: 'child_order_detail/:id',
        name: 'ChildOrderDetail',
        component: () => import('@client/views/childOrderDetail/index'),
        hidden: true,
        meta: { title: '子订单详情' }
      },
    ]
  },
  {
    path: '/b/property',
    component: Layout,
    children: [{
      path: '',
      name: 'Property',
      component: () => import('@client/views/property/index'),
      meta: {title: '我的资产', icon: 'property'},
    }]
  },
  {
    path: '/b/integral',
    component: Layout,
    children: [{
      path: '',
      name: 'Integral',
      component: () => import('@client/views/integral/index'),
      meta: {title: '我的积分', icon: 'integral'},
    }]
  },
  {
    path: '/b/invoice',
    component: Layout,
    children: [{
      path: '',
      name: 'Invoice',
      component: () => import('@client/views/invoice/index'),
      meta: {title: '发票管理', icon: 'invoice'},
    }]
  },
  {
    path: '/b/profile',
    component: Layout,
    children: [{
      path: '',
      name: 'Profile',
      component: () => import('@client/views/profile/index'),
      meta: {title: '个人资料', icon: 'user'},
    }]
  },
  {
    path: '/b/sub',
    component: Layout,
    children: [{
      path: '',
      name: 'Sub',
      component: () => import('@client/views/sub/index'),
      meta: {title: '我的预约', icon: 'sub'},
    }]
  },
  {
    path: '/b/sub_detail',
    component: Layout,
    hidden: true,
    children: [{
      path: '',
      name: 'SubDetail',
      component: () => import('@client/views/sub_detail/index'),
      meta: { title: '预约详情' },
    }]
  },
  {
    path: '/b/billing',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'Billing',
      component: () => import('@client/views/billing/index'),
      meta: {title: '开票'},
    }]
  },
  {
    path: '/b/pay_history',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'payHistory',
      component: () => import('@client/views/payHistory/index'),
      meta: {title: '流水明细'},
    }]
  },
  {
    path: '/b/repayment',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'repayment',
      component: () => import('@client/views/repayment/index'),
      meta: {title: '支付'},
    }]
  },
  {
    path: '/b/make_invoice_detail/:id',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'makeInvoiceDetail',
      component: () => import('@client/views/makeInvoiceDetail/index'),
      meta: { title: '开票详情' },
    }]
  },
  {
    path: '/b/pay_detail/:id',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'payDetail',
      component: () => import('@client/views/payDetail/index'),
      meta: { title: '充值详情' },
    }]
  },
  {
    path: '/b/payment_detail/:id',
    hidden: true,
    component: Layout,
    children: [{
      path: '',
      name: 'paymentDetail',
      component: () => import('@client/views/paymentDetail/index'),
      meta: { title: '支付详情' },
    }]
  },
  {
    path: '/discussionNotes',
    component: Layout,
    children: [{
      path: '',
      name: 'paymentDetail',
      component: () => import('@client/views/discussionNotes/index'),
      meta: {title: '喜欢\\收藏', icon: 'star'}
    }]
  },
  {
    path: '/discussionNotes/issue',
    component: Layout,
    children: [
      {
        path: '',
        name: 'discussionIssue',
        hidden: true,
        component: () => import('@client/views/discussionNotes/issue'),
        meta: {title: '发布'}
      }
    ]
  },



  {
    path: '/404',
    component: () => import('@client/views/404'),
    hidden: true
  },
  {
    path: '/redirect',
    component: Layout,
    hidden: true,
    redirect: '/b/order',
    children: [
      {
        path: ':path(.*)',
        component: () => import('@client/views/redirect/index')
      }
    ]
  },

  // 404 page must be placed at the end !!!
  { path: '/:pathMatch(.*)*', redirect: '/404', hidden: true },
]

/** 路由表由根 src/router 合并；此处仅导出 routes */
export const clientRoutes = constantRoutes

export function resetRouter(router) {
  if (!router) return
  router.getRoutes().forEach((route) => {
    if (route.name) router.removeRoute(route.name)
  })
}
