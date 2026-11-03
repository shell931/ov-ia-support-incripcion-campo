import { CaseDestination, CasePriority, CaseStatus, CloseReason } from '../cases/case.model';

export const DESTINATION_LABELS: Record<CaseDestination, string> = {
  help_desk: 'Mesa de ayuda',
  census_office: 'Dirección de Censo',
  logistics: 'Logística',
};

export const PRIORITY_LABELS: Record<CasePriority, string> = {
  high: 'ALTA',
  normal: 'normal',
};

export const STATUS_LABELS: Record<CaseStatus, string> = {
  open: 'Abierto',
  taken: 'Tomado',
  closed: 'Cerrado',
};

export const CLOSE_REASON_LABELS: Record<CloseReason, string> = {
  resolved_by_phone: 'Resuelto por teléfono',
  tablet_replaced: 'Tableta reemplazada',
  sent_to_census: 'Enviado a Dirección de Censo',
  other: 'Otro',
};

export const CLOSE_REASONS = Object.keys(CLOSE_REASON_LABELS) as CloseReason[];

export function formatWaiting(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}
