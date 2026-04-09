import time
from threading import Thread, Event  # Para controle da animação em segundo plano

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display
from ipywidgets import interact, IntSlider, FloatSlider, VBox, HBox, Button

# --- Parâmetros Astronômicos ---
NODAL_PERIOD_YEARS = 18.6
LUNAR_ORBIT_INCLINATION_DEG_DEFAULT = 5.14  # Inclinação padrão
EARTH_ORBIT_RADIUS = 0.0  # A Terra está na origem para esta visualização

# --- Variáveis Globais para o Gráfico e Animação ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
animation_thread = None
stop_animation_event = Event()


# --- Configuração Inicial do Gráfico 3D ---
def setup_plot(azimuth, elevation):
    ax.clear()  # Limpa o gráfico para redesenhar
    ax.set_aspect('equal', adjustable='box')  # Garante que os círculos não sejam elipses visivelmente

    # Configura a vista da câmera
    ax.view_init(elev=elevation, azim=azimuth)

    ax.set_title('Ciclo Nodal Lunar (Visualização 3D Interativa)')
    ax.set_xlabel('X (Plano da Eclíptica)')
    ax.set_ylabel('Y (Plano da Eclíptica)')
    ax.set_zlabel('Z (Fora da Eclíptica)')

    # Definir limites fixos para estabilidade visual
    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    ax.set_zlim([-1.5, 1.5])

    # Eixos de referência com setas para melhor orientação 3D
    ax.quiver(0, 0, 0, 1.5, 0, 0, color='gray', linestyle=':', arrow_length_ratio=0.1, label='Eixo X')
    ax.quiver(0, 0, 0, 0, 1.5, 0, color='gray', linestyle=':', arrow_length_ratio=0.1, label='Eixo Y')
    ax.quiver(0, 0, 0, 0, 0, 1.5, color='gray', linestyle=':', arrow_length_ratio=0.1, label='Eixo Z')

    # Eclíptica (plano de referência XY)
    ecliptic_theta = np.linspace(0, 2 * np.pi, 100)
    ecliptic_x = 1.0 * np.cos(ecliptic_theta)
    ecliptic_y = 1.0 * np.sin(ecliptic_theta)
    ecliptic_z = np.zeros_like(ecliptic_x)  # Z é zero para a eclíptica
    ax.plot(ecliptic_x, ecliptic_y, ecliptic_z, 'k--', alpha=0.5, label='Eclíptica (Plano XY)')
    ax.plot([0], [0], [0], 'o', color='blue', markersize=8, label='Terra (Origem)')


# --- Função de Atualização do Gráfico ---
def update_plot(nodal_progress_years, inclination_deg, orbit_radius,
                azimuth_deg, elevation_deg, num_steps_orbit):
    setup_plot(azimuth_deg, elevation_deg)  # Limpa e configura o plot base a cada atualização

    current_inclination_rad = np.deg2rad(inclination_deg)

    # Calcular a rotação atual dos nodos com base no progresso em anos
    # Os nodos regridem (movimento no sentido horário), então a rotação é negativa.
    nodal_longitude_rad = (nodal_progress_years / NODAL_PERIOD_YEARS) * (2 * np.pi) * -1

    # Pontos da órbita lunar antes da rotação e inclinação
    theta_moon_orbit = np.linspace(0, 2 * np.pi, num_steps_orbit)
    x_orbit_base = orbit_radius * np.cos(theta_moon_orbit)
    y_orbit_base = orbit_radius * np.sin(theta_moon_orbit)
    z_orbit_base = np.zeros_like(theta_moon_orbit)

    # 1. Inclinação do plano da órbita lunar
    # Rotação em torno do eixo X do plano dos nodos.
    x_inclined = x_orbit_base
    y_inclined = y_orbit_base * np.cos(current_inclination_rad) - z_orbit_base * np.sin(current_inclination_rad)
    z_inclined = y_orbit_base * np.sin(current_inclination_rad) + z_orbit_base * np.cos(current_inclination_rad)

    # 2. Precessão dos Nodos (Rotação do plano inclinado em torno do eixo Z da eclíptica)
    x_final = x_inclined * np.cos(nodal_longitude_rad) - y_inclined * np.sin(nodal_longitude_rad)
    y_final = x_inclined * np.sin(nodal_longitude_rad) + y_inclined * np.cos(nodal_longitude_rad)
    z_final = z_inclined  # A rotação em Z não afeta a coordenada Z

    # Plotar a órbita lunar
    ax.plot(x_final, y_final, z_final, 'r-', label='Órbita Lunar')

    # --- Calcular e Plotar os Nodos Lunares ---
    # Nodos estão no plano da eclíptica (Z=0)
    # Nodo ascendente
    node_asc_x = orbit_radius * np.cos(nodal_longitude_rad)
    node_asc_y = orbit_radius * np.sin(nodal_longitude_rad)
    ax.plot([node_asc_x], [node_asc_y], [0], 'gx', markersize=10, label='Nodo Ascendente')

    # Nodo descendente (180 graus de diferença do ascendente)
    node_desc_x = orbit_radius * np.cos(nodal_longitude_rad + np.pi)
    node_desc_y = orbit_radius * np.sin(nodal_longitude_rad + np.pi)
    ax.plot([node_desc_x], [node_desc_y], [0], 'go', markersize=10, label='Nodo Descendente')

    # Informações adicionais
    ax.text2D(0.05, 0.95, f'Progresso: {nodal_progress_years:.1f} anos', transform=ax.transAxes, fontsize=10)
    ax.text2D(0.05, 0.90, f'Longitude Nodal: {np.degrees(nodal_longitude_rad) % 360:.1f}°', transform=ax.transAxes,
              fontsize=10)

    ax.legend(loc='upper left', bbox_to_anchor=(0.85, 0.95), fontsize='small')
    plt.show()  # Exibir o gráfico atualizado


# --- Interface de Controle (ipywidgets) ---

# Sliders para parâmetros do ciclo nodal
nodal_slider = FloatSlider(
    value=0, min=0, max=NODAL_PERIOD_YEARS, step=0.1,
    description='Progresso Ciclo (Anos):', readout=True, readout_format='.1f',
    layout={'width': 'auto'}
)

inclination_slider = FloatSlider(
    value=LUNAR_ORBIT_INCLINATION_DEG_DEFAULT, min=0, max=10, step=0.1,
    description='Inclinação Órbita (°):', readout=True, readout_format='.1f',
    layout={'width': 'auto'}
)

orbit_radius_slider = FloatSlider(
    value=1.0, min=0.5, max=2.0, step=0.1,
    description='Raio Órbita:', readout=True, readout_format='.1f',
    layout={'width': 'auto'}
)

steps_slider = IntSlider(
    value=100, min=20, max=500, step=10,
    description='Suavidade Órbita:', readout=True,
    layout={'width': 'auto'}
)

# Sliders para controle da câmera 3D
azimuth_slider = FloatSlider(
    value=30, min=0, max=360, step=5,
    description='Azimute Câmera (°):', readout=True, readout_format='.0f',
    layout={'width': 'auto'}
)

elevation_slider = FloatSlider(
    value=30, min=0, max=90, step=5,
    description='Elevação Câmera (°):', readout=True, readout_format='.0f',
    layout={'width': 'auto'}
)

# Botão para resetar a câmera
reset_camera_button = Button(description="Resetar Câmera")


def on_reset_camera_clicked(b):
    azimuth_slider.value = 30
    elevation_slider.value = 30


reset_camera_button.on_clicked(on_reset_camera_clicked)

# Botões para controle da animação automática
animation_speed_slider = FloatSlider(
    value=0.1, min=0.01, max=1.0, step=0.01,
    description='Velocidade Animação:', readout=True, readout_format='.2f',
    layout={'width': 'auto'}
)

start_animation_button = Button(description="Iniciar Animação")
stop_animation_button = Button(description="Parar Animação")


def run_animation():
    global animation_thread
    stop_animation_event.clear()  # Limpa o evento de parada

    for year_val in np.arange(nodal_slider.value, NODAL_PERIOD_YEARS + 0.05, animation_speed_slider.value):
        if stop_animation_event.is_set():
            break  # Sai do loop se o evento de parada for acionado
        nodal_slider.value = year_val
        time.sleep(0.05)  # Pequeno atraso por frame

    # Resetar o slider no final da animação completa, se não foi parado manualmente
    if not stop_animation_event.is_set():
        nodal_slider.value = 0  # Volta ao início se o ciclo terminar

    animation_thread = None  # Libera a thread após a conclusão/parada


def on_start_animation_clicked(b):
    global animation_thread
    if animation_thread is None or not animation_thread.is_alive():
        animation_thread = Thread(target=run_animation)
        animation_thread.start()


def on_stop_animation_clicked(b):
    stop_animation_event.set()  # Aciona o evento para parar a animação


start_animation_button.on_clicked(on_start_animation_clicked)
stop_animation_button.on_clicked(on_stop_animation_clicked)

# Agrupar os sliders em VBoxes
nodal_controls = VBox([
    nodal_slider,
    inclination_slider,
    orbit_radius_slider,
    steps_slider
], layout={'border': '1px solid lightgray', 'padding': '10px', 'margin': '5px'})

camera_controls = VBox([
    azimuth_slider,
    elevation_slider,
    reset_camera_button
], layout={'border': '1px solid lightgray', 'padding': '10px', 'margin': '5px'})

animation_controls = VBox([
    animation_speed_slider,
    HBox([start_animation_button, stop_animation_button])
], layout={'border': '1px solid lightgray', 'padding': '10px', 'margin': '5px'})

# Criar o widget interativo principal
# 'continuous_update=False' para gráficos 3D que são mais pesados.
interactive_plot = interact(update_plot,
                            nodal_progress_years=nodal_slider,
                            inclination_deg=inclination_slider,
                            orbit_radius=orbit_radius_slider,
                            azimuth_deg=azimuth_slider,
                            elevation_deg=elevation_slider,
                            num_steps_orbit=steps_slider,
                            continuous_update=False)

# Exibir os controles e o gráfico no Jupyter/Colab
# clear_output(wait=True) # Limpa a saída anterior no notebook para exibir apenas o widget
display(HBox([nodal_controls, camera_controls, animation_controls]))

# Inicializa o plot uma vez com os valores padrão para exibir no início
# (Chamar interact já faz isso, mas se display for chamado antes, pode ser útil)
# update_plot(nodal_slider.value, inclination_slider.value, orbit_radius_slider.value,
#             azimuth_slider.value, elevation_slider.value, steps_slider.value)