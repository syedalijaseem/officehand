import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { HomePage } from './home-page';

describe('HomePage', () => {
  it('offers the two workflows as primary actions', async () => {
    await TestBed.configureTestingModule({
      imports: [HomePage],
      providers: [provideRouter([])],
    }).compileComponents();

    const fixture = TestBed.createComponent(HomePage);
    await fixture.whenStable();

    const actions = Array.from(
      fixture.nativeElement.querySelectorAll(
        '[data-testid="workflow-card"]',
      ) as NodeListOf<HTMLAnchorElement>,
    );
    expect(actions.map((a) => a.getAttribute('href'))).toEqual(['/inbox', '/ask']);
    expect(actions[0].textContent).toContain('Inbox');
    expect(actions[1].textContent).toContain('Ask');
  });
});
