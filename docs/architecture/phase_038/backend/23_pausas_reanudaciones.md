# 23. Pausas y reanudaciones

Solo puede existir una pausa activa por operación. La pausa guarda motivo, severidad, evidencia y actor/hora. Severidades HIGH/CRITICAL exigen evidencia. Reanudar calcula segundos autoritativos y los acumula; no acepta duración del cliente.

