# 24. Aborto operativo

Solo una descarga iniciada o pausada puede abortarse. Una pausa activa se cierra en servidor, la operación queda `ABORTED` y la asignación `RELEASE_PENDING`. El muelle no se libera implícitamente: se exige una acción posterior con motivo.

