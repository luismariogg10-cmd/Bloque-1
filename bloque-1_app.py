import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="ASFIES - Calculadora de Eficiencia",
    page_icon="📊",
    layout="wide"
)

# --- TÍTULO Y ENCABEZADO ---
st.title("📊 ASFIES CONSULTING")
st.subheader("Reporte de Diagnóstico Financiero y Logístico (Bloque 1)")
st.caption("📍 Ojo de Agua, Tecámac, Estado de México | Corredor: AIFA–Tecámac")

# --- ORGANIZACIÓN EN PESTAÑAS ---
tab_inputs, tab_reporte = st.tabs(["⚙️ Parámetros de Entrada (Inputs)", "📄 Reporte de Diagnóstico (Outputs)"])

with tab_inputs:
    st.markdown("### Parámetros Comerciales y de Flete")
    col1, col2, col3 = st.columns(3)
    with col1:
        tarifa_base = st.number_input("Tarifa base por flete/km ($)", value=38.50, step=1.0)
    with col2:
        km_cargados = st.number_input("Kilómetros cargados recorridos", value=10000.0, step=500.0)
    with col3:
        gf = st.number_input("Gastos fijos de estructura (GF)", value=105000.0, step=5000.0)

    st.markdown("### Fricción Comercial y Descuentos")
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        d_descuentos = st.number_input("Descuentos (D)", value=8000.0, step=1000.0)
    with col5:
        b_bonos = st.number_input("Bonificaciones (B)", value=5000.0, step=1000.0)
    with col6:
        r_ajustes = st.number_input("Devoluciones (R)", value=4000.0, step=1000.0)
    with col7:
        c_bf = st.number_input("Comisiones Broker/Factoraje", value=15400.0, step=1000.0)

    st.markdown("### Costos Operativos y Nómina (CDO)")
    col8, col9, col10, col11 = st.columns(4)
    with col8:
        c_dl = st.number_input("Diésel y Lubricantes (C_DL)", value=112000.0, step=5000.0)
    with col9:
        c_pc = st.number_input("Peajes en casetas (C_PC)", value=32000.0, step=1000.0)
    with col10:
        s_b = st.number_input("Sueldo base operador (S_B)", value=18000.0, step=1000.0)
    with col11:
        c_km_viaticos = st.number_input("Comisiones por km + Viáticos", value=38000.0, step=1000.0, help="Suma de C_KM (22k) + V (16k)")

    st.markdown("### Tiempos, Demoras y Penalizaciones (SLA)")
    col12, col13, col14, col15 = st.columns(4)
    with col12:
        t_e = st.number_input("Tiempo efectivo estancia (T_E)", value=18.0, step=1.0)
        t_l = st.number_input("Tiempo libre contractual (T_L)", value=10.0, step=1.0)
    with col13:
        c_h = st.number_input("Costo inmovilización (C_H)", value=650.0, step=50.0)
    with col14:
        d_exceso = st.number_input("Días exceso retención (D_Exceso)", value=2.0, step=1.0)
        t_demurrage = st.number_input("Tarifa sobreestadía (T_Demurrage)", value=1800.0, step=100.0)
    with col15:
        c_otif = st.number_input("Multas OTIF (C_OTIF)", value=4500.0, step=500.0)

    st.markdown("### Activos Fijos (Opcional para flujo de caja)")
    col16, col17 = st.columns(2)
    with col16:
        ca_flota = st.number_input("Costo de Flota y Equipo", value=3780000.0, help="Suma de Flota + Telemática")
    with col17:
        vr = st.number_input("Valor de salvamento (VR)", value=720000.0)


# --- MOTOR DE CÁLCULO FINANCIERO (Pestaña Workings) ---
# Ingresos y Fricción
ibf = tarifa_base * km_cargados
friccion_total = d_descuentos + b_bonos + r_ajustes + c_bf
inf = ibf - friccion_total

# OPEX y CDO
n_d = s_b + c_km_viaticos
cdo = c_dl + c_pc + n_d
opex = cdo + gf
or_ratio = (opex / inf) if inf > 0 else 0

# Fugas, Tiempos y SLA
cd_tiempo = max(0, t_e - t_l) * c_h
pc_sla = (d_exceso * t_demurrage) + c_otif
fugas_demoras_sla = cd_tiempo + pc_sla

# Indicadores de proporción
incidencia_nomina = (n_d / inf) if inf > 0 else 0
friccion_comercial = (friccion_total / ibf) if ibf > 0 else 0

# --- LÓGICA DE SEMÁFOROS ---
def evaluar_indicador(valor, tipo):
    if tipo == "OR":
        if valor <= 0.85: return "🟢", "Operación solvente y rentable."
        elif valor <= 0.92: return "🟡", "Operación solvente. Margen ajustado."
        else: return "🔴", "Alerta de rentabilidad. OPEX alto."
    elif tipo == "Detencion":
        if valor < 3000: return "🟢", "Tiempos de carga/descarga óptimos."
        elif valor <= 8000: return "🟡", "Alerta por tiempos en aduanas/andenes."
        else: return "🔴", "Fuga crítica por equipo detenido."
    elif tipo == "SLA":
        if valor < 2500: return "🟢", "Cumplimiento dentro de parámetros."
        elif valor <= 6000: return "🟡", "Fricción con clientes. Revisar SLAs."
        else: return "🔴", "Fuga crítica. Auditar citas en Cedis."
    elif tipo == "Nomina":
        if valor < 0.14: return "🟡", "Riesgo. Posible rotación."
        elif valor <= 0.20: return "🟢", "Compensación alineada al sector."
        else: return "🔴", "Costo operativo de nómina excedido."
    elif tipo == "Friccion":
        if valor < 0.05: return "🟢", "Relación comercial sana."
        elif valor <= 0.10: return "🟡", "Fricción de corretaje/notas de crédito."
        else: return "🔴", "Altos descuentos. Revisar cuentas."


# --- GENERACIÓN DEL REPORTE (Pestaña Outputs) ---
with tab_reporte:
    st.markdown("---")
    
    # KPIs Principales
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ingresos Netos (INF)", f"${inf:,.2f} MXN")
    kpi2.metric("Costo Directo (CDO)", f"${cdo:,.2f} MXN")
    kpi3.metric("Operating Ratio (OR)", f"{or_ratio * 100:.1f} %", delta=f"{(0.85 - or_ratio)*100:.1f}% vs Meta", delta_color="inverse")
    kpi4.metric("Fugas Totales (SLA + Demoras)", f"${fugas_demoras_sla:,.2f} MXN", delta="Impacto a Margen", delta_color="off")

    st.markdown("---")
    st.markdown("### Matriz de Semáforo de Control Operativo")
    
    # Construcción de la tabla de semáforo
    datos_semaforo = [
        ("Operating Ratio", f"{or_ratio * 100:.1f}%", "<85% | 85-92% | >92%", *evaluar_indicador(or_ratio, "OR")),
        ("Detención en Ruta", f"${cd_tiempo:,.2f}", "<$3k | $3k-$8k | >$8k", *evaluar_indicador(cd_tiempo, "Detencion")),
        ("Multas SLA (PC_SLA)", f"${pc_sla:,.2f}", "<$2.5k | $2.5k-$6k | >$6k", *evaluar_indicador(pc_sla, "SLA")),
        ("Incidencia de Nómina", f"{incidencia_nomina * 100:.1f}%", "14-20% | 20-25% | >25%", *evaluar_indicador(incidencia_nomina, "Nomina")),
        ("Fricción Comercial", f"{friccion_comercial * 100:.1f}%", "<5% | 5-10% | >10%", *evaluar_indicador(friccion_comercial, "Friccion")),
    ]
    
    df_semaforo = pd.DataFrame(datos_semaforo, columns=["Indicador Operativo", "Valor Actual", "Límites (V/A/R)", "Semáforo", "Diagnóstico"])
    st.dataframe(df_semaforo, use_container_width=True, hide_index=True)

    st.markdown("---")
    col_cdo, col_fugas = st.columns(2)
    
    with col_cdo:
        st.markdown("#### Estructura CDO")
        df_cdo = pd.DataFrame({
            "Rubro": ["Diésel y Lubricantes", "Peajes", "Nómina Operador"],
            "Monto": [f"${c_dl:,.2f}", f"${c_pc:,.2f}", f"${n_d:,.2f}"]
        })
        st.dataframe(df_cdo, use_container_width=True, hide_index=True)
        
    with col_fugas:
        st.markdown("#### Desglose de Fugas Comerciales")
        df_fugas = pd.DataFrame({
            "Concepto": ["Brokerage / Factoraje", "Descuentos", "Devoluciones", "Bonificaciones"],
            "Impacto": [f"${c_bf:,.2f}", f"${d_descuentos:,.2f}", f"${r_ajustes:,.2f}", f"${b_bonos:,.2f}"]
        })
        st.dataframe(df_fugas, use_container_width=True, hide_index=True)