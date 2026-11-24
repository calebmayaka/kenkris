from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),
    path("account/password/", views.PanelPasswordChangeView.as_view(), name="password_change"),
    path("inquiries/", views.InquiryListView.as_view(), name="inquiries"),
    path("inquiries/<int:pk>/", views.InquiryDetailView.as_view(), name="inquiry_detail"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/new/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", views.UserEditView.as_view(), name="user_edit"),
    path("users/<int:pk>/password/", views.UserSetPasswordView.as_view(), name="user_password"),
    path("courses/", views.CourseListView.as_view(), name="courses"),
    path("courses/new/", views.CourseCreateView.as_view(), name="course_create"),
    path("courses/<int:pk>/edit/", views.CourseEditView.as_view(), name="course_edit"),
    path("courses/<int:pk>/delete/", views.CourseDeleteView.as_view(), name="course_delete"),
    path("stats/", views.StatListView.as_view(), name="stats"),
    path("stats/new/", views.StatCreateView.as_view(), name="stat_create"),
    path("stats/<int:pk>/edit/", views.StatEditView.as_view(), name="stat_edit"),
    path("stats/<int:pk>/delete/", views.StatDeleteView.as_view(), name="stat_delete"),
    path("settings/", views.SiteSettingsView.as_view(), name="site_settings"),
]
