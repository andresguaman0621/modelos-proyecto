import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class BancoMultiCola:
    def __init__(self, env, num_cajeros, tasa_llegada, tasa_servicio):
        self.env = env
        self.cajeros = [simpy.Resource(env, capacity=1) for _ in range(num_cajeros)]
        self.tasa_llegada = tasa_llegada
        self.tasa_servicio = tasa_servicio
        self.tiempos_espera = []
        self.tiempos_sistema = []
        self.longitudes_cola = {i: [] for i in range(num_cajeros)}

    def llegada_cliente(self):
        while True:
            yield self.env.timeout(random.expovariate(self.tasa_llegada))
            cajero_elegido = self.elegir_cajero_mas_corto()
            self.env.process(self.atencion_cliente(cajero_elegido))

    def elegir_cajero_mas_corto(self):
        return min(range(len(self.cajeros)), key=lambda i: len(self.cajeros[i].queue))

    def atencion_cliente(self, cajero_id):
        llegada = self.env.now
        with self.cajeros[cajero_id].request() as req:
            yield req
            espera = self.env.now - llegada
            self.tiempos_espera.append(espera)
            self.longitudes_cola[cajero_id].append(len(self.cajeros[cajero_id].queue))
            tiempo_servicio = random.expovariate(self.tasa_servicio)
            yield self.env.timeout(tiempo_servicio)
            self.tiempos_sistema.append(self.env.now - llegada)

def ejecutar_simulacion_multi_cola(num_cajeros, tasa_llegada, tasa_servicio, tiempo_simulacion):
    env = simpy.Environment()
    banco = BancoMultiCola(env, num_cajeros, tasa_llegada, tasa_servicio)
    env.process(banco.llegada_cliente())
    env.run(until=tiempo_simulacion)
    return banco

# Parámetros de simulación
tiempo_simulacion = 480  # 8 horas

# Función para ejecutar experimentos
def ejecutar_experimentos(num_cajeros_list, tasa_llegada_list, tasa_servicio_list):
    resultados = []
    for num_cajeros in num_cajeros_list:
        for tasa_llegada in tasa_llegada_list:
            for tasa_servicio in tasa_servicio_list:
                banco = ejecutar_simulacion_multi_cola(num_cajeros, tasa_llegada, tasa_servicio, tiempo_simulacion)
                tiempo_espera_promedio = np.mean(banco.tiempos_espera)
                tiempo_sistema_promedio = np.mean(banco.tiempos_sistema)
                throughput = len(banco.tiempos_sistema) / tiempo_simulacion
                longitud_cola_promedio = np.mean([np.mean(cola) for cola in banco.longitudes_cola.values()])
                resultados.append({
                    'num_cajeros': num_cajeros,
                    'tasa_llegada': tasa_llegada,
                    'tasa_servicio': tasa_servicio,
                    'tiempo_espera_promedio': tiempo_espera_promedio,
                    'tiempo_sistema_promedio': tiempo_sistema_promedio,
                    'throughput': throughput,
                    'longitud_cola_promedio': longitud_cola_promedio
                })
    return pd.DataFrame(resultados)

# Ejecutar experimentos
num_cajeros_list = [2, 3, 4]
tasa_llegada_list = [1/5, 1/4, 1/3]
tasa_servicio_list = [1/4, 1/3, 1/2]

df_resultados = ejecutar_experimentos(num_cajeros_list, tasa_llegada_list, tasa_servicio_list)

# Imprimir resultados
print(df_resultados)

# Gráficos
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# Gráfico de tiempo de espera vs número de cajeros
for tasa_llegada in tasa_llegada_list:
    data = df_resultados[df_resultados['tasa_llegada'] == tasa_llegada]
    ax1.plot(data['num_cajeros'], data['tiempo_espera_promedio'], marker='o', label=f'Tasa llegada = {1/tasa_llegada:.2f} min')

ax1.set_title('Tiempo de espera promedio vs Número de cajeros')
ax1.set_xlabel('Número de cajeros')
ax1.set_ylabel('Tiempo de espera promedio (minutos)')
ax1.legend()
ax1.grid(True)

# Gráfico de throughput vs número de cajeros
for tasa_servicio in tasa_servicio_list:
    data = df_resultados[df_resultados['tasa_servicio'] == tasa_servicio]
    ax2.plot(data['num_cajeros'], data['throughput'], marker='o', label=f'Tasa servicio = {1/tasa_servicio:.2f} min')

ax2.set_title('Throughput vs Número de cajeros')
ax2.set_xlabel('Número de cajeros')
ax2.set_ylabel('Throughput (clientes/minuto)')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

# Análisis adicional: Utilización de cajeros
df_resultados['utilizacion'] = df_resultados['tasa_llegada'] / (df_resultados['num_cajeros'] * df_resultados['tasa_servicio'])

print("\nUtilización de cajeros:")
print(df_resultados[['num_cajeros', 'tasa_llegada', 'tasa_servicio', 'utilizacion']])

# Gráfico de utilización vs número de cajeros
plt.figure(figsize=(10, 6))
for tasa_llegada in tasa_llegada_list:
    data = df_resultados[df_resultados['tasa_llegada'] == tasa_llegada]
    plt.plot(data['num_cajeros'], data['utilizacion'], marker='o', label=f'Tasa llegada = {1/tasa_llegada:.2f} min')

plt.title('Utilización de cajeros vs Número de cajeros')
plt.xlabel('Número de cajeros')
plt.ylabel('Utilización')
plt.legend()
plt.grid(True)
plt.show()