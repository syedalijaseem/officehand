import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-inbox-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="text-4xl font-semibold">Inbox</h1>
    <p class="mt-3 max-w-xl text-lg text-ink-muted">
      New emails will appear here, ready for you to check and approve.
    </p>
  `,
})
export class InboxPage {}
