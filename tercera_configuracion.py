import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class BancoExpressRegular:
    def __init__(self, env, num_cajeros_express, num_cajeros_regulares, tasa_llegada, tasa_servicio_express, tasa_servicio_regular, prob_cliente_express):
        self.env = env
        self.cajeros_express = simpy.Resource(env, num_cajeros_express)
        self.cajeros_regulares = simpy.Resource(env, num_cajeros_regulares)
        self.tasa_llegada = tasa_llegada
        self.tasa_servicio_express = tasa_servicio_express
        self.tasa_servicio_regular = tasa_servicio_regular
        self.prob_cliente_express = prob_cliente_express
        self.tiempos_espera = []
        self.tiempos_sistema = []
        self.tipo_cliente = []

    def llegada_cliente(self):
        while True:
            yield self.env.timeout(random.expovariate(self.tasa_llegada))
            if random.random() < self.prob_cliente_express:
                self.env.process(self.atencion_cliente(self.cajeros_express, self.tasa_servicio_express, "Express"))
            else:
                self.env.process(self.atencion_cliente(self.cajeros_regulares, self.tasa_servicio_regular, "Regular"))

    def atencion_cliente(self, cajeros, tasa_servicio, tipo):
        llegada = self.env.now
        with cajeros.request() as req:
            yield req
            espera = self.env.now - llegada
            self.tiempos_espera.append(espera)
            tiempo_servicio = random.expovariate(tasa_servicio)
            yield self.env.timeout(tiempo_servicio)
            self.tiempos_sistema.append(self.env.now - llegada)
            self.tipo_cliente.append(tipo)

def ejecutar_simulacion_express_regular(num_cajeros_express, num_cajeros_regulares, tasa_llegada, tasa_servicio_express, tasa_servicio_regular, prob_cliente_express, tiempo_simulacion):
    env = simpy.Environment()
    banco = BancoExpressRegular(env, num_cajeros_express, num_cajeros_regulares, tasa_llegada, tasa_servicio_express, tasa_servicio_regular, prob_cliente_express)
    env.process(banco.llegada_cliente())
    env.run(until=tiempo_simulacion)
    return banco

# Función para ejecutar experimentos
def ejecutar_experimentos(num_cajeros_express_list, num_cajeros_regulares_list, tasa_llegada_list, tasa_servicio_express_list, tasa_servicio_regular_list, prob_cliente_express_list):
    resultados = []
    tiempo_simulacion = 480  # 8 horas
    for num_cajeros_express in num_cajeros_express_list:
        for num_cajeros_regulares in num_cajeros_regulares_list:
            for tasa_llegada in tasa_llegada_list:
                for tasa_servicio_express in tasa_servicio_express_list:
                    for tasa_servicio_regular in tasa_servicio_regular_list:
                        for prob_cliente_express in prob_cliente_express_list:
                            banco = ejecutar_simulacion_express_regular(
                                num_cajeros_express, num_cajeros_regulares, tasa_llegada,
                                tasa_servicio_express, tasa_servicio_regular, prob_cliente_express, tiempo_simulacion
                            )
                            tiempo_espera_promedio = np.mean(banco.tiempos_espera)
                            tiempo_sistema_promedio = np.mean(banco.tiempos_sistema)
                            throughput = len(banco.tiempos_sistema) / tiempo_simulacion
                            tiempo_espera_express = np.mean([t for t, tipo in zip(banco.tiempos_espera, banco.tipo_cliente) if tipo == "Express"])
                            tiempo_espera_regular = np.mean([t for t, tipo in zip(banco.tiempos_espera, banco.tipo_cliente) if tipo == "Regular"])
                            resultados.append({
                                'num_cajeros_express': num_cajeros_express,
                                'num_cajeros_regulares': num_cajeros_regulares,
                                'tasa_llegada': tasa_llegada,
                                'tasa_servicio_express': tasa_servicio_express,
                                'tasa_servicio_regular': tasa_servicio_regular,
                                'prob_cliente_express': prob_cliente_express,
                                'tiempo_espera_promedio': tiempo_espera_promedio,
                                'tiempo_sistema_promedio': tiempo_sistema_promedio,
                                'throughput': throughput,
                                'tiempo_espera_express': tiempo_espera_express,
                                'tiempo_espera_regular': tiempo_espera_regular
                            })
    return pd.DataFrame(resultados)

# Parámetros para los experimentos
num_cajeros_express_list = [1, 2]
num_cajeros_regulares_list = [2, 3]
tasa_llegada_list = [1/4, 1/3]
tasa_servicio_express_list = [1/2, 1/1.5]
tasa_servicio_regular_list = [1/4, 1/3]
prob_cliente_express_list = [0.3, 0.5]

# Ejecutar experimentos
df_resultados = ejecutar_experimentos(
    num_cajeros_express_list, num_cajeros_regulares_list, tasa_llegada_list,
    tasa_servicio_express_list, tasa_servicio_regular_list, prob_cliente_express_list
)

# Imprimir resultados
print(df_resultados)

# Gráficos
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# Gráfico de tiempo de espera promedio vs número total de cajeros
df_resultados['total_cajeros'] = df_resultados['num_cajeros_express'] + df_resultados['num_cajeros_regulares']
for tasa_llegada in tasa_llegada_list:
    data = df_resultados[df_resultados['tasa_llegada'] == tasa_llegada]
    ax1.plot(data['total_cajeros'], data['tiempo_espera_promedio'], marker='o', label=f'Tasa llegada = {1/tasa_llegada:.2f} min')

ax1.set_title('Tiempo de espera promedio vs Número total de cajeros')
ax1.set_xlabel('Número total de cajeros')
ax1.set_ylabel('Tiempo de espera promedio (minutos)')
ax1.legend()
ax1.grid(True)

# Gráfico de tiempo de espera express vs regular
ax2.scatter(df_resultados['tiempo_espera_express'], df_resultados['tiempo_espera_regular'])
ax2.set_title('Tiempo de espera: Express vs Regular')
ax2.set_xlabel('Tiempo de espera Express (minutos)')
ax2.set_ylabel('Tiempo de espera Regular (minutos)')
ax2.plot([0, max(df_resultados['tiempo_espera_express'].max(), df_resultados['tiempo_espera_regular'].max())],
         [0, max(df_resultados['tiempo_espera_express'].max(), df_resultados['tiempo_espera_regular'].max())],
         'r--', label='Línea de igualdad')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

# Análisis adicional: Eficiencia del sistema express
df_resultados['eficiencia_express'] = df_resultados['tiempo_espera_regular'] / df_resultados['tiempo_espera_express']

plt.figure(figsize=(10, 6))
plt.scatter(df_resultados['prob_cliente_express'], df_resultados['eficiencia_express'])
plt.title('Eficiencia del sistema express vs Probabilidad de cliente express')
plt.xlabel('Probabilidad de cliente express')
plt.ylabel('Eficiencia (Tiempo espera regular / Tiempo espera express)')
plt.grid(True)
plt.show()

print("\nEstadísticas de eficiencia del sistema express:")
print(df_resultados['eficiencia_express'].describe())