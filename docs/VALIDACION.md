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
| L7 | 8.8 cm | Se tomaba del tobillo de MediaPipe; el marcador (tarso) está ~8.7 cm más abajo (ver nota) |

En casi todos los puntos con error alto el sesgo es casi igual al error medio: el error
es sistemático y se puede corregir ajustando las proporciones.

Tablas: ángulos de hombros 0.9°, pelvis 1.9°, rodillas 2.6°; distancias frontales y
posteriores 0.5–1.1 cm. **Varo/valgo del pie (9–12°) y rotación del pie (4–7°) no son
confiables** con detección automática (ángulos entre puntos muy cercanos): requieren
ajuste manual.

### Ajuste de los puntos con los datos reales

Con `poses.json` se ajustó, para cada punto, un desplazamiento desde su ancla de MediaPipe
proporcional al tamaño del cuerpo (ancho de hombros y largo del tronco en las vistas
frontales; largo del muslo en la lateral). Reglas:

- Los pares bilaterales usan el mismo desplazamiento en espejo (un paciente simétrico sigue
  saliendo alineado). Corregir solo un lado empeoraba los ángulos de rodillas de 2.6° a 5.4°.
- Se corrige un punto (o un par) solo si mejora al menos 0.2 cm en validación cruzada.
- Los puntos de la línea media no tienen desplazamiento horizontal.
- Validación cruzada dejando una persona fuera (el ajuste nunca ve a la persona evaluada).

| | Antes | Después (validación cruzada) |
|---|---|---|
| Error medio de los 33 puntos | 3.7 cm | **1.9 cm** |
| Hombros (F3/F4/P3/P4/L2) | 4.2–5.5 cm | 1.0–2.6 cm |
| C7 / T5 | 5.4 / 8.4 cm | 1.9 / 2.8 cm |
| EIAS frontales / EIPS | 4.8–6.2 cm | 2.2–2.6 cm |
| L7 (tarso) | 9.3 cm | 1.5 cm |
| Distancias laterales a la plomada | 4–8 cm | 1–2 cm (dirección coincide 80–100 %) |
| Ángulo rodilla-pies | 7.8° | 1.3° |

Siguen sin ser fiables en modo automático y requieren ajuste manual: la inclinación
pélvica lateral (≈6°, por lo tanto la clasificación de la postura), varo/valgo y rotación
del pie, y los ángulos de pelvis y rodillas frontales (2–3°). Los coeficientes están en
`backend/app/lam/pose.py`; `backend/validation/ajustar_poses.py` los recalcula cuando haya
más pacientes con marcadores, y `tests/test_pose_validation.py` (`-m fotos`) evita que el
error vuelva a subir.

### Escala: la silueta es correcta, la escala de los marcadores no siempre

La estatura según la silueta supera a la real en 6–7 % de media (de −0.5 % a +20 %). Al
dibujar el vértice y el suelo detectados sobre las fotos, ambos caen en su lugar (parte
superior de la cabeza y plantas). La diferencia viene de la **escala de los marcadores**:
R1/R2 están en el suelo junto a la pared, detrás del paciente, y lo que está más lejos de
la cámara se ve más pequeño. Con el paciente unos 40–50 cm delante de la pared (FR), la
escala se infla ~20 %; con el paciente pegado a la pared (JE), la diferencia es −0.5 %.

Consecuencias:

1. En el método con marcadores, **las distancias en cm pueden estar infladas hasta un 20 %**
   según dónde se pare el paciente. Los ángulos no se ven afectados.
2. Protocolo recomendado para el modo con marcadores: colocar R1 y R2 en el mismo plano que
   el paciente (a sus costados, como describe el README), no en la pared.
3. La escala por estatura del modo sin marcadores no tiene este problema.
