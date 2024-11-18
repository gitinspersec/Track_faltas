from django.urls import path

from . import views

urlpatterns = [
    path('', views.redirecionar, name='redirecionar'),
    path('log_faltas/', views.log_faltas, name='log_faltas'),
    path('log_faltas_user/', views.log_faltas, name='log_faltas'),
    path('menu_faltas/', views.menu_faltas, name='menu_faltas'),
    path('menu_faltas_user/', views.menu_faltas, name='menu_faltas'),
    path('editar/<int:aluno_id>', views.editar, name='editar'),
    path('adicionar_falta/<int:aluno_id>/', views.adicionar_falta, name='adicionar_falta'),
    path('remover_falta/<int:aluno_id>/', views.remover_falta, name='remover_falta'),
    path('registrar_aluno/', views.registrar_aluno, name='registrar_aluno'),
    path('download_excel/', views.download_excel, name='download_excel'),
    path('aluno/deletar/<int:aluno_id>/', views.deletar_aluno, name='deletar_aluno'),
]