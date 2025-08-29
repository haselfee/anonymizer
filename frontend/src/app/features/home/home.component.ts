import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';

type AnonymizeResponse = {
  text: string;
  mapping?: Record<string, string>;
};

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './home.component.html',
})
export class HomeComponent {
  text: string = '';                        // Ein einziges Textfeld
  isBusy: boolean = false;
  errorMsg: string | null = null;
  mapping: Record<string, string> | null = null;

  constructor(private http: HttpClient) {}

  onEncode(): void { this.run('/api/encode', this.text); }
  onDecode(): void { this.run('/api/decode', this.text); }

  private run(url: string, text: string): void {
    this.isBusy = true;
    this.errorMsg = null;

    this.http.post<AnonymizeResponse>(url, { text })
      .subscribe({
        next: (res) => {
          this.text = res.text ?? '';              // Ergebnis überschreibt den Inhalt
          this.mapping = res.mapping ?? null;      // optional anzeigen
          this.isBusy = false;
        },
        error: (err) => {
          console.error(err);
          this.errorMsg = 'Fehler beim Aufruf der API.';
          this.isBusy = false;
        }
      });
  }
}
