from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from datetime import date
import openpyxl

from .models import Aluno, Faltas



# Login

def redirecionar(request):
    print(f"usuario salvo: {request.user.username}")
    return redirect("accounts/login")

def login(request):
    if request.method == 'POST':
        username = request.POST.get('name')
        print(username)
        
        try:
            aluno = Aluno.objects.get(name=username)
            return redirect('menu_faltas')
        except Aluno.DoesNotExist:
            messages.error(request, 'Nome de usuário ou senha incorretos.')
    
    return render(request, 'aluno/login.html')


# Menus

@login_required
def menu_faltas(request):
    print(request.user)
    if not request.user.is_authenticated:
        print("Não está autenticado")
        return redirect('login')
    
    if request.user.is_superuser:
        all_alunos = Aluno.objects.all().order_by('name')  # Ordena os alunos pelo nome
        return render(request, 'aluno/menu_faltas.html', {'alunos': all_alunos})
    
    all_alunos = Aluno.objects.all().order_by('name')  # Ordena os alunos pelo nome
    return render(request, 'aluno/menu_faltas_user.html', {'alunos': all_alunos})

@login_required
def log_faltas(request):
    if request.user.is_superuser:
        all_alunos = Aluno.objects.all().order_by('name')
        return render(request, 'aluno/log_faltas.html', {'alunos': all_alunos})
    
    all_alunos = Aluno.objects.all().order_by('name')
    return render(request, 'aluno/log_faltas_user.html', {'alunos': all_alunos})


# Adicionar e remover e editar faltas

@login_required
def adicionar_falta(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    # Cria uma nova instância de falta com a data atual
    nova_falta = Faltas.objects.create(data=date.today())
    # Adiciona a nova falta ao conjunto de faltas do aluno
    aluno.faltas.add(nova_falta)
    aluno.save()
    messages.success(request, f'Falta adicionada para {aluno.name}.')
    return redirect('menu_faltas')

@login_required
def remover_falta(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    # Remove a falta mais recente (ou a última) do aluno, se houver
    if aluno.faltas.exists():
        falta_mais_recente = aluno.faltas.last()
        aluno.faltas.remove(falta_mais_recente)
        if not falta_mais_recente.aluno_set.exists():
            falta_mais_recente.delete()
        messages.success(request, f'Falta removida para {aluno.name}.')
    else:
        messages.error(request, f'O aluno {aluno.name} não tem faltas para remover.')
    return redirect('menu_faltas')

@login_required
def editar(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    FaltasFormSet = modelformset_factory(Faltas, fields=('data',), extra=0)
    
    if request.method == 'POST':
        
        # Atualiza o nome do aluno, se fornecido
        aluno.name = request.POST.get('name', aluno.name)
        aluno.save()
        
        # Formset para editar as datas das faltas
        formset = FaltasFormSet(request.POST, queryset=aluno.faltas.all())

        if formset.is_valid():
            # Salva cada instância de falta editada
            formset.save()
            # Reassocia as faltas ao aluno, garantindo que as alterações sejam salvas
            messages.success(request, f'Dados atualizados para {aluno.name}.')
            return redirect('log_faltas')
        else:
            messages.error(request, 'Erro ao salvar as alterações nas datas das faltas.')
    else:
        formset = FaltasFormSet(queryset=aluno.faltas.all())
    
    return render(request, 'aluno/editar.html', {'aluno': aluno, 'formset': formset})

@login_required
def registrar_aluno(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        
        if username:
            # Cria uma nova instância do aluno e salva no banco de dados
            aluno = Aluno.objects.create(name=username)
            aluno.save()
            messages.success(request, 'Aluno registrado com sucesso!')
            return redirect('menu_faltas')
        else:
            messages.error(request, 'O nome do aluno não pode estar vazio.')
    
    return render(request, 'aluno/registrar_aluno.html')



@login_required
def deletar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)

    faltas_do_aluno = list(aluno.faltas.all())

    aluno.delete()
    
    for falta in faltas_do_aluno:
        if not falta.aluno_set.exists():  # Verifica se a falta está associada a outros alunos
            falta.delete()  # Deleta a falta do banco de dados

    messages.success(request, f'Aluno {aluno.name} foi excluído com sucesso.')
    return redirect('log_faltas')



def download_excel(request):
    # Cria um novo workbook e ativa a planilha
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Faltas dos Alunos"

    # Cabeçalhos das colunas
    sheet.append(["Nome do Aluno", "Data da Falta", "Quantidade de Faltas"])

    # Consulta o banco de dados para obter todos os alunos com faltas
    alunos = Aluno.objects.prefetch_related('faltas').all()

    # Preenchendo a planilha com dados do banco de dados
    for aluno in alunos:
        faltas = aluno.faltas.all()
        if faltas.exists():
            # Junta todas as datas de faltas em uma única string, separadas por vírgulas e espaços
            faltas_texto = ", ".join([falta.data.strftime("%d/%m/%Y") for falta in faltas])
            quantidade_faltas = faltas.count()
            sheet.append([aluno.name, faltas_texto, quantidade_faltas])
        else:
            # Se o aluno não tiver faltas, coloca "Nenhuma falta presente" e quantidade de faltas como 0
            sheet.append([aluno.name, "", 0])

    # Configurando a resposta como um arquivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="faltas_alunos.xlsx"'
    
    # Salvando o workbook no response
    workbook.save(response)
    return response
