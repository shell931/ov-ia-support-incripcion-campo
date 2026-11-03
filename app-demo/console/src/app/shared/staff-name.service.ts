import { Injectable, signal } from '@angular/core';

const KEY = 'console.staffName';

/** Demo-only identity: the name is kept in localStorage, no login. */
@Injectable({ providedIn: 'root' })
export class StaffNameService {
  readonly name = signal<string | null>(this.read());

  set(value: string): void {
    const clean = value.trim();
    if (!clean) return;
    this.name.set(clean);
    try {
      localStorage.setItem(KEY, clean);
    } catch {
      // storage unavailable: keep in memory only
    }
  }

  private read(): string | null {
    try {
      return localStorage.getItem(KEY);
    } catch {
      return null;
    }
  }
}
