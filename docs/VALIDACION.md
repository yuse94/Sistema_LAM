# Validación con fotografías reales

Fotos usadas (no están en el repositorio porque contienen pacientes identificables):

- `Pruebas_adultos/`: 10 adultos con 4 vistas cada uno, con marcadores verdes y las
  referencias R1/R2 en el suelo. Hay dos sesiones de fotos (salas y cámaras distintas).
- `tipos_de_postura/`: 6 ilustraciones de posturas sagitales con marcadores (ideal,
  cabeza adelante, cifolordótica, lordótica, espalda plana y espalda arqueada).

Pruebas automáticas: `uv run pytest -m fotos` (≈3 min).

## 1. Detector de marcadores

| | Umbral fijo 0.32 (consola) | Umbral automático |
|---|---|---|
| Fotos procesadas | 12 de 40 | **40 de 40** |

- Ningún umbral fijo sirve para todas: CZ necesita 0.32 y la mayoría de la otra sesión
  0.20–0.24 (depende de la iluminación). Ahora, si el umbral configurado no da la
  cantidad esperada de marcadores, el sistema busca otro valor (centro del rango de
  umbrales que funcionan) y lo informa en los resultados. Se puede desactivar en
  Configuración.
- Se revisaron visualmente las 30 fotos reales: todos los puntos quedan asignados a su
  punto anatómico.
- La escala (cm/píxel) es consistente entre las vistas de cada persona: diferencia
  máxima 3.8 % (CZ), el resto por debajo de 1.5 %.

**Las laterales izquierdas no son fotos reales.** Las 10 tienen exactamente los mismos
píxeles que su lateral derecha, con la marca EXIF "reflejar horizontalmente". Sirven para
comprobar que la app maneja el espejo (los resultados coinciden con la derecha), pero no
validan la anatomía de la vista izquierda. Para eso hacen falta fotos tomadas del lado
izquierdo.

## 2. Clasificación de la postura lateral (tipos_de_postura)

| Tolerancia | Posturas bien clasificadas |
|---|---|
| 0° y 0 cm (valor de la consola) | 5 de 6: "cabeza adelante" sale "Pelvis en posición normal" |
| 0.5°–2° y 0.5–1 cm | **6 de 6** |
| 3° y 2 cm | 5 de 6 |
| 5° y 3 cm | 4 de 6 |

Con tolerancia 0 una desviación de un píxel (0.01°) cuenta como "anterior" y descarta la
regla de "cabeza hacia delante". **Decisión:** tolerancias por defecto de 1° y 0.5 cm.

## 3. Errores heredados encontrados con las fotos

- **HALLAZGO-7 (corregido): el ángulo pélvico lateral perdía el signo.** La consola usaba
  `180 − |ángulo|`; una retroversión de 20° (EIAS más alta que la EIPS) se informaba como
  anteversión de 20°, y una de 10° como "Normal". Ahora el ángulo tiene signo (positivo =
  EIAS más baja). Caso real: CZ tiene −9.1°; antes habría salido +9.1° "Normal", ahora
  "Pos." y la postura cambia a "Espalda plana".
- **L3 y L4 estaban invertidos en los nombres.** La Tabla 2.1 de la tesis define L3 = EIAS y
  L4 = EIPS; la versión de consola (y el portado hasta ahora) los nombraba al revés. Los
  cálculos no cambian, pero el editor y el diccionario ahora muestran cada nombre sobre la
  espina correcta.

## 4. Modo sin marcadores: MediaPipe contra marcadores

Script: `backend/validation/markerless.py`. Compara, en las mismas 30 fotos y con la misma
escala, los puntos de MediaPipe (y los estimados por proporciones) contra los marcadores.

```powershell
cd backend
uv run validation/markerless.py --estaturas validation/estaturas.csv
```

Resultados en `validation/resultados/` (excluido de git): `resumen.md`, `puntos.csv`,
`tablas.csv`, `poses.json` (coordenadas de MediaPipe, sin imágenes) e `imagenes/`.

### Primera ejecución (proporciones iniciales, sin ajustar)

| Grupo de puntos | Error medio | Observación |
|---|---|---|
| Tobillos, dedos, talones, rodillas (MediaPipe) | 1–2.5 cm | Bueno. F11/F12 (línea media frontal) ≈ 1 cm |
| Entrecejo, mentón, ombligo (estimados) | 1–2 cm | Bueno |
| Hombros F3/F4/P3/P4/L2 (MediaPipe) | 4–5.5 cm | Sesgo fijo: MediaPipe marca el centro articular, ~4 cm más abajo y medial que la acromioclavicular |
| Horquilla, C7, T5, EIPS, EIAS (estimados) | 4–8 cm | Sesgo fijo hacia abajo (+4 a +8 cm) |
| L7 | 8.8 cm | El marcador de estas fotos está ~8.7 cm más abajo que el tobillo de MediaPipe (ver nota) |

En casi todos los puntos con error alto el sesgo es casi igual al error medio: el error
es sistemático y se puede corregir ajustando las proporciones.

Tablas: ángulos de hombros 0.9°, pelvis 1.9°, rodillas 2.6°; distancias frontales y
posteriores 0.5–1.1 cm. **Varo/valgo del pie (9–12°) y rotación del pie (4–7°) no son
confiables** con detección automática (ángulos entre puntos muy cercanos): requieren
ajuste manual.

Estatura según la silueta: +6–7 % en promedio frente a la estatura real (de −0.5 % a
+20 %). Parte de la diferencia se debe a que R1/R2 están en el suelo junto a la pared,
detrás del paciente: la escala de los marcadores corresponde a un plano más lejano y
también infla las medidas en cm del método original. No afecta a los ángulos.

**Nota sobre L7:** en estas fotos el marcador L7 parece estar colocado según el protocolo
de la tesis (articulación transversal del tarso) y no en el maléolo externo, por lo que su
error no es representativo de la nueva definición.

**Siguiente paso:** ajustar las proporciones de los puntos estimados y una corrección de
los hombros con `poses.json`, validando con "dejar una persona fuera".
