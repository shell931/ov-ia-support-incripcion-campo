import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { CasesService } from './cases.service';

describe('CasesService', () => {
  let service: CasesService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CasesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists without status param by default', () => {
    service.list().subscribe();
    const req = http.expectOne((r) => r.url === '/api/cases');
    expect(req.request.params.has('status')).toBe(false);
    req.flush([]);
  });

  it('lists closed cases with status param', () => {
    service.list('closed').subscribe();
    const req = http.expectOne((r) => r.url === '/api/cases');
    expect(req.request.params.get('status')).toBe('closed');
    req.flush([]);
  });

  it('takes a case sending taken_by', () => {
    service.take(7, 'Ana').subscribe();
    const req = http.expectOne('/api/cases/7/take');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ taken_by: 'Ana' });
    req.flush({});
  });

  it('closes a case sending reason and notes', () => {
    service.close(7, 'tablet_replaced', 'ok').subscribe();
    const req = http.expectOne('/api/cases/7/close');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ close_reason: 'tablet_replaced', notes: 'ok' });
    req.flush({});
  });
});
