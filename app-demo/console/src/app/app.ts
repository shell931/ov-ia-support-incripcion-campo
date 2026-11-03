import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  imports: [RouterOutlet, RouterLink],
  selector: 'app-root',
  styleUrl: './app.scss',
  template: `
    <header class="topbar">
      <a routerLink="/" class="brand">Consola de la mesa</a>
      <span class="subtitle">Soporte de campo - inscripción</span>
    </header>
    <main class="content"><router-outlet /></main>
  `,
})
export class App {}
