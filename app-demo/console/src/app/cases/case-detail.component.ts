import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, numberAttribute, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  CLOSE_REASONS,
  CLOSE_REASON_LABELS,
  DESTINATION_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
  formatWaiting,
} from '../shared/labels';
import { StaffNameService } from '../shared/staff-name.service';
import { CaseDetail, CloseReason } from './case.model';
import { CasesService } from './cases.service';

@Component({
  selector: 'app-case-detail',
  imports: [FormsModule, RouterLink],
  templateUrl: './case-detail.component.html',
  styleUrl: './case-detail.component.scss',
})
export class CaseDetailComponent {
  private readonly cases = inject(CasesService);
  private readonly staff = inject(StaffNameService);

  /** Bound from the :number route param (withComponentInputBinding). */
  readonly number = input.required({ transform: numberAttribute });

  protected readonly detail = signal<CaseDetail | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly busy = signal(false);

  protected readonly askName = signal(false);
  protected nameDraft = '';
  protected closeReason: CloseReason = 'resolved_by_phone';
  protected notes = '';

  protected readonly lastStep = computed(() => (this.detail()?.steps_tried.length ?? 0) - 1);

  protected readonly destinations = DESTINATION_LABELS;
  protected readonly priorities = PRIORITY_LABELS;
  protected readonly statuses = STATUS_LABELS;
  protected readonly closeLabels = CLOSE_REASON_LABELS;
  protected readonly closeReasons = CLOSE_REASONS;
  protected readonly formatWaiting = formatWaiting;

  constructor() {
    effect(() => this.load(this.number()));
  }

  private load(number: number): void {
    this.loading.set(true);
    this.error.set(null);
    this.cases.get(number).subscribe({
      next: (d) => {
        this.detail.set(d);
        this.loading.set(false);
      },
      error: (e) => {
        this.detail.set(null);
        this.loading.set(false);
        this.error.set(
          e instanceof HttpErrorResponse && e.status === 404
            ? 'El caso no existe.'
            : this.message(e),
        );
      },
    });
  }

  protected take(): void {
    const name = this.staff.name();
    if (!name) {
      this.askName.set(true);
      return;
    }
    this.send(this.cases.take(this.number(), name));
  }

  protected confirmName(): void {
    this.staff.set(this.nameDraft);
    if (!this.staff.name()) return;
    this.askName.set(false);
    this.take();
  }

  protected close(): void {
    this.send(this.cases.close(this.number(), this.closeReason, this.notes.trim()));
  }

  private send(request: ReturnType<CasesService['take']>): void {
    this.busy.set(true);
    this.error.set(null);
    request.subscribe({
      next: (d) => {
        this.detail.set(d);
        this.busy.set(false);
      },
      error: (e) => {
        this.busy.set(false);
        this.error.set(this.message(e));
        // Refresh so the screen reflects who actually holds the case.
        this.cases.get(this.number()).subscribe({ next: (d) => this.detail.set(d), error: () => {} });
      },
    });
  }

  private message(e: unknown): string {
    if (e instanceof HttpErrorResponse) {
      // The API speaks English (code); the screen speaks Spanish (content).
      const detail: unknown = e.error?.detail;
      if (typeof detail === 'string') {
        const takenBy = /^case already taken by (.+)$/.exec(detail);
        if (takenBy) return `Este caso ya lo tomó ${takenBy[1]}.`;
        if (detail === 'case is already closed') return 'Este caso ya está cerrado.';
        if (detail === 'case not found') return 'El caso no existe.';
      }
      if (e.status === 0) return 'No hay conexión con el servidor.';
    }
    return 'Ocurrió un error inesperado. Intente de nuevo.';
  }
}
