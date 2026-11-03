export type CaseStatus = 'open' | 'taken' | 'closed';
export type CasePriority = 'normal' | 'high';
export type CaseDestination = 'help_desk' | 'census_office' | 'logistics';
export type CloseReason = 'resolved_by_phone' | 'tablet_replaced' | 'sent_to_census' | 'other';

export interface CaseSummary {
  number: number;
  status: CaseStatus;
  priority: CasePriority;
  flow: string;
  flow_description: string;
  destination: CaseDestination;
  phone: string;
  masked_id_number: string | null;
  reason: string;
  taken_by: string | null;
  created_at: string;
  waiting_minutes: number;
}

export interface StepTried {
  id: string;
  text: string;
}

export interface TranscriptLine {
  speaker: 'operator' | 'agent';
  text: string;
}

export interface CaseDetail extends CaseSummary {
  steps_tried: StepTried[];
  transcript: TranscriptLine[];
  close_reason: CloseReason | null;
  notes: string | null;
}
