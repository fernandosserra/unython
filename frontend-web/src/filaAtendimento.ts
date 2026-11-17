import type { Agendamento } from './types';

export function proximoDaFila(fila: Agendamento[]): Agendamento | undefined {
  return fila.reduce<Agendamento | undefined>((proximo, item) => {
    if (item.status !== 'Aguardando') return proximo;
    if (!proximo) return item;
    if (item.preferencial !== proximo.preferencial) return item.preferencial ? item : proximo;
    if (item.ordem_chegada !== proximo.ordem_chegada) {
      return item.ordem_chegada < proximo.ordem_chegada ? item : proximo;
    }
    if (item.data_hora !== proximo.data_hora) return item.data_hora < proximo.data_hora ? item : proximo;
    return item.id < proximo.id ? item : proximo;
  }, undefined);
}
