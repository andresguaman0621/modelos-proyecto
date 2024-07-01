import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class Banco:
    def __init__(self, env, num_cajeros, tasa_llegada, tasa_servicio):
        self.env = env
        self.cajeros = simpy.Resource(env, num_cajeros)
        self.tasa_llegada = tasa_llegada
        self.tasa_servicio = tasa_servicio
        self.tiempos_espera = []
        self.tiempos_sistema = []

    def llegada_cliente(self):
        while True:
            yield self.env.timeout(random.expovariate(self.tasa_llegada))
            self.env.process(self.atencion_cliente())

    def atencion_cliente(self):
        llegada = self.env.now
        with self.cajeros.request() as req:
            yield req
            espera = self.env.now - llegada
            self.tiempos_espera.append(espera)
            tiempo_servicio = random.expovariate(self.tasa_servicio)
            yield self.env.timeout(tiempo_servicio)
            self.tiempos_sistema.append(self.env.now - llegada)

def ejecutar_simulacion(num_cajeros, tasa_llegada, tasa_servicio, tiempo_simulacion):
    env = simpy.Environment()
    banco = Banco(env, num_cajeros, tasa_llegada, tasa_servicio)
    env.process(banco.llegada_cliente())
    env.run(until=tiempo_simulacion)
    return banco

# Parámetros de simulación
num_cajeros = 3
tasa_llegada = 1/5  # Un cliente cada 5 minutos en promedio
tasa_servicio = 1/4  # 4 minutos de servicio en promedio
tiempo_simulacion = 480  # 8 horas

# Ejecutar simulación
banco = ejecutar_simulacion(num_cajeros, tasa_llegada, tasa_servicio, tiempo_simulacion)

# Calcular métricas
tiempo_espera_promedio = np.mean(banco.tiempos_espera)
tiempo_sistema_promedio = np.mean(banco.tiempos_sistema)
throughput = len(banco.tiempos_sistema) / tiempo_simulacion

print(f"Tiempo promedio de espera: {tiempo_espera_promedio:.2f} minutos")
print(f"Tiempo promedio en el sistema: {tiempo_sistema_promedio:.2f} minutos")
print(f"Throughput: {throughput:.2f} clientes por minuto")

# Crear una figura con dos subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Graficar resultados de la primera simulación
ax1.hist(banco.tiempos_espera, bins=30, edgecolor='black')
ax1.set_title('Distribución de tiempos de espera')
ax1.set_xlabel('Tiempo de espera (minutos)')
ax1.set_ylabel('Frecuencia')

# Ejemplo de recopilación de resultados
resultados = []
for num_cajeros in [2, 3, 4]:
    for tasa_llegada in [1/5, 1/4, 1/3]:
        for tasa_servicio in [1/4, 1/3, 1/2]:
            banco = ejecutar_simulacion(num_cajeros, tasa_llegada, tasa_servicio, tiempo_simulacion)
            tiempo_espera_promedio = np.mean(banco.tiempos_espera)
            tiempo_sistema_promedio = np.mean(banco.tiempos_sistema)
            throughput = len(banco.tiempos_sistema) / tiempo_simulacion
            resultados.append({
                'num_cajeros': num_cajeros,
                'tasa_llegada': tasa_llegada,
                'tasa_servicio': tasa_servicio,
                'tiempo_espera_promedio': tiempo_espera_promedio,
                'tiempo_sistema_promedio': tiempo_sistema_promedio,
                'throughput': throughput
            })

# Análisis de resultados
df_resultados = pd.DataFrame(resultados)
print(df_resultados)

# Gráfico de tiempo de espera vs número de cajeros
for tasa_llegada in [1/5, 1/4, 1/3]:
    data = df_resultados[df_resultados['tasa_llegada'] == tasa_llegada]
    ax2.plot(data['num_cajeros'], data['tiempo_espera_promedio'], marker='o', label=f'Tasa llegada = {1/tasa_llegada:.2f} min')

ax2.set_title('Tiempo de espera promedio vs Número de cajeros')
ax2.set_xlabel('Número de cajeros')
ax2.set_ylabel('Tiempo de espera promedio (minutos)')
ax2.legend()
ax2.grid(True)

# Ajustar el diseño y mostrar la figura
plt.tight_layout()
plt.show()