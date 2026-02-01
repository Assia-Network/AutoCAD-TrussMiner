# AutoCAD TrussMiner

**AutoCAD TrussMiner** es una herramienta de escritorio (creada con Python y Streamlit) que automatiza la extracción de geometría y topología desde planos de AutoCAD para generar modelos de análisis estructural en 3D.

Su objetivo principal es eliminar la tediosa tarea de introducir coordenadas manualmente para el análisis de armaduras espaciales.

## ¿Qué hace realmente?

1.  **Conexión en Vivo:** Se conecta a una instancia abierta de AutoCAD usando la interfaz COM (`win32com`).
2.  **Filtrado Inteligente:** Escanea el dibujo activo, ignora textos y cotas, y extrae únicamente las líneas que representan barras.
3.  **Mapeo de Propiedades:** Lee las capas de las líneas para asignar propiedades mecánicas (Módulo de Elasticidad `E` y Área `A`) basándose en la descripción de la capa.
4.  **Visualización 3D:** Genera un gráfico interactivo con Plotly para inspeccionar la estructura antes de calcular.
5.  **Matriz de Rigidez:** Prepara los datos (nodos y conectividad) para ser procesados por métodos matriciales.

## Descarga

¿Listo para usarlo? Descarga el ejecutable para Windows directamente aquí:

[![Download](https://img.shields.io/badge/Windows-Descargar_Exe-0078D6?style=for-the-badge&logo=windows)](https://github.com/Assia-Network/AutoCAD-TrussMiner/releases/download/Windows/AutoCAD.TrussMiner.exe)

## ⚙️ Requisitos Previos

Para que el ejecutable funcione, necesitas:

- **Sistema Operativo:** Windows 10/11 (La interfaz COM de AutoCAD no existe en Mac/Linux).
- **Software:** AutoCAD instalado (cualquier versión desde 2018 en adelante debería funcionar).
- **Estado:** AutoCAD debe estar **abierto** y con un archivo `.dwg` cargado antes de iniciar TrussMiner.

## Cómo usarlo

1.  Abre tu modelo en **AutoCAD**.
    - _Nota:_ Asegúrate de que las barras sean líneas simples (`LINE`), no polilíneas.
    - _Tip:_ Usa capas distintas para diferentes secciones (ej. "Cordon_Superior", "Diagonales").
    - _Importante:_ En la descripción de las capas colocar el modulo de elasticidad y área transversal (ej. "E = 1e+11 , A = 0.25")
2.  Ejecuta `AutoCAD TrussMiner.exe`.
3.  Espera unos segundos a que cargue la interfaz.
4.  Haz clic en el botón para extraer datos.
5.  Visualiza tu armadura e inspecciona los nodos.

## ⚠️ Limitaciones Conocidas

- **Velocidad:** La extracción utiliza la tecnología COM de Windows. Para modelos pequeños (<1000 barras) es rápido. Para modelos masivos (+10,000 barras), puede tardar unos segundos en procesar la comunicación entre Python y AutoCAD.
- **Bloqueo de UI:** Mientras extrae los datos, la ventana puede parecer congelada ("No responde"). Es normal, está procesando.
- **Geometría:** Solo detecta líneas (`AcDbLine`). Si dibujaste tu estructura con Polilíneas (`PLINE`), debes explotarlas (`EXPLODE`) primero.
- **Permisos:** A veces Windows bloquea la conexión si AutoCAD se ejecuta como Administrador y este programa no (o viceversa). Intenta ejecutar ambos con el mismo nivel de privilegios.

## Tecnologías

- **Python 3.13** - Lógica principal.
- **Streamlit** - Interfaz de usuario.
- **PyWin32** - Comunicación con la API de AutoCAD.
- **Plotly** - Motor gráfico 3D.
- **Pandas** - Manipulación de datos vectorizada.

## Licencia

Este proyecto es de uso académico/personal. Úsalo bajo tu propia responsabilidad. Siempre verifica los resultados del análisis con un método alternativo.

---

_Desarrollado por Jesús Bautista Ramirez - 2026_
