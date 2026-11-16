from django.urls import path
from django.views.generic import RedirectView

from .views.advanced_recommend import AdvancedRecommendView

urlpatterns = [
    path(
        'recommend/advanced/',
        RedirectView.as_view(pattern_name='recommendations', permanent=False),
        name='advanced_recommend_page',
    ),
    path('api/recommend/advanced/', AdvancedRecommendView.as_view(), name='advanced_recommend'),
]
