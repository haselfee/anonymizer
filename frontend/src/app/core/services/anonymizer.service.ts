import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface TextIn {
  text: string;
  // mapping is optional; API accepts ORIGINAL -> TOKEN
  mapping?: Record<string, string>;
}

export interface TextOut {
  text: string;
  // API returns ORIGINAL -> TOKEN
  mapping: Record<string, string>;
}

@Injectable({ providedIn: 'root' })
export class AnonymizerService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  encode(payload: TextIn): Observable<TextOut> {
    // POST /encode
    return this.http.post<TextOut>(`${this.base}/encode`, payload);
  }

  decode(payload: TextIn): Observable<TextOut> {
    // POST /decode
    return this.http.post<TextOut>(`${this.base}/decode`, payload);
  }

  health(): Observable<{ ok: boolean }> {
    return this.http.get<{ ok: boolean }>(`${this.base}/health`);
    }
}
