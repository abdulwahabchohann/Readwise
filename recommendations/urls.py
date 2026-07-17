from django.urls import path

from .views.advanced_recommend import AdvancedRecommendView, advanced_recommend_page

urlpatterns = [
    path('recommend/advanced/', advanced_recommend_page, name='advanced_recommend_page'),
    path('api/recommend/advanced/', AdvancedRecommendView.as_view(), name='advanced_recommend'),
]
