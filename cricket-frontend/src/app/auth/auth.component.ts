import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Output } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { AuthService } from '../auth.service';

function passwordsMatchFn(group: AbstractControl): ValidationErrors | null {
  const p = group.get('password')?.value;
  const c = group.get('confirmPassword')?.value;
  if (p == null || c == null || c === '') return null;
  return p === c ? null : { passwordMismatch: true };
}

@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.css'],
})
export class AuthComponent {
  @Output() done = new EventEmitter<void>();

  /** true = login card only; false = register card */
  showLogin = true;

  showLoginPassword = false;
  showRegPassword = false;
  showRegPassword2 = false;

  loginError: string | null = null;
  registerError: string | null = null;
  submitting = false;

  loginForm = this.fb.group({
    identifier: ['', [Validators.required]],
    password: ['', [Validators.required]],
  });

  registerForm = this.fb.group(
    {
      username: ['', [Validators.required, Validators.maxLength(150)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]],
      terms: [false, [Validators.requiredTrue]],
    },
    { validators: [passwordsMatchFn] },
  );

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
  ) {}

  switchToRegister(): void {
    this.showLogin = false;
    this.loginError = null;
  }

  switchToLogin(): void {
    this.showLogin = true;
    this.registerError = null;
  }

  submitLogin(): void {
    this.loginError = null;
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }
    const v = this.loginForm.getRawValue();
    this.submitting = true;
    this.auth.login(String(v.identifier ?? '').trim(), String(v.password ?? '')).subscribe({
      next: () => {
        this.submitting = false;
        this.done.emit();
      },
      error: (err: HttpErrorResponse) => {
        this.submitting = false;
        const d = err.error;
        if (d instanceof Event) {
          this.loginError =
            err.status === 0
              ? 'Cannot reach the server. Check that the API is running and the URL is correct.'
              : 'Login failed. Please try again.';
          return;
        }
        this.loginError =
          (typeof d === 'string' ? d : null) ||
          (d && typeof d === 'object' && 'detail' in d && typeof (d as { detail?: unknown }).detail === 'string'
            ? (d as { detail: string }).detail
            : null) ||
          (d && typeof d === 'object' && Array.isArray((d as { non_field_errors?: unknown }).non_field_errors)
            ? (d as { non_field_errors: string[] }).non_field_errors[0]
            : null) ||
          'Login failed. Check your details and try again.';
      },
    });
  }

  submitRegister(): void {
    this.registerError = null;
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }
    const r = this.registerForm.getRawValue();
    this.submitting = true;
    this.auth
      .register({
        username: String(r.username ?? '').trim(),
        email: String(r.email ?? '').trim(),
        password: String(r.password ?? ''),
      })
      .subscribe({
        next: () => {
          this.submitting = false;
          this.done.emit();
        },
        error: (err: HttpErrorResponse) => {
          this.submitting = false;
          const d = err.error;
          // Network/CORS failures often put a browser Event/ProgressEvent here —
          // Object.entries would surface "isTrusted: true" as the message.
          if (d instanceof Event) {
            this.registerError =
              err.status === 0
                ? 'Cannot reach the server. Check that the API is running and the URL is correct.'
                : 'Registration failed. Please try again.';
            return;
          }
          if (typeof d === 'string') {
            this.registerError = d;
            return;
          }
          if (d && typeof d === 'object' && !Array.isArray(d)) {
            const body = d as Record<string, unknown>;
            const detail = body['detail'];
            if (typeof detail === 'string') {
              this.registerError = detail;
              return;
            }
            const nfe = body['non_field_errors'];
            if (Array.isArray(nfe) && nfe.length && typeof nfe[0] === 'string') {
              this.registerError = nfe[0];
              return;
            }
            const parts = Object.entries(body)
              .map(([k, v]) => {
                const msg = Array.isArray(v) ? v[0] : v;
                if (msg == null || typeof msg === 'object') return null;
                return `${k}: ${String(msg)}`;
              })
              .filter((s): s is string => !!s)
              .join(' ');
            this.registerError = parts || 'Registration failed.';
            return;
          }
          this.registerError = 'Registration failed.';
        },
      });
  }

  regFieldError(name: string): string | null {
    const c = this.registerForm.get(name);
    if (!c || !c.touched || !c.errors) return null;
    if (c.errors['required']) return 'Required';
    if (c.errors['email']) return 'Enter a valid email';
    if (c.errors['minlength'])
      return `At least ${c.errors['minlength'].requiredLength} characters`;
    return null;
  }

  regPasswordMismatch(): boolean {
    return (
      this.registerForm.touched &&
      this.registerForm.hasError('passwordMismatch')
    );
  }
}
