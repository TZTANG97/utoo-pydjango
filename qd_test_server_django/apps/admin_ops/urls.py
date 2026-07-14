from django.urls import path

from apps.admin_ops.views import advert as advert_views
from apps.admin_ops.views import banner as banner_views
from apps.admin_ops.views import catalog as catalog_views
from apps.admin_ops.views import entry as entry_views
from apps.admin_ops.views import goods as goods_views
from apps.admin_ops.views import qd_setting as setting_views
from apps.admin_ops.views import redeem as redeem_views
from apps.admin_ops.views import whitelist as whitelist_views

urlpatterns = [
    # Banner: PC / 小程序轮播 / 小程序加载页
    path("banner/photolist.ajax", banner_views.photolist),
    path("banner/xcxfmlist.ajax", banner_views.xcxfmlist),
    path("banner/detail.ajax", banner_views.banner_detail),
    path("banner/slidecreate.ajax", banner_views.slidecreate),
    path("banner/slideupdate.ajax", banner_views.slideupdate),
    path("banner/xcxfmslidecreate.ajax", banner_views.xcxfmslidecreate),
    path("banner/xcxfmslideupdate.ajax", banner_views.xcxfmslideupdate),
    path("banner/delBanner.ajax", banner_views.del_banner),
    path("banner/updateisshow.ajax", banner_views.updateisshow),
    path("banner/updateisshow_xcx.ajax", banner_views.updateisshow),
    # Advert / AdvPos
    path("admin/advert_list.ajax", advert_views.advert_list),
    path("admin/advert_detail.ajax", advert_views.advert_detail),
    path("admin/advert_save.ajax", advert_views.advert_save),
    path("admin/advert_del.ajax", advert_views.advert_del),
    path("admin/adv_pos_list.ajax", advert_views.adv_pos_list),
    path("admin/adv_pos_detail.ajax", advert_views.adv_pos_detail),
    path("admin/adv_pos_save.ajax", advert_views.adv_pos_save),
    path("admin/adv_pos_del.ajax", advert_views.adv_pos_del),
    path("admin/adv_pos_options.ajax", advert_views.adv_pos_options),
    # QdSetting (5 content pages)
    path("edit/set_get.ajax", setting_views.setting_get),
    path("edit/set_update.ajax", setting_views.setting_update),
    # Redeem logs
    path("redeem/redeemloglist.ajax", redeem_views.redeemloglist),
    path("redeem/redeemGoodsLogDetail.ajax", redeem_views.redeem_detail),
    path("redeem/shipment.ajax", redeem_views.shipment),
    # Entry / Comment
    path("entry/entryList.ajax", entry_views.entry_list),
    path("entry/entryDetail.ajax", entry_views.entry_detail),
    path("entry/auditEntry.ajax", entry_views.audit_entry),
    path("entry/commentList.ajax", entry_views.comment_list),
    path("entry/commentDetail.ajax", entry_views.comment_detail),
    path("entry/auditComment.ajax", entry_views.audit_comment),
    path("entry/deletecomment.ajax", entry_views.delete_comment),
    # Whitelist
    path("whitelist/whitelist.ajax", whitelist_views.whitelist_list),
    path("whitelist/detail.ajax", whitelist_views.whitelist_detail),
    path("whitelist/addwhitelist.ajax", whitelist_views.add_whitelist),
    path("whitelist/updatewhitelist.ajax", whitelist_views.update_whitelist),
    path("whitelist/delete.ajax", whitelist_views.delete_whitelist),
    path("whitelist/syUsers.ajax", whitelist_views.sy_user_options),
    # Mall goods list
    path("goods/goods_list.ajax", goods_views.goods_list),
    path("goods/brand_options.ajax", goods_views.goods_brand_options),
    path("goods/class_options.ajax", goods_views.goods_class_options),
    path("goods/updateRecommend.ajax", goods_views.update_recommend),
    path("goods/goods_sale.ajax", goods_views.goods_sale),
    # Product catalog
    path("goodspec/list.ajax", catalog_views.spec_list),
    path("goodspec/detail.ajax", catalog_views.spec_detail),
    path("goodspec/save.ajax", catalog_views.spec_save),
    path("goodspec/del.ajax", catalog_views.spec_del),
    path("goodsbrand/list.ajax", catalog_views.brand_list),
    path("goodsbrand/detail.ajax", catalog_views.brand_detail),
    path("goodsbrand/save.ajax", catalog_views.brand_save),
    path("goodsbrand/del.ajax", catalog_views.brand_del),
    path("goodstype/list.ajax", catalog_views.type_list),
    path("goodstype/detail.ajax", catalog_views.type_detail),
    path("goodstype/save.ajax", catalog_views.type_save),
    path("goodstype/del.ajax", catalog_views.type_del),
    path("goodstype/options.ajax", catalog_views.type_options),
    path("goodsclass/list.ajax", catalog_views.class_list),
    path("goodsclass/detail.ajax", catalog_views.class_detail),
    path("goodsclass/save.ajax", catalog_views.class_save),
    path("goodsclass/del.ajax", catalog_views.class_del),
    path("album/list.ajax", catalog_views.album_list),
    path("album/detail.ajax", catalog_views.album_detail),
    path("album/save.ajax", catalog_views.album_save),
    path("album/del.ajax", catalog_views.album_del),
    path("album/images.ajax", catalog_views.album_images),
    path("album/image_del.ajax", catalog_views.album_image_del),
    path("album/cover.ajax", catalog_views.album_cover),
    path("evaluate/list.ajax", catalog_views.evaluate_list),
    path("evaluate/detail.ajax", catalog_views.evaluate_detail),
    path("evaluate/check.ajax", catalog_views.evaluate_check),
    path("consult/consultConfigGet.ajax", catalog_views.consult_config_get),
    path("consult/consultConfigSave.ajax", catalog_views.consult_config_save),
]
