import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Series, LiveMatch } from './series.model';
import { Scorecard } from './scorecard.model';

export interface NewsItem {
  id: number;
  source: string;
  title: string;
  link: string;
  summary: string;
  published_at: string | null;
  image_url: string;
}

@Injectable({
  providedIn: 'root'
})
export class CricketService {
  private apiUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) { }

  getMatches(): Observable<Series[]> {
    return this.http.get<Series[]>(this.apiUrl + 'matches/');
  }

  getScorecard(matchId: string): Observable<Scorecard> {
    return this.http.get<Scorecard>(`${this.apiUrl}matches/${matchId}/scorecard/`);
  }

  getLiveMatches(): Observable<LiveMatch[]> {
    return this.http.get<LiveMatch[]>(this.apiUrl + 'live-matches/');
  }

  getLiveScorecard(matchId: string): Observable<Scorecard> {
    return this.http.get<Scorecard>(`${this.apiUrl}live-matches/${matchId}/scorecard/`);
  }

  getLiveResults(): Observable<LiveMatch[]> {
    return this.http.get<LiveMatch[]>(this.apiUrl + 'live-results/');
  }

  getNews(): Observable<NewsItem[]> {
    return this.http.get<NewsItem[]>(this.apiUrl + 'news/');
  }
}