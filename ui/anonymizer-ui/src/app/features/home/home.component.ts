import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';     // für *ngIf, *ngFor, keyvalue
import { FormsModule } from '@angular/forms';        // für [(ngModel)]
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
  // Form-State (Properties, keine Signals)
  inputText: string = '';
  outputText: string = '';
  isBusy: boolean = false;
  errorMsg: string | null = null;

  // Optional: Mapping anzeigen, falls Backend das liefert
  mapping: Record<string, string> | null = null;

  constructor(private http: HttpClient) {}

  onEncode(): void {
    this.run('/api/encode', this.inputText);
  }

  onDecode(): void {
    this.run('/api/decode', this.inputText);
  }

  copyOutput(): void {
    this.inputText = this.outputText;
  }

  private run(url: string, text: string): void {
    this.isBusy = true;
    this.errorMsg = null;

    this.http.post<AnonymizeResponse>(url, { text })
      .subscribe({
        next: (res) => {
          this.outputText = res.text ?? '';
          this.mapping = res.mapping ?? null;
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
