import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

interface WorkflowCard {
  readonly route: string;
  readonly title: string;
  readonly kicker: string;
  readonly description: string;
}

@Component({
  selector: 'app-home-page',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section aria-labelledby="home-heading" class="max-w-3xl">
      <p class="text-sm font-semibold tracking-[0.18em] text-spruce uppercase">
        Your office, with a second pair of hands
      </p>
      <h1 id="home-heading" class="mt-3 text-4xl leading-[1.05] font-semibold sm:text-6xl">
        Less typing. Fewer surprises.
        <span class="text-ink-muted">Nothing happens without your OK.</span>
      </h1>
    </section>

    <div class="mt-12 grid gap-5 sm:grid-cols-[1.15fr_1fr]">
      @for (card of cards; track card.route; let first = $first) {
        <a
          [routerLink]="card.route"
          data-testid="workflow-card"
          class="group relative flex flex-col justify-between overflow-hidden rounded-[var(--radius-card)] border border-rule p-7 shadow-[var(--shadow-card)] transition-[transform,box-shadow] duration-300 ease-[var(--ease-out-expo)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-hover)] active:translate-y-0"
          [class]="
            first
              ? 'bg-spruce text-paper-raised border-spruce-strong min-h-64'
              : 'bg-paper-raised min-h-64'
          "
        >
          <div>
            <p
              class="text-sm font-semibold tracking-wide uppercase"
              [class]="first ? 'text-spruce-wash' : 'text-spruce'"
            >
              {{ card.kicker }}
            </p>
            <h2 class="mt-2 text-3xl font-semibold">{{ card.title }}</h2>
            <p
              class="mt-3 max-w-md text-lg"
              [class]="first ? 'text-spruce-wash' : 'text-ink-muted'"
            >
              {{ card.description }}
            </p>
          </div>
          <span
            aria-hidden="true"
            class="mt-8 inline-flex items-center gap-2 font-semibold transition-transform duration-300 ease-[var(--ease-out-expo)] group-hover:translate-x-1"
            >Open {{ card.title }} →</span
          >
        </a>
      }
    </div>
  `,
})
export class HomePage {
  protected readonly cards: readonly WorkflowCard[] = [
    {
      route: '/inbox',
      title: 'Inbox',
      kicker: 'Emails → tracker',
      description:
        'Invoices, change orders and sub updates, read and filled in for you to check and approve.',
    },
    {
      route: '/ask',
      title: 'Ask',
      kicker: 'Project documents',
      description: 'Ask about contracts, specs and schedules. Every answer shows the exact source.',
    },
  ];
}
