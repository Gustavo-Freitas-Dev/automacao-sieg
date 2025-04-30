import flet as ft
from datetime import datetime
from ct_e import Ct_e
from nf_e import Nf_e

def main(page: ft.Page):
    page.window.icon = r"Z:\Programas\Assents\icon.ico"
    page.title = "SiegAutomator"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 500
    page.window.height = 650
    page.window.maximizable = False
    page.bgcolor = '#F2F2F2'
    page.padding = 40
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER

    meses = [ft.dropdown.Option(m) for m in [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]]
    ano_atual = datetime.now().year
    anos = [ft.dropdown.Option(str(ano)) for ano in range(2019, ano_atual + 1)]

    cnpj_input = ft.TextField(label="CNPJ", width=400, border_radius=15)
    mes_input = ft.Dropdown(label='Mês', width=400, border_radius=15, options=meses)
    ano_input = ft.Dropdown(label='Ano', width=400, border_radius=15, options=anos)
    operacao_ref = ft.Ref[ft.RadioGroup]()
    status_text = ft.Text(value="", size=14)

    # Blush overlay com ProgressRing centralizado
    blush_overlay = ft.Container(
        visible=False,
        bgcolor=ft.colors.BLACK54,
        alignment=ft.alignment.center,
        content=ft.ProgressRing(),
        expand=True,
        width=page.window.width,
        height=page.window.height,
        margin=-40
    )

    def on_executar(e):
        cnpj = cnpj_input.value.strip()
        mes = mes_input.value
        ano = ano_input.value
        operacao = operacao_ref.current.value

        if not cnpj or not mes or not ano or not operacao:
            status_text.value = "❗ Preencha todos os campos!"
            page.update()
            return

        blush_overlay.visible = True
        page.update()

        try:
            if operacao == 'Ct-e':
                status_text.value = ""
                page.update()
                Ct_e(cnpj=cnpj, ano=int(ano), mes=mes).executar()                
            elif operacao == 'Nf-e':
                status_text.value = ""
                page.update()
                Nf_e(cnpj=cnpj, ano=int(ano), mes=mes).executar()
        except Exception as erro:
            status_text.value = f"❌ Erro: {str(erro)}"
        finally:
            blush_overlay.visible = False
            page.update()

    button = ft.ElevatedButton("Executar", on_click=on_executar, width=400)

    # Conteúdo principal (como estava antes)
    conteudo = ft.Column([
        ft.Row(controls=[
            ft.Container(
                ft.Text("SIEG", size=48, weight="bold", color='#007BFF'),
                padding=ft.padding.only(top=-20)
            )
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Column([
            ft.Container(
                content=ft.Text('Digite o CNPJ:', size=18, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=10, top=20),
            ),
        ]),
        ft.Row([cnpj_input], alignment=ft.MainAxisAlignment.CENTER),

        ft.Column([
            ft.Container(
                content=ft.Text('Selecione o mês:', size=18, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=10, top=15)
            ),
        ]),
        ft.Row([mes_input], alignment=ft.MainAxisAlignment.CENTER),

        ft.Column([
            ft.Container(
                content=ft.Text('Selecione o ano:', size=18, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=10, top=15)
            ),
        ]),
        ft.Row([ano_input], alignment=ft.MainAxisAlignment.CENTER),

        ft.Row(
            controls=[
                ft.RadioGroup(
                    ref=operacao_ref,
                    content=ft.Row(
                        [
                            ft.Radio(value='Ct-e', label='Ct-e'),
                            ft.Radio(value='Nf-e', label='Nf-e'),
                        ],
                        spacing=80
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),

        ft.Column([
            ft.Container(
                content=ft.Row([button], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=20)
            ),
        ]),
        status_text
    ],
    expand=True)

    # Exibe conteúdo + overlay blush por cima
    page.add(
        ft.Stack(
            controls=[
                conteudo,
                blush_overlay
            ]
        )
    )

def executar():
    ft.app(target=main)
