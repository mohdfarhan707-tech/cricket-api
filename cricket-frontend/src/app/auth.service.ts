import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface AuthTokensResponse {
  access: string;
  refresh: string;
  user: AuthUser;
}

const ACCESS_KEY = 'criclive_access_token';
const REFRESH_KEY = 'criclive_refresh_token';
const USER_KEY = 'criclive_user_json';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'https://criclive-2dzo.onrender.com/api/';
  private userSubject = new BehaviorSubject<AuthUser | null>(this.readStoredUser());

  readonly user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient) {}

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  currentUser(): AuthUser | null {
    return this.userSubject.value;
  }

  /** Staff or superuser — gets the Angular admin console after login. */
  isAdmin(): boolean {
    const u = this.currentUser();
    return !!(u && (u.is_staff || u.is_superuser));
  }

  authHeaders(): HttpHeaders {
    const t = this.getAccessToken();
    return t ? new HttpHeaders({ Authorization: `Bearer ${t}` }) : new HttpHeaders();
  }

  private readStoredUser(): AuthUser | null {
    try {
      const raw = localStorage.getItem(USER_KEY);
      if (!raw) return null;
      const u = JSON.parse(raw) as AuthUser;
      return {
        ...u,
        is_staff: !!u.is_staff,
        is_superuser: !!u.is_superuser,
      };
    } catch {
      return null;
    }
  }

  private persistSession(data: AuthTokensResponse): void {
    localStorage.setItem(ACCESS_KEY, data.access);
    localStorage.setItem(REFRESH_KEY, data.refresh);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    this.userSubject.next(data.user);
  }

  logout(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.userSubject.next(null);
  }

  register(payload: {
    username: string;
    email: string;
    password: string;
  }): Observable<AuthTokensResponse> {
    return this.http
      .post<AuthTokensResponse>(this.apiUrl + 'auth/register/', payload)
      .pipe(tap((d) => this.persistSession(d)));
  }

  login(identifier: string, password: string): Observable<AuthTokensResponse> {
    return this.http
      .post<AuthTokensResponse>(this.apiUrl + 'auth/login/', {
        identifier: identifier.trim(),
        password,
      })
      .pipe(tap((d) => this.persistSession(d)));
  }
}
