from django.urls import path

from apps.entry import views

urlpatterns = [
    path("commenttreebulder.ajax", views.comment_tree),
    path("publishList.ajax", views.publish_list),
    path("likeList.ajax", views.like_list),
    path("commentsByEntry.ajax", views.comments_by_entry),
    path("entryDetail.ajax", views.entry_detail),
    path("insertentry.ajax", views.insert_entry),
    path("deleteentry.ajax", views.delete_entry),
    path("updatecomment.ajax", views.update_comment),
    path("deletecomment.ajax", views.update_comment),
    path("isLike.ajax", views.entry_is_like),
    path("commentLike.ajax", views.comment_like),
    path("insertcomment.ajax", views.insert_comment),
]
