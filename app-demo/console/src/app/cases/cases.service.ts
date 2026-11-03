import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { CaseDetail, CaseStatus, CaseSummary, CloseReason } from './case.model';

@Injectable({ providedIn: 'root' })
export class CasesService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/cases';

  /** Omitting status returns open and taken cases. */
  list(status?: CaseStatus): Observable<CaseSummary[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    return this.http.get<CaseSummary[]>(this.base, { params });
  }

  get(number: number): Observable<CaseDetail> {
    return this.http.get<CaseDetail>(`${this.base}/${number}`);
  }

  take(number: number, takenBy: string): Observable<CaseDetail> {
    return this.http.post<CaseDetail>(`${this.base}/${number}/take`, { taken_by: takenBy });
  }

  close(number: number, closeReason: CloseReason, notes: string): Observable<CaseDetail> {
    return this.http.post<CaseDetail>(`${this.base}/${number}/close`, {
      close_reason: closeReason,
      notes,
    });
  }
}
