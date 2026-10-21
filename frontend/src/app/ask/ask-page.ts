import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-ask-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="text-4xl font-semibold">Ask</h1>
    <p class="mt-3 max-w-xl text-lg text-ink-muted">
      Ask a question about your project documents. Every answer shows where it came from.
    </p>
  `,
})
export class AskPage {}
