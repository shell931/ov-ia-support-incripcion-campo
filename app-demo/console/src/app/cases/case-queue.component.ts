import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { catchError, of, switchMap, tap, timer } from 'rxjs';
import { DESTINATION_LABELS, PRIORITY_LABELS, STATUS_LABELS, formatWaiting } from '../shared/labels';
import { CaseSummary } from './case.model';
import { CasesService } from './cases.service';

type Tab = 'open' | 'closed';
const POLL_MS = 5000;

@Component({
  selector: 'app-case-queue',
  templateUrl: './case-queue.component.html',
  styleUrl: './case-queue.component.scss',
})
export class CaseQueueComponent {
  private readonly cases = inject(CasesService);
  private readonly router = inject(Router);

  protected readonly tab = signal<Tab>('open');
  protected readonly items = signal<CaseSummary[]>([]);
  protected readonly loaded = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly destinations = DESTINATION_LABELS;
  protected readonly priorities = PRIORITY_LABELS;
  protected readonly statuses = STATUS_LABELS;
  protected readonly formatWaiting = formatWaiting;

  constructor() {
    // Restarts the polling timer whenever the tab changes; unsubscribes on destroy.
    toObservable(this.tab)
      .pipe(
        tap(() => this.loaded.set(false)),
        switchMap((tab) =>
          timer(0, POLL_MS).pipe(
            switchMap(() =>
              this.cases.list(tab === 'closed' ? 'closed' : undefined).pipe(
                tap(() => this.error.set(null)),
                catchError(() => {
                  this.error.set('No se pudo actualizar la cola. Reintentando...');
                  return of(null);
                }),
              ),
            ),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((data) => {
        if (data) this.items.set(data);
        this.loaded.set(true);
      });
  }

  protected select(tab: Tab): void {
    if (tab === this.tab()) return;
    this.items.set([]);
    this.tab.set(tab);
  }

  protected open(c: CaseSummary): void {
    this.router.navigate(['/cases', c.number]);
  }
}
