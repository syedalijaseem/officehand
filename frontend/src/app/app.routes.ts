import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'OfficeHand',
    loadComponent: () => import('./home/home-page').then((m) => m.HomePage),
  },
  {
    path: 'inbox',
    title: 'Inbox · OfficeHand',
    loadComponent: () => import('./inbox/inbox-page').then((m) => m.InboxPage),
  },
  {
    path: 'ask',
    title: 'Ask · OfficeHand',
    loadComponent: () => import('./ask/ask-page').then((m) => m.AskPage),
  },
  { path: '**', redirectTo: '' },
];
