import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./cases/case-queue.component').then((m) => m.CaseQueueComponent),
  },
  {
    path: 'cases/:number',
    loadComponent: () => import('./cases/case-detail.component').then((m) => m.CaseDetailComponent),
  },
  { path: '**', redirectTo: '' },
];
