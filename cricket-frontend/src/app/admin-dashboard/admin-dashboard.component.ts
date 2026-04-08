import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../auth.service';

export interface AdminSummary {
  users_total: number;
  series_total: number;
  matches_total: number;
  live_match_rows: number;
  staff_email: string;
  staff_username: string;
}

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.css'],
})
export class AdminDashboardComponent implements OnInit {
  @Output() openPublicSite = new EventEmitter<void>();
  @Output() logout = new EventEmitter<void>();

  private readonly api = 'http://127.0.0.1:8000/api/';

  summary: AdminSummary | null = null;
  loading = true;
  error: string | null = null;
  syncBusy = false;
  syncMessage: string | null = null;

  readonly djangoAdminUrl = 'http://127.0.0.1:8000/admin/';

  constructor(
    private http: HttpClient,
    public auth: AuthService,
  ) {}

  ngOnInit(): void {
    this.loadSummary();
  }

  loadSummary(): void {
    this.loading = true;
    this.error = null;
    this.http
      .get<AdminSummary>(this.api + 'auth/admin/summary/', {
        headers: this.auth.authHeaders(),
      })
      .subscribe({
        next: (d) => {
          this.summary = d;
          this.loading = false;
        },
        error: () => {
          this.error = 'Could not load admin summary. Check that you are logged in as staff.';
          this.loading = false;
        },
      });
  }

  triggerMatchSync(): void {
    this.syncBusy = true;
    this.syncMessage = null;
    this.http.get(this.api + 'matches/?refresh=1').subscribe({
      next: () => {
        this.syncBusy = false;
        this.syncMessage = 'Match data sync triggered.';
        this.loadSummary();
      },
      error: () => {
        this.syncBusy = false;
        this.syncMessage = 'Sync request failed.';
      },
    });
  }

  onLogout(): void {
    this.logout.emit();
  }

  onViewPublicSite(): void {
    this.openPublicSite.emit();
  }
}
