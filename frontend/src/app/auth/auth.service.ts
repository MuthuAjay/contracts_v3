import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private isAuthenticated = new BehaviorSubject<boolean>(false);

  constructor(private router: Router) {
    const token = localStorage.getItem('token');
    this.isAuthenticated.next(!!token);
  }

  login(email: string, password: string): void {
    // Simulate API call
    if (email && password) {
      localStorage.setItem('token', 'dummy-token');
      this.isAuthenticated.next(true);
      this.router.navigate(['/dashboard']);
    }
  }

  signup(email: string, password: string): void {
    // Simulate API call
    if (email && password) {
      localStorage.setItem('token', 'dummy-token');
      this.isAuthenticated.next(true);
      this.router.navigate(['/dashboard']);
    }
  }

  logout(): void {
    localStorage.removeItem('token');
    this.isAuthenticated.next(false);
    this.router.navigate(['/login']);
  }

  isAuthenticated$() {
    return this.isAuthenticated.asObservable();
  }
}