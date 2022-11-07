from django.urls import path

from goals import views

urlpatterns = [
    path('goal_category/create', views.GoalCategoryCreateView.as_view(), name='create-category'),
    path('goal_category/list', views.GoalCategoryListView.as_view(), name='list-categories'),
    path('goal_category/<pk>', views.GoalCategoryView.as_view(), name='retrieve-update-destroy-category'),

    path('goal/create', views.GoalCreateView.as_view(), name='create-goal'),
    path('goal/list', views.GoalListView.as_view(), name='list-goals'),
    path('goal/<pk>', views.GoalView.as_view(), name='retrieve-update-destroy-goal'),

    path('goal_comment/create', views.GoalCommentCreateView.as_view(), name='create-comment'),
    path('goal_comment/list', views.GoalCommentListView.as_view(), name='list-comments'),
    path('goal_comment/<pk>', views.GoalCommentView.as_view(), name='retrieve-update-destroy-comment'),
]
