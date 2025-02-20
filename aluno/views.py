from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from datetime import date
import openpyxl
from .models import Aluno, Faltas

# Constantes
MENU_ADMIN_TEMPLATE = 'aluno/menu_faltas.html'
MENU_USER_TEMPLATE = 'aluno/menu_faltas_user.html'
LOG_ADMIN_TEMPLATE = 'aluno/log_faltas.html'
LOG_USER_TEMPLATE = 'aluno/log_faltas_user.html'
REDIRECT_LOGIN = 'login'
REDIRECT_MENU = 'menu_faltas'

# Funções Helper
def _get_template(request, admin_template, user_template):
    """Retorna o template correto baseado no status de superusuário."""
    return admin_template if request.user.is_superuser else user_template

def _get_alunos_queryset(semestre=None):
    """Retorna queryset de alunos com otimização e filtro opcional por semestre, sempre ordenado alfabeticamente."""
    queryset = Aluno.objects.select_related().prefetch_related('faltas').order_by('name')
    if semestre in ['1', '2']:
        queryset = queryset.filter(semestre=semestre)
    return queryset

# Autenticação e Redirecionamentos
def redirecionar_user(request):
    """Redireciona para o menu do usuário."""
    return redirect('menu_faltas_user')

def redirecionar_login(request):
    """Redireciona para a página de login."""
    return redirect(REDIRECT_LOGIN)

def login(request):
    """Realiza autenticação simples baseada no nome do aluno."""
    if request.method == 'POST':
        username = request.POST.get('name')
        try:
            Aluno.objects.get(name=username)  # Validação básica
            return redirect(REDIRECT_MENU)
        except Aluno.DoesNotExist:
            messages.error(request, 'Nome de usuário ou senha incorretos.')
    return render(request, 'aluno/login.html')

# Menus
@login_required
def menu_faltas(request):
    """Exibe o menu de faltas para admin ou usuário, com alunos em ordem alfabética."""
    alunos = _get_alunos_queryset()
    template = _get_template(request, MENU_ADMIN_TEMPLATE, MENU_USER_TEMPLATE)
    return render(request, template, {'alunos': alunos})

@login_required
def menu_faltas_filtrado(request, semestre):
    """Exibe o menu de faltas filtrado por semestre, com alunos em ordem alfabética."""
    alunos = _get_alunos_queryset(semestre)
    template = _get_template(request, MENU_ADMIN_TEMPLATE, MENU_USER_TEMPLATE)
    return render(request, template, {'alunos': alunos, 'semestre': semestre})

@login_required
def menu_faltas_user(request):
    """Exibe o menu de faltas para usuários comuns, com alunos em ordem alfabética."""
    alunos = _get_alunos_queryset()
    return render(request, MENU_USER_TEMPLATE, {'alunos': alunos})

# Logs
@login_required
def log_faltas(request):
    """Exibe o log de faltas para admin ou usuário, com alunos em ordem alfabética."""
    alunos = _get_alunos_queryset()
    template = _get_template(request, LOG_ADMIN_TEMPLATE, LOG_USER_TEMPLATE)
    return render(request, template, {'alunos': alunos})

@login_required
def log_faltas_user(request):
    """Exibe o log de faltas para usuários comuns, com alunos em ordem alfabética."""
    alunos = _get_alunos_queryset()
    return render(request, LOG_USER_TEMPLATE, {'alunos': alunos})

# Gerenciamento de Faltas
@login_required
def adicionar_falta(request, aluno_id):
    """Adiciona uma nova falta para o aluno especificado."""
    aluno = get_object_or_404(Aluno, id=aluno_id)
    nova_falta = Faltas.objects.create(data=date.today())
    aluno.faltas.add(nova_falta)
    messages.success(request, f'Falta adicionada para {aluno.name}.')
    return redirect(request.GET.get('next', REDIRECT_MENU))

@login_required
def remover_falta(request, aluno_id):
    """Remove a falta mais recente do aluno especificado."""
    aluno = get_object_or_404(Aluno, id=aluno_id)
    if aluno.faltas.exists():
        falta = aluno.faltas.last()
        aluno.faltas.remove(falta)
        if not falta.aluno_set.exists():
            falta.delete()
        messages.success(request, f'Falta removida para {aluno.name}.')
    else:
        messages.error(request, f'O aluno {aluno.name} não tem faltas para remover.')
    return redirect(request.GET.get('next', REDIRECT_MENU))

@login_required
def editar(request, aluno_id):
    """Edita os dados do aluno e suas faltas."""
    aluno = get_object_or_404(Aluno, id=aluno_id)
    FaltasFormSet = modelformset_factory(Faltas, fields=('data',), extra=0)

    if request.method == 'POST':
        aluno.name = request.POST.get('name', aluno.name)
        aluno.save()
        formset = FaltasFormSet(request.POST, queryset=aluno.faltas.all())
        if formset.is_valid():
            formset.save()
            messages.success(request, f'Dados atualizados para {aluno.name}.')
            return redirect('log_faltas')
        else:
            messages.error(request, 'Erro ao salvar as alterações nas datas das faltas.')
    else:
        formset = FaltasFormSet(queryset=aluno.faltas.all())

    return render(request, 'aluno/editar.html', {'aluno': aluno, 'formset': formset})

# Gerenciamento de Alunos
@login_required
def registrar_aluno(request):
    """Registra um novo aluno com nome e semestre, capitalizando a primeira letra de cada palavra."""
    if request.method == 'POST':
        username = request.POST.get('username')
        semestre = request.POST.get('semestre')
        if username and semestre in ['1', '2']:
            # Capitaliza a primeira letra de cada palavra no nome
            username_capitalized = username.strip().title()
            Aluno.objects.create(name=username_capitalized, semestre=semestre)
            messages.success(request, 'Aluno registrado com sucesso!')
            return redirect(REDIRECT_MENU)  # Redireciona para menu_faltas, que já ordena alfabeticamente
        else:
            messages.error(request, 'Nome ou semestre inválido.')
    return render(request, 'aluno/registrar_aluno.html')

@login_required
def deletar_aluno(request, aluno_id):
    """Deleta um aluno e suas faltas associadas, se não usadas por outros."""
    aluno = get_object_or_404(Aluno, id=aluno_id)
    faltas = list(aluno.faltas.all())
    aluno.delete()
    for falta in faltas:
        if not falta.aluno_set.exists():
            falta.delete()
    messages.success(request, f'Aluno {aluno.name} foi excluído com sucesso.')
    return redirect('log_faltas')

# Exportação
@login_required
def download_excel(request):
    """Gera e retorna um arquivo Excel com o registro de faltas, em ordem alfabética."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Faltas dos Alunos"
    sheet.append(["Nome do Aluno", "Data da Falta", "Quantidade de Faltas"])

    alunos = _get_alunos_queryset()  # Já ordenado alfabeticamente
    for aluno in alunos:
        faltas = aluno.faltas.all()
        faltas_texto = ", ".join([falta.data.strftime("%d/%m/%Y") for falta in faltas]) if faltas.exists() else ""
        sheet.append([aluno.name, faltas_texto, faltas.count()])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="faltas_alunos.xlsx"'
    workbook.save(response)
    return response