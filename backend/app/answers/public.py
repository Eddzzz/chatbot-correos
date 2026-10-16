from app.contracts import ChatResponse, Evidence
from app.data_access.public import QueryResult

def compose_answer(request_id: str, session_id: str, result: QueryResult) -> ChatResponse:
    if not result.rows and result.truncated:
        answer = 'La ficha supera el límite de respuesta y no fue posible mostrarla completa. Consulta los datos resumidos o acota los registros a una sucursal o un código.'
    elif not result.rows:
        answer = 'No se encontraron registros para esos filtros dentro del alcance autorizado.'
    else:
        first = result.rows[0]
        if 'details' in first:
            answer = f'Ficha y datos asociados: {len(result.rows)} ' + ('sucursal' if 'office_id' in first and len(result.rows) == 1 else 'sucursales' if 'office_id' in first else 'registro de seguimiento' if len(result.rows) == 1 else 'registros de seguimiento') + '. Se muestran los campos y relaciones disponibles del respaldo, incluidos datos personales autorizados. Las secciones indican si una relación está vacía o limitada. Contraseñas, tokens y archivos binarios no se incluyen.'
            if 'office_id' in first:
                answer += ' Más abajo encontrarás el personal, los envíos y las demás categorías relacionadas que estén disponibles. Cada categoría explica cuántos registros tiene y permite consultar sus detalles. Algunos datos aparecen solo como referencia y no indican que la operación se haya realizado en esta sucursal.'
        elif 'tracking_code' in first:
            if len(result.rows) == 1:
                answer = f'El registro {first["tracking_code"]} de la familia {first.get("source") or "sin dato"} figura con el estado «{first.get("status") or "sin dato"}».'
                if first.get('destination'):
                    answer += f' Su destino registrado es {first["destination"]}.'
            else:
                answer = f'Encontré {len(result.rows)} registros para el código {first["tracking_code"]}. Revisa sus familias y estados en la tabla; pueden representar registros relacionados.'
        elif 'office_id' in first:
            answer = f'Encontré {len(result.rows)} ' + ('sucursal' if len(result.rows) == 1 else 'sucursales') + ' para los filtros indicados. La tabla muestra el municipio, departamento y teléfono institucional disponibles; no hay horarios ni direcciones en esta fuente.'
        elif 'total' in first:
            answer = (f'La consulta devuelve {sum(row["total"] for row in result.rows)} registros, distribuidos en {len(result.rows)} grupos. Consulta el desglose en la tabla.'
                      if not result.truncated else 'La tabla muestra un desglose parcial por grupos.')
        else:
            answer = f'Encontré {len(result.rows)} registros autorizados. Consulta los datos disponibles en la tabla.'
    if 'DEMOSTRACIÓN' in result.source:
        answer = 'Demostración con datos ficticios.\n' + answer
    if result.truncated:
        answer += '\nResultado parcial limitado. Los grupos y registros mostrados no representan el total completo. Ajusta los filtros.'
    return ChatResponse(request_id=request_id, session_id=session_id, status='answer' if result.rows else 'needs_clarification' if result.truncated else 'no_results', answer=answer, evidence=[Evidence(source=result.source, queried_at=result.queried_at, row_count=len(result.rows), truncated=result.truncated)], rows=result.rows, columns=list(result.rows[0]) if result.rows else [], source=result.source, queried_at=result.queried_at)
