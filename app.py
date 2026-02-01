import sys
sys.path.append("utils")
import streamlit as st
import utils as uts
import pandas as pd

try:
    # Configuración de página
    st.set_page_config(
        page_title="AutoCAD TrussMiner", 
        page_icon=r"https://raw.githubusercontent.com/AssiaFB/Imgenes-de-AssiaFB/refs/heads/main/Ping%C3%BCino%20nocturno%20trabajando%20en%20laptop.png", 
        layout="wide"
    )

    # Cargar el CSS desde la carpeta style
    uts.load_css(uts.obtener_ruta_recurso("style/style.min.css"))

    # TITULO
    st.markdown("""
    <div class="assiafb-title">AutoCAD TrussMiner</div>
    """, unsafe_allow_html=True)

    # Descripción
    st.markdown("""
    <div class="assiafb-section">
    <p>
        Esta herramienta lee la geometría de líneas y capas desde el archivo de AutoCAD activo. 
        Convierte el dibujo en un modelo de datos (nodos y barras) para visualizar la estructura 
        en 3D y generar automáticamente las matrices de cálculo, evitando la entrada manual de coordenadas.
    </p>
    </div>
    """, unsafe_allow_html=True)

    # TARGET Autor
    uts.target_autor()

    # Verificar conexión con AutoCAD
    resultado_seccion_actual, estado_seccion_actual = uts.verificar_session_autocad()

    # Titulo de session actual
    st.markdown(f"<div class='section-title'>{'Sessión actual'.upper()}:</div>", unsafe_allow_html=True)

    # Descripción de session actual
    st.markdown(f"""
    <div class="assiafb-body-center">
    <p>
        {resultado_seccion_actual}
    </p>
    </div>
    """, unsafe_allow_html=True)

    # Verificar estado
    if estado_seccion_actual:
        # Variable temporal
        defaults_var_temp = {
            'seccion': None,
            'estado': False,
            'lista_barras': [],
            'mapa_nodos': [],
            'fuerzas_nodos': pd.DataFrame(columns=["Nodo", "(Fx, Fy, Fz)"]),
            'nodos_restricciones': pd.DataFrame(columns=["Nodo", "(Rx, Ry, Rz)"]),
            'pase_de_introduccion': False,
            'pase_de_eliminación': False,
            'seleccion_actual_id': [],
            'nodo_GDL_barras_act': [],
            'nodo_GDL_despl_barras': [],
            'matriz_rigidez': [],
            'def_un_esf_normal': [],
            'nodo_unico': None,
            'matriz_rigidez_global': [],
            'escala_deformada': 1,
            'fuerzas_globales': [],
            'condicion_globales': False
        }

        for key, value in defaults_var_temp.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Titulo de acciones
        st.markdown(f"<div class='section-title'>{'Acciones'.upper()}:</div>", unsafe_allow_html=True)

        # Botones de uso
        col1, col2, col3 = st.columns(3)

        with col1:
            # Botón 1: Cargar Datos
            if st.button("📂 Cargar Datos del CAD Activo", key="btn_cargar", use_container_width=True):
                st.session_state['estado'], st.session_state['seccion'], st.session_state['lista_barras'] = uts.funcion_cargar_datos()

        with col2:
            # Botón 2: Calcular
            if st.button("🧮 Calcular Armadura", key="btn_calc", use_container_width=True):
                st.session_state['estado'], st.session_state['seccion'], st.session_state['nodo_GDL_barras_act'], st.session_state['nodo_GDL_despl_barras'], st.session_state['matriz_rigidez'], st.session_state['def_un_esf_normal'], st.session_state['matriz_rigidez_global'], st.session_state['fuerzas_globales'] = uts.funcion_calcular(st.session_state['lista_barras'], st.session_state['mapa_nodos'], st.session_state['fuerzas_nodos'], st.session_state['nodos_restricciones'])
        
        with col3:
            # Botón 3: gloables
            if st.button("🧮 Matriz y fuerza globales".upper(), key="btn_gloables", use_container_width=True):
                st.session_state['condicion_globales'] = True
            else:
                st.session_state['condicion_globales'] = False

        if st.session_state['seccion'] != None and st.session_state['estado'] and st.session_state['condicion_globales']==False:
            # Titulo de acciones
            st.markdown(f"<div class='section-title'>{f'{st.session_state['seccion']}'.upper()}:</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3,1,3])

            with col2:
                # Botón 1: Selección manual
                if st.button("Selección manual", key="btn_seleccion", use_container_width=True):
                    st.session_state['seleccion_actual_id'] = uts.seleccion_actual_id()
                
            if st.session_state['seleccion_actual_id']:
                st.markdown(f"""
                <div class="assiafb-alert">
                <p><strong>✅ Exito:</strong> Se seleccionaron {len(st.session_state['seleccion_actual_id'])} barras</p>
                </div>
                """, unsafe_allow_html=True)
            
            if st.session_state['seccion'] == "Datos extraidos":
                lista_barra_df = pd.DataFrame(st.session_state['lista_barras'])
                n_nodos, st.session_state['lista_barras'], st.session_state['mapa_nodos'] = uts.contructor_nodos(lista_barra_df)

                
                html_tabla_nodos = st.session_state['mapa_nodos'].T.rename(columns={
                                            0: "X",
                                            1: "Y",
                                            2: "Z"
                                        }).to_html(classes='tabla-ingenieria', index=True, border=0)

                st.markdown(f"""
                <div class="assiafb-alert">
                <p><strong>✅ Exito:</strong> Se encontraron {n_nodos} nodos y {len(st.session_state['lista_barras'])} barras</p>
                </div>
                """, unsafe_allow_html=True)

                if not st.session_state['lista_barras'].empty:
                    styler = st.session_state['lista_barras'].style.apply(uts.estio_red_seleccion, axis=1)

                    html_tabla_barras = styler.to_html(classes='tabla-ingenieria', index=True, border=0)
                else:
                    html_tabla_barras = "<p>No hay datos</p>"

                with st.expander("Nodos", expanded=False):
                    st.markdown(f"<div class='contenedor-tabla'>{html_tabla_nodos}</div>", unsafe_allow_html=True)

                with st.expander("Barras", expanded=False):
                    st.markdown(f"<div class='contenedor-tabla'>{html_tabla_barras}</div>", unsafe_allow_html=True)

                c_izq, c_der = st.columns(2, vertical_alignment="center")

            
                with c_izq:
                    res_fur = st.selectbox("Deseas aplicar", ["Restricciones", "Fuerzas"])

                with c_der:
                    metodo_seleccion_id_comun = st.selectbox("Método de selección del grupo de barras", ["Todos los nudos", "El nudo en común", "Nodo unico"])
                
                if metodo_seleccion_id_comun == "Nodo unico":
                    c_izq, c_central ,c_der = st.columns([3,1,3], vertical_alignment="center")
                    with c_central:
                        st.session_state['nodo_unico'] = st.selectbox("Nodo unico", st.session_state['mapa_nodos'].columns.tolist())
                
                if res_fur == "Fuerzas":
                    c_izq, c_central ,c_der = st.columns(3, vertical_alignment="center")
            
                    with c_izq:
                        x_force = st.number_input("Fuerza en X", step=0.001, value=0.00, format='%.4f')
                    with c_central:
                        y_force = st.number_input("Fuerza en Y", step=0.001, value=0.00, format='%.4f')
                    with c_der:
                        z_force = st.number_input("Fuerza en Z", step=0.001, value=0.00, format='%.4f')

                    fuerza_actual_new = (x_force, y_force, z_force)
                    
                else:
                    c_izq, c_central ,c_der = st.columns(3, vertical_alignment="center")
            
                    with c_central:
                        nodo_gdl_res = st.multiselect(res_fur, options=["x","y","z"], default=["x","y","z"])

                
                col1, col2, col3, col4 = st.columns([2,1,1,2])

                with col2:
                    # Botón 1: Introducir
                    if st.button("Introducir", key="Introducir_restricciones_o_fuerza", use_container_width=True):
                        st.session_state['pase_de_introduccion'] = True
                    else:
                        st.session_state['pase_de_introduccion'] = False
                with col3:
                    # Botón 2: Eliminar
                    if st.button("Eliminar", key="Eliminar_restricciones_o_fuerza", use_container_width=True):
                        st.session_state['pase_de_eliminación'] = True
                    else:
                        st.session_state['pase_de_eliminación'] = False
                
                if st.session_state['pase_de_introduccion']:
                    nodos_respectivo = uts.seleccionar_nudo_comun(metodo_seleccion_id_comun, st.session_state['seleccion_actual_id'], st.session_state['lista_barras'])

                    if len(nodos_respectivo) > 0:
                        if res_fur == "Restricciones":
                            restriccion_list_temp = [False, False, False]
                            for eje in nodo_gdl_res:
                                if eje == "x":
                                    restriccion_list_temp[0] = True
                                if eje == "y":
                                    restriccion_list_temp[1] = True
                                if eje == "z":
                                    restriccion_list_temp[2] = True
                            temp_restriccion_tupla = tuple(restriccion_list_temp)
                            for nodo in nodos_respectivo:
                                st.session_state['nodos_restricciones'] = pd.concat([st.session_state['nodos_restricciones'], pd.DataFrame([{'Nodo': nodo, '(Rx, Ry, Rz)': temp_restriccion_tupla}])], ignore_index=True)
                            st.session_state['nodos_restricciones'] = st.session_state['nodos_restricciones'].drop_duplicates(subset=['Nodo'], keep='last').reset_index(drop=True)
                        elif res_fur == "Fuerzas":
                            for nodo in nodos_respectivo:
                                st.session_state['fuerzas_nodos'] = pd.concat([st.session_state['fuerzas_nodos'], pd.DataFrame([{'Nodo': nodo, '(Fx, Fy, Fz)': fuerza_actual_new}])], ignore_index=True)
                            st.session_state['fuerzas_nodos'] = st.session_state['fuerzas_nodos'].drop_duplicates(subset=['Nodo'], keep='last').reset_index(drop=True)

                elif st.session_state['pase_de_eliminación']:
                    nodos_respectivo = uts.seleccionar_nudo_comun(metodo_seleccion_id_comun, st.session_state['seleccion_actual_id'], st.session_state['lista_barras'])
                    if len(nodos_respectivo) > 0:
                        if res_fur == "Restricciones":
                            for nodo in nodos_respectivo:
                                st.session_state['nodos_restricciones'] = st.session_state['nodos_restricciones'][st.session_state['nodos_restricciones']["Nodo"] != nodo]
                        elif res_fur == "Fuerzas":
                            for nodo in nodos_respectivo:
                                st.session_state['fuerzas_nodos'] = st.session_state['fuerzas_nodos'][st.session_state['fuerzas_nodos']["Nodo"] != nodo]

                if not st.session_state['nodos_restricciones'].empty:
                    html_tabla_nodos_restringidos = st.session_state['nodos_restricciones'].to_html(classes='tabla-ingenieria', index=False, border=0)
                else:
                    html_tabla_nodos_restringidos = "<p>No hay datos</p>"

                if not st.session_state['fuerzas_nodos'].empty:
                    html_tabla_nodos_fuerzas = st.session_state['fuerzas_nodos'].to_html(classes='tabla-ingenieria', index=False, border=0)
                else:
                    html_tabla_nodos_fuerzas = "<p>No hay datos</p>"

                with st.expander("Restricciones", expanded=False):
                    st.markdown(f"<div class='contenedor-tabla'>{html_tabla_nodos_restringidos}</div>", unsafe_allow_html=True)
                with st.expander("Fuerzas", expanded=False):
                    st.markdown(f"<div class='contenedor-tabla'>{html_tabla_nodos_fuerzas}</div>", unsafe_allow_html=True) 

                st.markdown(f"<div class='section-title'>{'Vista de la armadura'.upper()}:</div>", unsafe_allow_html=True)     

                uts.ploter_def(st.session_state['lista_barras'], st.session_state['mapa_nodos']) 

            if st.session_state['seccion'] == "Vista de deformada":
                col1, col2, col3 = st.columns(3)
                with col2:
                    st.session_state['escala_deformada'] = st.number_input("Escala de deformada", min_value=0.01, step=0.01, value=1.00, format='%.2f')
                uts.ploter_def_deformada(st.session_state['lista_barras'], st.session_state['nodo_GDL_despl_barras'], st.session_state['matriz_rigidez'], st.session_state['def_un_esf_normal'], st.session_state['escala_deformada'], st.session_state['nodo_GDL_barras_act']) 
            
        if st.session_state['condicion_globales']:
            uts.print_globales()
except Exception as e:
    st.error(f"Error: {e}")
    
    # Forzar la recarga
    st.rerun()