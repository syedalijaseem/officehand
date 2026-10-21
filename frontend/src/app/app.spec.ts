import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { routes } from './app.routes';

describe('App shell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('shows the product name', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const brand = fixture.nativeElement.querySelector('[data-testid="brand"]') as HTMLElement;
    expect(brand.textContent).toContain('OfficeHand');
  });

  it('has primary navigation to Inbox and Ask', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const nav = fixture.nativeElement.querySelector('nav[aria-label="Main"]') as HTMLElement;
    const links = Array.from(nav.querySelectorAll('a')).map((a) => ({
      text: a.textContent?.trim(),
      href: a.getAttribute('href'),
    }));
    expect(links).toEqual([
      { text: 'Inbox', href: '/inbox' },
      { text: 'Ask', href: '/ask' },
    ]);
  });

  it('includes a skip link for keyboard users', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const skip = fixture.nativeElement.querySelector('a[href="#main"]') as HTMLElement;
    expect(skip).toBeTruthy();
  });
});
