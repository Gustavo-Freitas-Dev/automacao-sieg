from playwright.sync_api import sync_playwright
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import shutil
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Ct_e:
    def __init__(self, cnpj, ano, mes):
        self.cnpj = cnpj
        self.ano = ano
        self.mes = mes
        self.email = os.getenv("EMAIL")
        self.senha = os.getenv("SENHA")
        self.pasta_downloads = Path("downloads")
        self.pasta_downloads.mkdir(exist_ok=True)
        self.list_status = []

    def baixar_xmls(self):
        with sync_playwright() as p:
            navegador = p.chromium.launch(channel="chrome", headless=True)
            contexto = navegador.new_context(accept_downloads=True)
            pagina = contexto.new_page()

            pagina.goto("https://auth.sieg.com/login?ReturnUrl=https%3a%2f%2fhub.sieg.com%2fdefault.aspx")
            pagina.fill('#txtEmail', self.email)
            pagina.fill('#txtPassword', self.senha)
            pagina.click('#btnSubmit')
            pagina.wait_for_timeout(2000)

            pagina.goto("https://cofre.sieg.com/cte")
            pagina.select_option('select#MainContent_cphMainContent_ListXmlFolderCTe_ddlOrder_Xml', value='7')

            pagina.click(f"a.link-folder >> text={self.ano}")
            pagina.click(f"a.link-folder >> text={self.mes}")
            pagina.fill('#searchId', self.cnpj)
            pagina.wait_for_selector(f"text={self.cnpj}")
            pagina.click(f"text={self.cnpj}")
            pagina.wait_for_selector('tbody.table-click tr')
            linhas = pagina.query_selector_all('tbody.table-click tr')

            for idx, linha in enumerate(linhas):
                status = linha.query_selector('.hide')
                if status:
                    status_text = status.inner_text().strip()
                    self.list_status.append(status_text)
                else:
                    self.list_status.append('N/A')

                linha.click(button='right')
                with pagina.expect_download() as download_info:
                    pagina.click('text=Download CT-e')
                download = download_info.value
                nome_arquivo = f"cte_{idx + 1}.xml"
                download.save_as(str(self.pasta_downloads / nome_arquivo))

    def executar(self):
        self.baixar_xmls()
        processor = XMLProcessor(self.pasta_downloads, self.list_status)
        dados = processor.processar()
        nome_planilha = f"CT-e {self.mes}-{self.ano}.xlsx"
        GeradorPlanilha(dados, nome_planilha).gerar()
        Limpeza.remover_pasta(self.pasta_downloads)

class XMLProcessor:
    def __init__(self, pasta_downloads, list_status):
        self.pasta_downloads = pasta_downloads
        self.list_status = list_status
        self.dados = []

    def processar(self):
        for arquivo in self.pasta_downloads.glob("*.xml"):
            try:
                tree = ET.parse(arquivo)
                root = tree.getroot()
                ns = {'ns': root.tag.split('}')[0].strip('{')}
                nome = root.find(".//ns:xNome", ns)
                cte = root.find(".//ns:nCT", ns)
                data = root.find(".//ns:dhEmi", ns)
                base_calculo = root.find(".//ns:vBC", ns)
                Vnf = root.find(".//ns:vPrest/ns:vTPrest", ns)
                aliq_icms = root.find(".//ns:pICMS", ns)
                vICMS = root.find(".//ns:vICMS", ns)
                inf_cte = root.find(".//{*}infCte")
                id_cte = inf_cte.attrib.get("Id") if inf_cte is not None else 'N/A'
                id_cte_formatado = id_cte.replace("CTe", "") if id_cte != 'N/A' else 'N/A'
                status_atual = self.list_status.pop(0) if self.list_status else 'N/A'
                link = f'https://cofre.sieg.com/gerardacte?cte={id_cte_formatado}'

                self.dados.append({
                    "Data": datetime.strptime(data.text[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if data is not None and data.text else 'N/A',
                    "Nome": nome.text if nome is not None else 'N/A',
                    "Nº NF": cte.text if cte is not None else 'N/A',
                    "Base de Cálculo": float(base_calculo.text) if base_calculo is not None and base_calculo.text else 0.0,
                    "Valor da NF": float(Vnf.text) if Vnf is not None and Vnf.text else 0.0,
                    "Alíq ICMS": float(aliq_icms.text) if aliq_icms is not None and aliq_icms.text else 0.0,
                    "Valor ICMS": float(vICMS.text) if vICMS is not None and vICMS.text else 0.0,
                    "Status": status_atual,
                    "Link": link,
                })
            except ET.ParseError:
                print(f"Erro ao ler XML: {arquivo.name}")
        return self.dados

class GeradorPlanilha:
    def __init__(self, dados, nome_arquivo):
        self.df = pd.DataFrame(dados)
        self.nome_arquivo = nome_arquivo

    def gerar(self):
        self.df["Alíq ICMS"] = self.df["Alíq ICMS"].apply(lambda x: x / 100 if x > 1 else x)
        with pd.ExcelWriter(self.nome_arquivo, engine='xlsxwriter') as writer:
            self.df.to_excel(writer, index=False, sheet_name='CTEs')
            workbook = writer.book
            worksheet = writer.sheets['CTEs']
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00', 'align': 'right'})
            formato_pct = workbook.add_format({'num_format': '0,00%', 'align': 'right'})
            for col in ["Base de Cálculo", "Valor da NF","Valor ICMS"]:
                if col in self.df.columns:
                    i = self.df.columns.get_loc(col)
                    worksheet.set_column(i, i, 18, formato_moeda)
            if "Alíq ICMS" in self.df.columns:
                i = self.df.columns.get_loc("Alíq ICMS")
                worksheet.set_column(i, i, 12, formato_pct)
            link_idx = self.df.columns.get_loc("Link")
            for row, url in enumerate(self.df["Link"], start=1):
                worksheet.write_url(row, link_idx, url, string="CTE")

class Limpeza:
    @staticmethod
    def remover_pasta(pasta):
        shutil.rmtree(pasta)
