from playwright.sync_api import sync_playwright
from pathlib import Path
import openpyxl as px
from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil
import pandas as pd

load_dotenv(override=True)

class Nf_e:
    def __init__(self, cnpj, ano, mes):
        self.cnpj = cnpj
        self.ano = ano
        self.mes = mes
        self.email = os.getenv("EMAIL")
        self.senha = os.getenv("SENHA")
        self.pasta_downloads = Path("downloads")
        self.pasta_downloads.mkdir(exist_ok=True)
        self.dados = []

    def iniciar_navegador(self):
        self.playwright = sync_playwright().start()
        self.navegador = self.playwright.chromium.launch(channel='chrome', headless=True)
        self.contexto = self.navegador.new_context(accept_downloads=True)
        self.pagina = self.contexto.new_page()

    def fechar_navegador(self):
        self.navegador.close()
        self.playwright.stop()

    def login(self):
        self.pagina.goto("https://auth.sieg.com/login?ReturnUrl=https%3a%2f%2fhub.sieg.com%2fdefault.aspx")
        self.pagina.fill('#txtEmail', self.email)
        self.pagina.fill('#txtPassword', self.senha)
        self.pagina.click('#btnSubmit')
        self.pagina.wait_for_timeout(2000)

    def navegar_para_xml(self):
        self.pagina.goto("https://cofre.sieg.com/xml")
        self.pagina.select_option('select#MainContent_cphMainContent_ListXmlFolder_ddlOrder_Xml', value='2')
        self.pagina.click(f"a.link-folder >> text={self.ano}")
        self.pagina.click(f"a.link-folder >> text={self.mes}")
        self.pagina.click('#cnpj-adv-opt')
        self.pagina.wait_for_timeout(2000)
        self.pagina.fill('input.search-table-all', self.cnpj)
        self.pagina.click('button.btn-search-cnpj')
        self.pagina.wait_for_timeout(2000)
        self.pagina.click(f'a.link-folder >> text={self.cnpj}')

    def gerar_danfe(self):
        self.tags = []
        self.pagina.wait_for_selector('tbody.table-click tr')
        linhas = self.pagina.query_selector_all('tbody.table-click tr')

        for idx, linha in enumerate(linhas):
            tags = linha.query_selector('.icon-tag-table')
            if tags:
                pai_a = tags.query_selector('xpath=..')
                if pai_a:
                    esconder = pai_a.query_selector('.esconder')
                    if esconder:
                        texto = esconder.inner_text().strip()
                        if texto:
                            self.tags.append(texto)

            linha.click(button='right')
            with self.pagina.expect_download() as download_info:
                self.pagina.click('text=Download NF-e')
            download = download_info.value
            nome_arquivo = f"{idx + 1:02d} cte.xml"
            download.save_as(str(self.pasta_downloads / nome_arquivo))

    def extrair_dados(self):
        for arquivo in self.pasta_downloads.glob("*.xml"):
            tree = ET.parse(arquivo)
            root = tree.getroot()
            ns = {'ns': root.tag.split('}')[0].strip('{')}
            nome = root.find(".//ns:xNome", ns)
            nfe = root.find(".//ns:nNF", ns)
            data = root.find(".//ns:dhEmi", ns)
            base_calculo = root.find(".//ns:ICMSTot/ns:vBC", ns)
            vNF = root.find(".//ns:ICMSTot/ns:vNF", ns)
            aliq_icms = root.find(".//ns:pICMS", ns)
            vICMS = root.find(".//ns:ICMSTot/ns:vICMS", ns)
            inf_nfe = root.find(".//{*}infNFe")
            id_nfe = inf_nfe.attrib.get("Id") if inf_nfe is not None else 'N/A'
            id_nfe_formatado = id_nfe.replace("NFe", "") if id_nfe != 'N/A' else 'N/A'
            link = f'https://cofre.sieg.com/ajax/danfe.aspx?nfe={id_nfe_formatado}'
            tag_atual = self.tags.pop(0) if self.tags else 'N/A'

            dados_extraidos = {
                "Data": datetime.strptime(data.text[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if data is not None and data.text else 'N/A',
                "Nome": nome.text if nome is not None else 'N/A',
                "Nº NF": nfe.text if nfe is not None else 'N/A',
                "Base de Cálculo": float(base_calculo.text) if base_calculo is not None and base_calculo.text else 0.0,
                "Valor da NF": float(vNF.text) if vNF is not None and vNF.text else 0.0,
                "Alíq ICMS": float(aliq_icms.text) if aliq_icms is not None and aliq_icms.text else 0.0,
                "Valor ICMS": float(vICMS.text) if vICMS is not None and vICMS.text else 0.0,
                "Tags": tag_atual,
                "Link": link,
            }

            self.dados.append(dados_extraidos)


        return self.dados

    def gerar_planilha(self):
        self.df = pd.DataFrame(self.dados)
        self.nome_arquivo = f"Nf-e {self.mes} {self.ano}.xlsx"
        self.df["Alíq ICMS"] = self.df["Alíq ICMS"].apply(lambda x: x / 100 if x > 1 else x)
        with pd.ExcelWriter(self.nome_arquivo, engine='xlsxwriter') as writer:
            self.df.to_excel(writer, index=False, sheet_name="Nt-e's")
            workbook = writer.book
            worksheet = writer.sheets["Nt-e's"]
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00', 'align': 'right'})
            formato_pct = workbook.add_format({'num_format': '0,00%', 'align': 'right'})
            for col in ["Base de Cálculo", "Valor da NF", "Valor ICMS"]:
                if col in self.df.columns:
                    i = self.df.columns.get_loc(col)
                    worksheet.set_column(i, i, 18, formato_moeda)
            if "Alíq ICMS" in self.df.columns:
                i = self.df.columns.get_loc("Alíq ICMS")
                worksheet.set_column(i, i, 12, formato_pct)
            link_idx = self.df.columns.get_loc("Link")
            formato_link = workbook.add_format({'color': 'blue', 'underline': 1})
            for row, url in enumerate(self.df["Link"], start=1):
                if isinstance(url, str) and url.startswith("http"):
                    worksheet.write_url(row, link_idx, url, formato_link, string="Ver danfe")

    def executar(self):
        try:
            self.iniciar_navegador()
            self.login()
            self.navegar_para_xml()
            self.gerar_danfe()
            self.extrair_dados()
            self.gerar_planilha()
        finally:
            self.fechar_navegador()
            if self.pasta_downloads.exists() and self.pasta_downloads.is_dir():
                shutil.rmtree(self.pasta_downloads)