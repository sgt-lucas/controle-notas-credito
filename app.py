import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
from data_service import DataService
import logging

# Configuração do Logging
logging.basicConfig(filename="erros.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuração da Página
st.set_page_config(page_title="Controle de Notas de Crédito", layout="wide")
st.title("Controle de Notas de Crédito")

# Inicialização do DataService
try:
    data_service = DataService()
except Exception as e:
    st.error(f"Erro ao inicializar a aplicação: {e}")
    st.stop()

# Funções de Validação
def validar_data(data_str):
    """Valida se uma string está no formato DD/MM/AAAA."""
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def validar_numerico(valor):
    """Valida se o valor é numérico."""
    try:
        return float(valor.replace(',', '.')) if valor else None
    except ValueError:
        return None

def validar_ptres(ptres):
    """Valida PTRES: exatamente 6 dígitos."""
    return ptres.isdigit() and len(ptres) == 6

def validar_fonte(fonte):
    """Valida Fonte: exatamente 10 dígitos."""
    return fonte.isdigit() and len(fonte) == 10

def validar_nota_numero(numero):
    """Valida Número da Nota: NC + 6 dígitos."""
    return bool(re.match(r"^NC\d{6}$", numero))

# Barra Lateral de Navegação
menu = [
    "🏠 Início",
    "📋 Adicionar Plano Interno",
    "📋 Adicionar Natureza da Despesa",
    "📋 Adicionar Seção Requisitante",
    "➕ Adicionar Nota",
    "📉 Registrar Empenho",
    "🗑️ Deletar Nota",
    "🗑️ Deletar Empenho",
    "📊 Visualizar Relatório",
    "📊 Empenhos por Seção",
    "📑 Relatório Excel",
    "📄 Relatório PDF",
    "🌐 Consultar SIAFI"
]
opcao = st.sidebar.selectbox("Menu", menu)

# Estilo Personalizado
st.markdown("""
    <style>
    .stButton > button {
        background-color: #1E90FF;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #104E8B;
    }
    .stTextInput > div > input {
        background-color: #FFFFFF;
        color: black;
    }
    .stSelectbox > div > select {
        background-color: #FFFFFF;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# Funções da Interface
if opcao == "🏠 Início":
    st.header("Bem-vindo ao Controle de Notas de Crédito")
    st.write("Use o menu lateral para gerenciar notas de crédito, empenhos e relatórios.")

elif opcao == "📋 Adicionar Plano Interno":
    st.header("Adicionar Plano Interno")
    with st.form("form_plano_interno"):
        codigo = st.text_input("Código (ex: PI001)")
        submit = st.form_submit_button("Salvar")
        if submit:
            try:
                if not codigo:
                    st.error("O campo código não pode estar vazio.")
                else:
                    data_service.save_plano_interno({"codigo": codigo.upper()})
                    st.success(f"Plano Interno {codigo} adicionado com sucesso!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

elif opcao == "📋 Adicionar Natureza da Despesa":
    st.header("Adicionar Natureza da Despesa")
    planos = data_service.load_planos_internos()
    if not planos:
        st.warning("Nenhum plano interno cadastrado. Cadastre um plano interno primeiro.")
    else:
        with st.form("form_natureza_despesa"):
            plano_codigo = st.selectbox("Plano Interno", [p["codigo"] for p in planos])
            codigo = st.text_input("Código (ex: 3.3.90.39)")
            submit = st.form_submit_button("Salvar")
            if submit:
                try:
                    if not codigo:
                        st.error("O campo código não pode estar vazio.")
                    else:
                        data_service.save_natureza_despesa({
                            "codigo": codigo,
                            "plano_interno_codigo": plano_codigo
                        })
                        st.success(f"Natureza da Despesa {codigo} adicionada com sucesso!")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

elif opcao == "📋 Adicionar Seção Requisitante":
    st.header("Adicionar Seção Requisitante")
    with st.form("form_secao_requisitante"):
        codigo = st.text_input("Código (ex: SR001)")
        submit = st.form_submit_button("Salvar")
        if submit:
            try:
                if not codigo:
                    st.error("O campo código não pode estar vazio.")
                else:
                    data_service.save_secao_requisitante({"codigo": codigo.upper()})
                    st.success(f"Seção Requisitante {codigo} adicionada com sucesso!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

elif opcao == "➕ Adicionar Nota":
    st.header("Adicionar Nota de Crédito")
    planos = data_service.load_planos_internos()
    naturezas = data_service.load_naturezas_despesa()
    if not planos or not naturezas:
        st.warning("Cadastre pelo menos um Plano Interno e uma Natureza da Despesa antes de adicionar uma nota.")
    else:
        with st.form("form_nota"):
            plano_codigo = st.selectbox("Plano Interno", [p["codigo"] for p in planos])
            naturezas_filtradas = [n["codigo"] for n in data_service.load_naturezas_despesa(plano_codigo)]
            natureza_codigo = st.selectbox("Natureza da Despesa", naturezas_filtradas)
            ptres_codigo = st.text_input("PTRES Código (6 dígitos)")
            fonte_codigo = st.text_input("Fonte Código (10 dígitos)")
            numero = st.text_input("Número da Nota (NC + 6 dígitos, ex: NC123456)")
            valor = st.text_input("Valor (ex: 1000.50)")
            descricao = st.text_input("Descrição")
            observacao = st.text_input("Observação (opcional)")
            prazo = st.text_input("Prazo Limite (DD/MM/AAAA)")
            submit = st.form_submit_button("Salvar")
            if submit:
                try:
                    if not all([plano_codigo, natureza_codigo, ptres_codigo, fonte_codigo, numero, valor, descricao, prazo]):
                        st.error("Preencha todos os campos obrigatórios.")
                    elif not validar_ptres(ptres_codigo):
                        st.error("O PTRES Código deve ter exatamente 6 dígitos.")
                    elif not validar_fonte(fonte_codigo):
                        st.error("O Fonte Código deve ter exatamente 10 dígitos.")
                    elif not validar_nota_numero(numero):
                        st.error("O Número da Nota deve ser NC seguido de 6 dígitos (ex: NC123456).")
                    elif not validar_data(prazo):
                        st.error("Prazo inválido! Use o formato DD/MM/AAAA (ex: 01/08/2025).")
                    else:
                        valor_float = validar_numerico(valor)
                        if valor_float is None or valor_float <= 0:
                            st.error("O valor deve ser um número positivo.")
                        else:
                            nota = {
                                "numero": numero.upper(),
                                "valor": valor_float,
                                "valor_restante": valor_float,
                                "descricao": descricao or "Sem descrição",
                                "observacao": observacao or "Sem observação",
                                "prazo": prazo,
                                "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "natureza_despesa_codigo": natureza_codigo,
                                "plano_interno_codigo": plano_codigo,
                                "ptres_codigo": ptres_codigo,
                                "fonte_codigo": fonte_codigo
                            }
                            data_service.save_nota(nota)
                            st.success(f"Nota {numero} adicionada com sucesso!")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

elif opcao == "📉 Registrar Empenho":
    st.header("Registrar Empenho")
    notas = data_service.load_notas()
    secoes = data_service.load_secoes_requisitantes()
    if not notas:
        st.warning("Nenhuma nota de crédito cadastrada para registrar um empenho.")
    elif not secoes:
        st.warning("Nenhuma seção requisitante cadastrada. Cadastre uma seção antes de registrar um empenho.")
    else:
        with st.form("form_empenho"):
            nota_opcoes = [f'{n["numero"]} (Saldo: R${n["valor_restante"]:.2f})' for n in notas]
            nota_selecionada = st.selectbox("Nota de Crédito", nota_opcoes)
            secao_codigo = st.selectbox("Seção Requisitante", [s["codigo"] for s in secoes])
            valor = st.text_input("Valor do Empenho")
            descricao = st.text_input("Descrição")
            submit = st.form_submit_button("Salvar")
            if submit:
                try:
                    numero_nota = nota_selecionada.split(" ")[0]
                    nota = next((n for n in notas if n["numero"] == numero_nota), None)
                    valor_float = validar_numerico(valor)
                    if not all([numero_nota, secao_codigo, valor, descricao]):
                        st.error("Preencha todos os campos.")
                    elif valor_float is None or valor_float <= 0:
                        st.error("O valor do empenho deve ser positivo.")
                    elif valor_float > nota["valor_restante"]:
                        st.error(f"Valor do empenho excede o saldo restante (R${nota['valor_restante']:.2f}).")
                    else:
                        nota["valor_restante"] -= valor_float
                        empenho = {
                            "numero_nota": numero_nota,
                            "valor": valor_float,
                            "descricao": descricao or "Empenho sem descrição",
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "secao_requisitante_codigo": secao_codigo
                        }
                        data_service.save_empenho(empenho, nota)
                        st.success(f"Empenho de R${valor_float:.2f} registrado na nota {numero_nota}.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

elif opcao == "🗑️ Deletar Nota":
    st.header("Deletar Nota de Crédito")
    notas = data_service.load_notas()
    if not notas:
        st.warning("Nenhuma nota de crédito cadastrada para deletar.")
    else:
        with st.form("form_deletar_nota"):
            nota_opcoes = [f'{n["numero"]} (Saldo: R${n["valor_restante"]:.2f})' for n in notas]
            nota_selecionada = st.selectbox("Nota de Crédito", nota_opcoes)
            submit = st.form_submit_button("Deletar")
            if submit:
                try:
                    numero_nota = nota_selecionada.split(" ")[0]
                    if st.checkbox("Confirmar exclusão (todos os empenhos associados serão excluídos)"):
                        data_service.delete_nota(numero_nota)
                        st.success(f"Nota {numero_nota} deletada com sucesso!")
                    else:
                        st.warning("Marque a caixa de confirmação para deletar.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

elif opcao == "🗑️ Deletar Empenho":
    st.header("Deletar Empenho")
    empenhos = data_service.load_empenhos()
    if not empenhos:
        st.warning("Nenhum empenho cadastrado para deletar.")
    else:
        with st.form("form_deletar_empenho"):
            empenho_opcoes = [f'ID {e["id"]} - Nota {e["numero_nota"]} (Valor: R${e["valor"]:.2f}, Data: {e["data"]}, Seção: {e["secao_requisitante_codigo"]})' for e in empenhos]
            empenho_selecionado = st.selectbox("Empenho", empenho_opcoes)
            submit = st.form_submit_button("Deletar")
            if submit:
                try:
                    empenho_id = int(empenho_selecionado.split(" ")[1])
                    if st.checkbox("Confirmar exclusão"):
                        data_service.delete_empenho(empenho_id)
                        st.success(f"Empenho ID {empenho_id} deletado com sucesso!")
                    else:
                        st.warning("Marque a caixa de confirmação para deletar.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

elif opcao == "📊 Visualizar Relatório":
    st.header("Relatório Detalhado")
    notas = data_service.load_notas()
    empenhos = data_service.load_empenhos()
    naturezas = data_service.load_naturezas_despesa()
    planos = data_service.load_planos_internos()
    secoes = data_service.load_secoes_requisitantes()

    data = []
    for nota in notas:
        natureza = next((n for n in naturezas if n["codigo"] == nota["natureza_despesa_codigo"]), {"codigo": "N/A", "plano_interno_codigo": None})
        plano = next((p for p in planos if p["codigo"] == natureza["plano_interno_codigo"]), {"codigo": "N/A"}) if natureza["plano_interno_codigo"] else {"codigo": "N/A"}
        related_empenhos = [e for e in empenhos if e["numero_nota"] == nota["numero"]]
        if not related_empenhos:
            data.append({
                "Plano Interno": plano["codigo"],
                "Natureza da Despesa": natureza["codigo"],
                "PTRES": nota["ptres_codigo"],
                "Fonte": nota["fonte_codigo"],
                "Nº Nota": nota["numero"],
                "V. Original": f"R${nota['valor']:.2f}",
                "V. Restante": f"R${nota['valor_restante']:.2f}",
                "Data Empenho": "Nenhum",
                "V. Empenho": "",
                "Descrição Empenho": nota["descricao"],
                "Seção Requisitante": "N/A"
            })
        else:
            for empenho in related_empenhos:
                secao = next((s for s in secoes if s["codigo"] == empenho["secao_requisitante_codigo"]), {"codigo": "N/A"}) if empenho["secao_requisitante_codigo"] else {"codigo": "N/A"}
                data.append({
                    "Plano Interno": plano["codigo"],
                    "Natureza da Despesa": natureza["codigo"],
                    "PTRES": nota["ptres_codigo"],
                    "Fonte": nota["fonte_codigo"],
                    "Nº Nota": nota["numero"],
                    "V. Original": f"R${nota['valor']:.2f}",
                    "V. Restante": f"R${nota['valor_restante']:.2f}",
                    "Data Empenho": empenho["data"],
                    "V. Empenho": f"R${empenho['valor']:.2f}",
                    "Descrição Empenho": empenho["descricao"],
                    "Seção Requisitante": secao["codigo"]
                })

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir.")

elif opcao == "📊 Empenhos por Seção":
    st.header("Empenhos por Seção Requisitante")
    secoes = data_service.load_secoes_requisitantes()
    if not secoes:
        st.warning("Nenhuma seção requisitante cadastrada.")
    else:
        secao_codigo = st.selectbox("Seção Requisitante", [s["codigo"] for s in secoes])
        if secao_codigo:
            empenhos = data_service.load_empenhos()
            data = [
                {
                    "Nº Nota": e["numero_nota"],
                    "Valor Empenho": f"R${e['valor']:.2f}",
                    "Data Empenho": e["data"],
                    "Descrição Empenho": e["descricao"]
                }
                for e in empenhos if e["secao_requisitante_codigo"] == secao_codigo
            ]
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhum empenho encontrado para esta seção.")

elif opcao == "📑 Relatório Excel":
    st.header("Gerar Relatório Excel")
    if st.button("Gerar Relatório"):
        try:
            filename = data_service.generate_excel_report()
            with open(filename, "rb") as f:
                st.download_button(
                    label="Baixar Relatório Excel",
                    data=f,
                    file_name="relatorio_notas_credito.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            st.success("Relatório Excel gerado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")

elif opcao == "📄 Relatório PDF":
    st.header("Gerar Relatório PDF")
    if st.button("Gerar Relatório"):
        try:
            filename = data_service.generate_pdf_report()
            with open(filename, "rb") as f:
                st.download_button(
                    label="Baixar Relatório PDF",
                    data=f,
                    file_name="relatorio_notas_credito.pdf",
                    mime="application/pdf"
                )
            st.success("Relatório PDF gerado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")

elif opcao == "🌐 Consultar SIAFI":
    st.header("Consultar SIAFI (Fictício)")
    with st.form("form_siafi"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Consultar")
        if submit:
            try:
                result = data_service.consultar_siafi(usuario, senha)
                st.success(f"Resposta do SIAFI: {result['message']}")
            except Exception as e:
                st.error(f"Erro na consulta: {e}")