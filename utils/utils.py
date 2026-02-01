import win32com.client  
import streamlit as st
import re
import pythoncom
import random
import pandas as pd
import os
import sys
import math
import numpy as np
import plotly.graph_objects as go


def verificar_session_autocad():
    try:
        autocad = win32com.client.Dispatch("AutoCAD.Application")
        
        # Obtenemos el documento actual en pantalla
        doc = autocad.ActiveDocument

        estado = True

        # Confirmación
        return doc.Name, estado

    except Exception as e:
        estado = False
        return "❌ Error: No se pudo conectar a AutoCAD. Asegúrate de que AutoCAD esté abierto.", estado

def extraer_propiedades(descripcion):
    if not descripcion:
        return 0.0, 0.0

    patron_numero = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"

    regex_E = fr"E\s*[=:]\s*({patron_numero})"
    regex_A = fr"A\s*[=:]\s*({patron_numero})"

    match_E = re.search(regex_E, descripcion, re.IGNORECASE)
    match_A = re.search(regex_A, descripcion, re.IGNORECASE)

    try:
        valor_E = float(match_E.group(1)) if match_E else 0.0
        valor_A = float(match_A.group(1)) if match_A else 0.0
    except ValueError:
        return 0.0, 0.0

    return valor_E, valor_A

def seleccion_actual_id():
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
        doc = acad.ActiveDocument

        try:
            acad.Visible = True
            acad.WindowState = 2
        except:
            pass

        nombre_ss = f"Seleccion_Manual_{random.randint(100,999)}"

        try:
            ss = doc.SelectionSets.Add(nombre_ss)
        except:
            # Si existe, lo limpiamos y usamos
            ss = doc.SelectionSets.Item(nombre_ss)
            ss.Clear()

        # Estado reservado
        aviso_estado = st.empty()

        aviso_estado.markdown("""
            <div class="assiafb-alert">
            <p><strong>🖱️ Esperando input del usuario en AutoCAD...</strong></p>
            </div>
            """, unsafe_allow_html=True)

        # Esto pausa Python hasta que tú termines de seleccionar en AutoCAD y des ENTER
        try:
            ss.SelectOnScreen()
            aviso_estado.empty()
        except pythoncom.com_error:
            # Si el usuario da ESC o cancela
            ss.Delete()
            aviso_estado.empty()

        # Procesando captura
        datos = []
        if ss.Count > 0:
            for entidad in ss:
                if entidad.EntityName == "AcDbLine":
                    datos.append(entidad.Handle)
    except:
        datos = []
    return datos

def estio_red_seleccion(row):
    if row["ID"] in st.session_state['seleccion_actual_id']:
        return ['background-color: rgba(220, 53, 69, 0.5); color: white; font-weight: bold'] * len(row)
    else:
        return [''] * len(row)

def estio_red_seleccion_indice(row):
    if row.name in st.session_state['seleccion_actual_id']:
        return ['background-color: rgba(220, 53, 69, 0.5); color: white; font-weight: bold'] * len(row)
    else:
        return [''] * len(row)

def extaer_barras():

    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    doc = acad.ActiveDocument
    model_space = doc.ModelSpace
    lista_barras = []

    for entidad in model_space:

        # Filtramos solo las lineas 
        if entidad.EntityName == "AcDbLine":
            
            # Id unico
            id_barra = entidad.Handle

            # Coordenadas
            punto_inicio = tuple(round(c, 5) for c in entidad.StartPoint)
            punto_fin    = tuple(round(c, 5) for c in entidad.EndPoint)

            # Nombre de capa
            nombre_capa = entidad.Layer
            objeto_capa = doc.Layers.Item(nombre_capa)

            # Descripcion de capa
            descripcion_capa = objeto_capa.Description
            
            # Extraemos las propiedades
            E, A = extraer_propiedades(descripcion_capa)

            # Guardamos los datos
            datos = {
                "ID": id_barra,
                "Inicio (x, y, z)": punto_inicio,
                "Fin (x, y, z)": punto_fin,
                "E": E,
                "A": A,
                "Capa": nombre_capa
            }
            lista_barras.append(datos)

        
    print("listo")

    return lista_barras

def contructor_nodos(data_frame):
    col_inicio = 'Inicio (x, y, z)'
    col_fin = 'Fin (x, y, z)'
    todos_los_nodos = pd.concat([data_frame[col_inicio], data_frame[col_fin]])

    nodos_unicos = todos_los_nodos.unique()

    mapa_nodos = {coord: int(i) for i, coord in enumerate(nodos_unicos)}
    mapa_nodos_inv = {int(i): coord for i, coord in enumerate(nodos_unicos)}

    data_frame['Nodo i'] = data_frame[col_inicio].map(mapa_nodos)
    data_frame['Nodo f'] = data_frame[col_fin].map(mapa_nodos)


    return len(nodos_unicos), data_frame, pd.DataFrame(mapa_nodos_inv)


def funcion_cargar_datos():
    lista_barras = extaer_barras()
    seccion = "Datos extraidos"
    
    if lista_barras:
        st.markdown("""
        <div class="assiafb-alert">
        <p><strong>✅ Exito:</strong> Se cargaron correctamente las barras</p>
        </div>
        """, unsafe_allow_html=True)
        estado = True
    else:
        st.markdown("""
        <div class="assiafb-alert">
        <p><strong>❌ Ocurrió un error:</strong> No se encontraron barras, verifica que el archivo este abierto y que las barras sean lineas y no polilineas</p>
        </div>
        """, unsafe_allow_html=True)
        estado = False
    return estado, seccion, lista_barras

# fuente: https://hebmerma.com/analisis-estructural/analisis-de-armaduras-espaciales-hm-armaduras3d-v-1-excel/
def k_rigidez(ni,nf, A, E):
    xi, yi, zi = ni
    xf, yf, zf = nf

    longt = math.sqrt((xf - xi)**2 + (yf - yi)**2 + (zf - zi)**2)

    lambda_x = (xf - xi)/longt
    lambda_y = (yf - yi)/longt
    lambda_z = (zf - zi)/longt

    AE_L = A*E/longt

    ki = AE_L*np.array([[lambda_x**2, lambda_x*lambda_y, lambda_x*lambda_z, -lambda_x**2, -lambda_x*lambda_y, -lambda_x*lambda_z],
                        [lambda_x*lambda_y, lambda_y**2, lambda_y*lambda_z, -lambda_x*lambda_y, -lambda_y**2, -lambda_y*lambda_z],
                        [lambda_x*lambda_z, lambda_y*lambda_z, lambda_z**2, -lambda_x*lambda_z, -lambda_y*lambda_z, -lambda_z**2],
                        [-lambda_x**2, -lambda_x*lambda_y, -lambda_x*lambda_z, lambda_x**2, lambda_x*lambda_y, lambda_x*lambda_z],
                        [-lambda_x*lambda_y, -lambda_y**2, -lambda_y*lambda_z, lambda_x*lambda_y, lambda_y**2, lambda_y*lambda_z],
                        [-lambda_x*lambda_z, -lambda_y*lambda_z, -lambda_z**2, lambda_x*lambda_z, lambda_y*lambda_z, lambda_z**2]])

    return ki

@st.cache_resource(show_spinner=False)
def ensambladora(matriz_rigidez, numero_nodos, nodo_GDL_barras_act):
    dims = numero_nodos*3
    k_global = np.zeros((dims, dims))
    fuerzas_globales = np.zeros(dims)
    desplazamientos_globales = np.zeros(dims)
    
    for k in matriz_rigidez:
        indices_loc = nodo_GDL_barras_act[k]
        rango_usado = np.ix_(indices_loc, indices_loc)
        k_global[rango_usado] += matriz_rigidez[k]

    return k_global, fuerzas_globales, desplazamientos_globales

@st.cache_resource(show_spinner=False)
def fuerzas_globales_func(fuerzas_vect, fuerzas, nodo_GDL_actuales):
    for fuerza in fuerzas.to_dict(orient='records'):
        nodo_id = fuerza["Nodo"]
        gdl = nodo_GDL_actuales[nodo_id]
        fx, fy, fz = fuerza["(Fx, Fy, Fz)"]
        fuerzas_vect[gdl] = [fx, fy, fz]
    return fuerzas_vect

@st.cache_resource(show_spinner=False)
def grados_lib_restr_func(restricciones, nodo_GDL_actuales):
    grados_lib_rest = []
    GDL_total = np.arange(len(nodo_GDL_actuales)*3)
    for restriccion in restricciones.to_dict(orient='records'):
        nodo_id = restriccion["Nodo"]
        gdl = nodo_GDL_actuales[nodo_id]
        lista_actuante = []

        Rx, Ry, Rz = restriccion["(Rx, Ry, Rz)"]

        if Rx:
            lista_actuante.append(gdl[0])
        if Ry:
            lista_actuante.append(gdl[1])
        if Rz:
            lista_actuante.append(gdl[2])

        grados_lib_rest += lista_actuante

    return grados_lib_rest, np.setdiff1d(GDL_total, grados_lib_rest)

@st.cache_resource(show_spinner=False)
def funcion_calcular(barras, nodos, fuerzas, restricciones):
    nodo_GDL_actuales = {}
    nodo_GDL_barras_act = {}
    nodo_GDL_despl_barras = {}
    matriz_rigidez = {}
    def_un_esf_normal = {}
    seccion = "Vista de deformada"
    matriz_rigidez_global = None
    fuerzas_globales = None
    if len(barras) > 0 and len(nodos) > 0 and len(fuerzas) > 0 and len(restricciones) > 0:
        estado = True
        try:
            for nodo in nodos:
                nodo_GDL_actuales[nodo] = [nodo*3, nodo*3+1, nodo*3+2]
            for barra in barras.to_dict(orient='records'):
                id_barra = barra["ID"]
                nis = barra["Inicio (x, y, z)"]
                nfs = barra["Fin (x, y, z)"]
                Es = barra["E"]
                As = barra["A"]
                ni_id = barra["Nodo i"]
                nf_id = barra["Nodo f"]
                ks = k_rigidez(nis,nfs, As, Es)
                matriz_rigidez[id_barra] = ks
                nodo_GDL_barras_act[id_barra] = nodo_GDL_actuales[ni_id] + nodo_GDL_actuales[nf_id]
            
            matriz_rigidez_global, fuerzas_globales, desplazamientos_globales = ensambladora(matriz_rigidez, len(nodo_GDL_actuales), nodo_GDL_barras_act)
            fuerzas_globales = fuerzas_globales_func(fuerzas_globales, fuerzas, nodo_GDL_actuales)
            grados_lib_restr, grados_lib_libres = grados_lib_restr_func(restricciones, nodo_GDL_actuales)

            # Calculo de desplamientos
            rango_usado = np.ix_(grados_lib_libres, grados_lib_libres)
            desplazamientos_globales[grados_lib_libres] = fuerzas_globales[grados_lib_libres].T @ np.linalg.inv(matriz_rigidez_global[rango_usado])

            # Fuerza completa
            fuerzas_globales = desplazamientos_globales.T @ matriz_rigidez_global
            
            for barra in barras.to_dict(orient='records'):
                id_barra = barra["ID"]
                xi, yi, zi = barra["Inicio (x, y, z)"]
                xf, yf, zf = barra["Fin (x, y, z)"]
                Es = barra["E"]
                As = barra["A"]
                nodo_GDL_despl_barras[id_barra] = desplazamientos_globales[nodo_GDL_barras_act[id_barra]]

                #def_unitarias
                longt = math.sqrt((xf - xi)**2 + (yf - yi)**2 + (zf - zi)**2)
                lambda_x = (xf - xi)/longt
                lambda_y = (yf - yi)/longt
                lambda_z = (zf - zi)/longt

                def_uni = (1/longt)*np.array([-lambda_x, -lambda_y, -lambda_z, lambda_x, lambda_y, lambda_z]) @ desplazamientos_globales[nodo_GDL_barras_act[id_barra]].T
                
                if def_uni > 0:
                    tipo_esfuerzo = "Traccion"
                elif def_uni < 0:
                    tipo_esfuerzo = "Compresion"
                else:
                    tipo_esfuerzo = "Sin esfuerzo"
                
                # esfuerzo
                esfuerzo = Es * def_uni
                fuerza_axial = esfuerzo * As

                def_un_esf_normal[id_barra] = [def_uni, esfuerzo, fuerza_axial, tipo_esfuerzo]  
            
        except Exception as e:
            estado = False
            st.markdown("""
            <div class="assiafb-alert">
            <p><strong>❌ Ocurrió un error:</strong> La estructura no se pudo calcular, verifica las restricciones, propiedades mecánicas y geométricas </p>
            </div>
            """, unsafe_allow_html=True)

            matriz_rigidez_global = None
            fuerzas_globales = None

            print(e)
        
    else:
        st.markdown("""
        <div class="assiafb-alert">
        <p><strong>❌ Ocurrió un error:</strong> No se encontraron datos para calcular, verifica las barras, fuerzas y restricciones</p>
        </div>
        """, unsafe_allow_html=True)
        estado = False

    return estado, seccion, nodo_GDL_barras_act, nodo_GDL_despl_barras, matriz_rigidez, def_un_esf_normal, matriz_rigidez_global, fuerzas_globales

@st.cache_resource(show_spinner=False)
def ploter_def(barras, nodos_coord):
    if len(barras) > 0 and len(nodos_coord):
        # Creamos la figura
        fig = go.Figure()
        nx, ny, nz = [], [], []
        max_coord = 0
        n_text = []
        x_lines, y_lines, z_lines = [], [], []
        for nodo in nodos_coord:
            nodo_t = tuple(nodos_coord[nodo].tolist())
            nx.append(nodo_t[0])
            ny.append(nodo_t[1])
            nz.append(nodo_t[2])
            n_text.append(str(nodo))

        for i, barra in enumerate(barras.to_dict(orient='records')):
            id_barra = barra["ID"]
            xi, yi, zi = barra["Inicio (x, y, z)"]
            xf, yf, zf = barra["Fin (x, y, z)"]

            xm = (xi+xf)/2
            ym = (yi+yf)/2
            zm = (zi+zf)/2

            longt = math.sqrt((xf - xi)**2 + (yf - yi)**2 + (zf - zi)**2)

            max_coord = max(max_coord, abs(xi), abs(xf), abs(yi), abs(yf), abs(zi), abs(zf))

            info = f"<b>ID: {id_barra}</b><br>L: {longt:.3f}"

            x_lines.extend([xi, xf, None])
            y_lines.extend([yi, yf, None])
            z_lines.extend([zi, zf, None])

            # Barras
            fig.add_trace(go.Scatter3d(
                x=[xm],
                y=[ym],
                z=[zm],
                mode='markers',
                name='Etiquetas',
                text=info,
                hoverinfo='text',
                hoverlabel=dict(
                    bgcolor="white",       
                    font=dict(
                        size=15,           
                        family="Arial",    
                        color="black"      
                    )
                ),
                marker=dict(
                    size=15,      
                    opacity=0,    
                    color='white' 
                )
            ))
        
        long_vect = max_coord * 0.2 if max_coord > 0 else 5

        # Estructura
        fig.add_trace(go.Scatter3d(
            x=x_lines,
            y=y_lines,
            z=z_lines,
            mode='lines',
            line=dict(color='#00FFFF', width=5),
            hoverinfo='none'
        ))

        # Vector x
        fig.add_trace(go.Scatter3d(
            x=[0, long_vect], y=[0, 0], z=[0, 0],
            mode='lines+text', text=["", "X"], textposition="middle right",
            line=dict(color='red', width=10), 
            textfont=dict(color='red', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Vector y
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, long_vect], z=[0, 0],
            mode='lines+text', text=["", "Y"], textposition="middle center",
            line=dict(color='#00FF00', width=10),
            textfont=dict(color='#00FF00', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Vector z
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, long_vect],
            mode='lines+text', text=["", "Z"], textposition="middle center",
            line=dict(color='blue', width=10),
            textfont=dict(color='blue', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Nodos
        fig.add_trace(go.Scatter3d(
            x=nx, y=ny, z=nz,
            mode='markers',
            name='Nodos',
            text=n_text,       
            hoverinfo='text',  
            hoverlabel=dict(
                bgcolor="rgba(50, 50, 50, 0.9)",
                bordercolor="#FFD700",           
                font=dict(size=16, color="white")
            ),
            marker=dict(
                size=8,        
                color='white', 
                symbol='circle'
            )
        ))

        # Configuracion visual
        fig.update_layout(
            title="Visualización 3D - Estado Inicial",
            showlegend=False,
            paper_bgcolor='black',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                aspectmode='data',
                bgcolor='black',
                xaxis=dict(visible=False, showgrid=False,showticklabels=False, title=''), 
                yaxis=dict(visible=False, showgrid=False,showticklabels=False, title=''), 
                zaxis=dict(visible=False, showgrid=False,showticklabels=False, title='')  
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        st.plotly_chart(fig, width="stretch", height=1200, theme=None, key="armadura_3d",config={
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'responsive': True
        })

        st.markdown("<br>" * 3, unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def ploter_def_deformada(barras, nodo_GDL_despl_barras, matriz_rigidez, def_un_esf_normal, escala_deformada, nodo_GDL_barras_act):   
    if len(barras) > 0 and len(nodo_GDL_despl_barras) > 0 and len(matriz_rigidez) > 0 and len(def_un_esf_normal) > 0:
        # Creamos la figura
        fig = go.Figure()
        max_coord = 0
        x_lines_comp, y_lines_comp, z_lines_comp = [], [], []
        x_lines_trac, y_lines_trac, z_lines_trac = [], [], []
        x_lines_neut, y_lines_neut, z_lines_neut = [], [], []

        for i, barra in enumerate(barras.to_dict(orient='records')):
            id_barra = barra["ID"]
            xi, yi, zi = barra["Inicio (x, y, z)"]
            xf, yf, zf = barra["Fin (x, y, z)"]

            xid, yid, zid, xfd, yfd, zfd = nodo_GDL_despl_barras[id_barra]

            def_unt_barra = def_un_esf_normal[id_barra][0]
            esfuerzo_axial = def_un_esf_normal[id_barra][1]
            fuerza_axial = def_un_esf_normal[id_barra][2]
            
            info = (
                f"<b>ID: {id_barra}</b><br>"
                f"U: {def_unt_barra:.2e}<br>"
                f"σ: {esfuerzo_axial:.2e}<br>"  
                f"<i>F</i>: {fuerza_axial:.2e}")

            xi = xi + xid * escala_deformada
            yi = yi + yid * escala_deformada
            zi = zi + zid * escala_deformada
            xf = xf + xfd * escala_deformada
            yf = yf + yfd * escala_deformada
            zf = zf + zfd * escala_deformada

            if def_unt_barra > 0:
                x_lines_trac.extend([xi, xf, None])
                y_lines_trac.extend([yi, yf, None])
                z_lines_trac.extend([zi, zf, None])
            elif def_unt_barra < 0:
                x_lines_comp.extend([xi, xf, None])
                y_lines_comp.extend([yi, yf, None])
                z_lines_comp.extend([zi, zf, None])
            else:
                x_lines_neut.extend([xi, xf, None])
                y_lines_neut.extend([yi, yf, None])
                z_lines_neut.extend([zi, zf, None])

            xm = (xi+xf)/2
            ym = (yi+yf)/2
            zm = (zi+zf)/2

            max_coord = max(max_coord, abs(xi), abs(xf), abs(yi), abs(yf), abs(zi), abs(zf))

            # Barras
            fig.add_trace(go.Scatter3d(
                x=[xm],
                y=[ym],
                z=[zm],
                mode='markers',
                name='Etiquetas',
                text=info,
                hoverinfo='text',
                hoverlabel=dict(
                    bgcolor="white",       
                    font=dict(
                        size=15,           
                        family="Arial",    
                        color="black"      
                    )
                ),
                marker=dict(
                    size=15,      
                    opacity=0,    
                    color='white' 
                )
            ))

        
        long_vect = max_coord * 0.2 if max_coord > 0 else 5

        # Vector x
        fig.add_trace(go.Scatter3d(
            x=[0, long_vect], y=[0, 0], z=[0, 0],
            mode='lines+text', text=["", "X"], textposition="middle right",
            line=dict(color='red', width=10), 
            textfont=dict(color='red', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Vector y
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, long_vect], z=[0, 0],
            mode='lines+text', text=["", "Y"], textposition="middle center",
            line=dict(color='#00FF00', width=10),
            textfont=dict(color='#00FF00', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Vector z
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, long_vect],
            mode='lines+text', text=["", "Z"], textposition="middle center",
            line=dict(color='cyan', width=10),
            textfont=dict(color='cyan', size=25, family="Arial Black"),
            hoverinfo='none', showlegend=False
        ))

        # Estructura
        # traccion
        fig.add_trace(go.Scatter3d(
            x=x_lines_trac,
            y=y_lines_trac,
            z=z_lines_trac,
            mode='lines',
            line=dict(color="rgb(0, 255, 0)", width=12),
            hoverinfo='none'
        ))
        # compresion
        fig.add_trace(go.Scatter3d(
            x=x_lines_comp,
            y=y_lines_comp,
            z=z_lines_comp,
            mode='lines',
            line=dict(color="rgb(255, 0, 0)", width=12),
            hoverinfo='none'
        ))
        # neutra
        fig.add_trace(go.Scatter3d(
            x=x_lines_neut,
            y=y_lines_neut,
            z=z_lines_neut,
            mode='lines',
            line=dict(color="rgb(255, 255, 255)", width=12),
            hoverinfo='none'
        ))

        # Configuracion visual
        fig.update_layout(
            title="Visualización 3D - Estado Inicial",
            showlegend=False,
            paper_bgcolor='black',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                aspectmode='data',
                bgcolor='black',
                xaxis=dict(visible=False, showgrid=False,showticklabels=False, title=''), 
                yaxis=dict(visible=False, showgrid=False,showticklabels=False, title=''), 
                zaxis=dict(visible=False, showgrid=False,showticklabels=False, title='')  
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        st.plotly_chart(fig, width="stretch", height=1200)

        st.markdown("<br>" * 3, unsafe_allow_html=True) 

        st.markdown(f"<div class='section-title'>{'Resumenes (ID Barra)'.upper()}:</div>", unsafe_allow_html=True) 

        # desplamiento en armadura
        data_frame = pd.DataFrame(nodo_GDL_despl_barras).T.rename(columns={
                                        0: "U-X (Nodo inicial)",
                                        1: "U-Y (Nodo inicial)",
                                        2: "U-Z (Nodo inicial)",
                                        3: "U-X (Nodo final)",
                                        4: "U-Y (Nodo final)",
                                        5: "U-Z (Nodo final)"
                                    })
        styler = data_frame.style.apply(estio_red_seleccion_indice, axis=1)
        html_tabla_df_desplazamientos = styler.to_html(classes='tabla-ingenieria', index=True, border=0)

        with st.expander("Desplazamientos nodales en los elementos".upper(), expanded=False):
            st.markdown(f"<div class='contenedor-tabla'>{html_tabla_df_desplazamientos}</div>", unsafe_allow_html=True)  

        # deformacion unitaria esfuerzo normal
        data_frame = pd.DataFrame(def_un_esf_normal).T.rename(columns={
                                        0: "Deformación unitaria",
                                        1: "Esfuerzo normal",
                                        2: "Fuerza interna",
                                        3: "Tipo de fuerza",
                                    })
        styler = data_frame.style.apply(estio_red_seleccion_indice, axis=1)
        html_tabla_df_unitaria = styler.to_html(classes='tabla-ingenieria', index=True, border=0)

        with st.expander("Deformacion unitaria - Esfuerzo normal - Fuerza Interna en los elementos".upper(), expanded=False):
            st.markdown(f"<div class='contenedor-tabla'>{html_tabla_df_unitaria}</div>", unsafe_allow_html=True)  

        st.markdown(f"<div class='section-title'>{'Matriz de rigidez por elemento seleccionado'.upper()}:</div>", unsafe_allow_html=True) 

        for matriz in matriz_rigidez:
            if matriz in st.session_state['seleccion_actual_id']:
                kg_text = matriz_rigidez[matriz]
                filas_tex = []
                for fila in kg_text:
                    texto_fila = " & ".join([f"{x:.3f}" for x in fila])
                    filas_tex.append(texto_fila)

                contenido_latex = " \\\\ ".join(filas_tex)

                ecuacion = f"K_{{{matriz}}} = \\begin{{bmatrix}} {contenido_latex} \\end{{bmatrix}}"

                st.latex(ecuacion)

        st.markdown(f"<div class='section-title'>{'Grados de libertad por elemento seleccionado'.upper()}:</div>", unsafe_allow_html=True) 

        for gdl_act in nodo_GDL_barras_act:
            if gdl_act in st.session_state['seleccion_actual_id']:
                kg_text = nodo_GDL_barras_act[gdl_act]

                texto_fila = " & ".join([f"{x}" for x in kg_text])

                ecuacion = f"GDL_{{{gdl_act}}} = \\begin{{bmatrix}} {texto_fila} \\end{{bmatrix}}"

                st.latex(ecuacion)

@st.cache_resource(show_spinner=False)
def print_globales():
    try:
        if len(st.session_state['matriz_rigidez_global']) > 0 and len(st.session_state['fuerzas_globales']) > 0:
            st.markdown(f"<div class='section-title'>{'Matriz de rigidez global de la estructura'.upper()}:</div>", unsafe_allow_html=True) 
            filas_tex = []
            for fila in st.session_state['matriz_rigidez_global']:
                texto_fila = " & ".join([f"{x:.3e}" for x in fila])
                filas_tex.append(texto_fila)

            contenido_latex_global = " \\\\ ".join(filas_tex)

            ecuacion = f"K_{{global}} = \\begin{{bmatrix}} {contenido_latex_global} \\end{{bmatrix}}"
            
            with st.expander("", expanded=False):
                st.latex(ecuacion)

            st.markdown(f"<div class='section-title'>{'Vector de fuerzas de la estructura'.upper()}:</div>", unsafe_allow_html=True) 
            contenido_vector = " \\\\ ".join([f"{x:.3e}" for x in st.session_state['fuerzas_globales']])
            ecuacion = f"F_{{global}} = \\begin{{bmatrix}} {contenido_vector} \\end{{bmatrix}}"
            with st.expander("", expanded=False):
                st.latex(ecuacion)
        else:
            contenedor_mensaje = st.empty()
            contenedor_mensaje.markdown(f"""
            <div class="assiafb-body-center">
            <p>
                No existe datos de calculo, porfavor haga clic en el boton "Calcular Armadura" para obtener los resultados
            </p>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state['condicion_globales'] == False:
                contenedor_mensaje.empty()
    except:
        contenedor_mensaje = st.empty()
        contenedor_mensaje.markdown(f"""
        <div class="assiafb-body-center">
        <p>
            No existe datos de calculo, porfavor haga clic en el boton "Calcular Armadura" para obtener los resultados
        </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state['condicion_globales'] == False:
            contenedor_mensaje.empty()

@st.cache_resource(show_spinner=False)
def seleccionar_nudo_comun(metodo_seleccion_id_comun, ids_seleccionados, barras_dict): 
    
    nodos_respectivo = []

    if ids_seleccionados and metodo_seleccion_id_comun != "Nodo unico":
        barras_filtradas_nodos = barras_dict[barras_dict['ID'].isin(ids_seleccionados)][['ID', 'Nodo i', 'Nodo f']]
        if metodo_seleccion_id_comun == "Todos los nudos":
            nodos_respectivo = pd.concat([barras_filtradas_nodos['Nodo i'], barras_filtradas_nodos['Nodo f']]).unique()
        elif metodo_seleccion_id_comun == "El nudo en común":
            # truco juntamos los nodos y vemos que nudo se repite tantas veces como barras seleccionadas
            nodos_respectivo = pd.concat([barras_filtradas_nodos['Nodo i'], barras_filtradas_nodos['Nodo f']])
            conteo = nodos_respectivo.value_counts()
            nodos_respectivo = conteo[conteo == len(barras_filtradas_nodos)].index.tolist()
        
        texto_nodos = ", ".join(map(str, nodos_respectivo)) if len(nodos_respectivo) > 0 else "Ninguno"

        st.markdown(f"""
            <div class="assiafb-alert">
            <p><strong>{metodo_seleccion_id_comun.upper()}:</strong> Nodo(s) a participar {texto_nodos}</p>
            </div>
            """, unsafe_allow_html=True)
    elif metodo_seleccion_id_comun != "Nodo unico":
        st.markdown("""
            <div class="assiafb-alert">
            <p><strong>❌ Ocurrió un error:</strong> No se seleccionaron barras</p>
            </div>
            """, unsafe_allow_html=True)

    if metodo_seleccion_id_comun == "Nodo unico":
        nodos_respectivo = [st.session_state['nodo_unico']]
        texto_nodos = ", ".join(map(str, nodos_respectivo)) if len(nodos_respectivo) > 0 else "Ninguno"
        st.markdown(f"""
            <div class="assiafb-alert">
            <p><strong>{metodo_seleccion_id_comun.upper()}:</strong> Nodo(s) a participar {texto_nodos}</p>
            </div>
            """, unsafe_allow_html=True)
    
    return nodos_respectivo
            
# Función para cargar CSS externo
@st.cache_resource(show_spinner=False)
def load_css(file_name):
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo de estilos: {file_name}")

@st.cache_resource(show_spinner=False)
def obtener_ruta_recurso(ruta_relativa):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, ruta_relativa)

@st.cache_resource(show_spinner=False)
def target_autor():
    st.markdown("""
    <div class="assiafb-author-card">
    <h3>Autor: Jesús Bautista</h3>
    <div class="assiafb-links">
        <a class="assiafb-link" href="https://www.linkedin.com/in/jesus-bautista-ing-civil/" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg" alt="LinkedIn">
        </a>
        <a class="assiafb-link" href="https://www.youtube.com/@bitbuilderx" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/youtube.svg" alt="YouTube">
        </a>
        <a class="assiafb-link" href="https://github.com/Assia-Network" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg" alt="GitHub">
        </a>
    </div>
    </div>
    """, unsafe_allow_html=True)